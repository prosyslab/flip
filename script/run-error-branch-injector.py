#!/usr/bin/env python3

from parse import *
import os
from pathlib import Path
import subprocess
from asyncio.subprocess import DEVNULL
import logging
import multiprocessing

from time import sleep

from benchmark import benchmark
import random


PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flip_output'

RUN_DOCKER_SCRIPT = PROJECT_HOME / 'script/run-docker.py'

logging.basicConfig(
    level=logging.INFO,
    format=
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S")



def inject_error(project, case, env_signal_list):
    def run_cmd_and_check(cmd,
                          *,
                          capture_output=False,
                          text=False,
                          stdout=None,
                          stderr=None):
        process = subprocess.run(cmd,
                                 capture_output=capture_output,
                                 text=text,
                                 stdout=stdout,
                                 stderr=stderr)
        try:
            process.check_returncode()
        except subprocess.CalledProcessError:
            logging.error(f'{project}-{case} failure: {" ".join(cmd)}')
        return process

    print("[*] Injecting error of : %s-%s" % (project, case))

    # run docker
    cmd = [f'{RUN_DOCKER_SCRIPT}', f'{project}-{case}', '-d', '--rm', '--name', f'{project}-{case}-error-branch']
    cmd = cmd + ['--mem', '40g'] if project == 'python' else cmd
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

    docker_id = f'{project}-{case}-error-branch'
    sleep(5)

    run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'touch /experiment/signal_list.txt'])

    run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'touch /experiment/signal_neg_list.txt'])
    
    for (inject_file, inject_line, is_pos) in env_signal_list:
        if is_pos:
            run_cmd_and_check(
                ['docker', 'exec', docker_id, 'bash', '-c', f'echo {inject_file}:{inject_line} >> /experiment/signal_list.txt'])
        else:
            run_cmd_and_check(
                ['docker', 'exec', docker_id, 'bash', '-c', f'echo {inject_file}:{inject_line} >> /experiment/signal_neg_list.txt'])
    
    run_cmd_and_check(
        ['timeout', '10m', 'docker', 'exec', docker_id, '/bugfixer/localizer/main.exe', '-engine', 'error_coverage', '-mmap', '.'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    run_cmd_and_check(
        ['docker', 'exec', '-w', '/experiment', docker_id, 'bash', '-c', f'echo "#!/bin/bash\nexport __ENV_SIGNAL=\$1\ntimeout 5m /bugfixer/localizer/main.exe -engine error_run ." > run.sh'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    run_cmd_and_check(
        ['docker', 'exec', '-w', '/experiment', docker_id, 'bash', '-c', f'chmod 755 run.sh'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    for (inject_file, inject_line, _) in env_signal_list:
        run_cmd_and_check(
            ['timeout', '5m', 'docker', 'exec', '-w', '/experiment', docker_id, 'bash', '-c', f'./run.sh {inject_file}:{inject_line}'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        
        os.makedirs(COVERAGE_DIR / project / case / 'branch' / inject_file / inject_line, exist_ok=True)
        
        run_cmd_and_check(
            ['docker', 'cp', f'{docker_id}:/experiment/localizer-out/result.txt', f"{str(COVERAGE_DIR / project / case / 'branch' / inject_file / inject_line / 'result_ochiai_error.txt')}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        
        run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'rm /experiment/localizer-out/result.txt'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
    
    run_cmd_and_check(['docker', 'kill', f'{docker_id}'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)


def read_signal_list(signal_list_file):
    result = []
    for line in signal_list_file:
        parse_line = parse("{}:{}", line.strip())
        if parse_line != None:
            result.append((os.path.basename(parse_line[0]), parse_line[1]))
    return result
    

def main():
    for project in benchmark:
        for case in benchmark[project]:
            
            if not os.path.exists(COVERAGE_DIR / project / case / 'result_branch.txt'):
                continue
            if not os.path.exists(COVERAGE_DIR / project / case / 'result_branch_neg.txt'):
                continue
            signal_list_file = open(COVERAGE_DIR / project / case / 'result_branch.txt')
            signal_list = read_signal_list(signal_list_file)
            signal_list_file.close()
            signal_list_neg_file = open(COVERAGE_DIR / project / case / 'result_branch_neg.txt')
            signal_list_neg = read_signal_list(signal_list_neg_file)
            signal_list_neg_file.close()

            env_signal_list = []
            for (inject_file, inject_line) in signal_list:
                os.makedirs(COVERAGE_DIR / project / case / 'branch' / inject_file / inject_line, exist_ok=True)
            for (inject_file, inject_line) in signal_list_neg:
                os.makedirs(COVERAGE_DIR / project / case / 'branch' / inject_file / inject_line, exist_ok=True)
                
            for (inject_file, inject_line) in signal_list:
                env_signal_list.append((inject_file, inject_line, True))

            for (inject_file, inject_line) in signal_list_neg:
                env_signal_list.append((inject_file, inject_line, False))

            inject_error(project, case, env_signal_list)


if __name__ == '__main__':
    main()
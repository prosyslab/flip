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



def inject_assume(project, case, inject_file, inject_line, is_pos):
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

    print("[*] Injecting assume of : %s-%s-%s-%s" % (project, case, inject_file, str(inject_line)))

    # run docker
    cmd = [f'{RUN_DOCKER_SCRIPT}', f'{project}-{case}', '-d', '--rm', '--name', f'{project}-{case}-{inject_file}-{inject_line}-assume']
    cmd = cmd + ['--mem', '40g'] if project == 'python' else cmd
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

    docker_id = f'{project}-{case}-{inject_file}-{inject_line}-assume'
    sleep(5)

    run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'touch /experiment/signal_list.txt'])

    run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'touch /experiment/signal_neg_list.txt'])
            
    if is_pos:
        run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'echo {inject_file}:{inject_line} >> /experiment/signal_list.txt'])
    else:
        run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'echo {inject_file}:{inject_line} >> /experiment/signal_neg_list.txt'])

    run_cmd_and_check(
        ['timeout', '60m', 'docker', 'exec', docker_id, '/bugfixer/localizer/main.exe', '-engine', 'assume', '.'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    os.makedirs(COVERAGE_DIR / project / case / 'value' / inject_file / inject_line, exist_ok=True)
    
    run_cmd_and_check(
        ['docker', 'cp', f'{docker_id}:/experiment/localizer-out/result.txt', f"{str(COVERAGE_DIR / project / case / 'value' / inject_file / inject_line / 'result_ochiai_assume.txt')}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    run_cmd_and_check(['docker', 'kill', f'{docker_id}'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)


def read_signal_list(signal_list_file):
    result = []
    for line in signal_list_file:
        parse_line = parse("{}:{}\t{} {} {}", line.strip())
        if parse_line != None:
            result.append((parse_line[0], parse_line[1]))
    return result


def inject_assume_process(run_info):
    params, cpu_count = run_info
    for param in params:
        inject_assume(param + (cpu_count,))


def split_list(lst, length):
    result = [[] for i in range(length)]
    for i in range(len(lst)):
        result[i%length].append(lst[i])
    return result
    

def main():
    for project in benchmark:
        for case in benchmark[project]:
            
            if not os.path.exists(COVERAGE_DIR / project / case / 'value'):
                continue
            if not os.path.exists(COVERAGE_DIR / project / case / 'result_signal_filter.txt'):
                continue
            if not os.path.exists(COVERAGE_DIR / project / case / 'result_signal_neg_filter.txt'):
                continue
            signal_list_file = open(COVERAGE_DIR / project / case / 'result_signal_filter.txt')
            signal_list = read_signal_list(signal_list_file)
            signal_list_file.close()
            signal_list_neg_file = open(COVERAGE_DIR / project / case / 'result_signal_neg_filter.txt')
            signal_list_neg = read_signal_list(signal_list_neg_file)
            signal_list_neg_file.close()

            for (inject_file, inject_line) in signal_list:
                inject_assume(project, case, inject_file, inject_line, True)
            for (inject_file, inject_line) in signal_list_neg:
                inject_assume(project, case, inject_file, inject_line, False)


if __name__ == '__main__':
    main()
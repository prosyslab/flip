#!/usr/bin/env python3

from parse import *
import os
import yaml
from pathlib import Path
import subprocess
from asyncio.subprocess import DEVNULL
import logging
from benchmark import benchmark

PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flip_output'
YML_DIR = PROJECT_HOME / 'benchmark'


RUN_DOCKER_SCRIPT = PROJECT_HOME / 'script/run-docker.py'

logging.basicConfig(
    level=logging.INFO,
    format=
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S")


def get_test_num(project, case):
    with open(os.path.join(YML_DIR, project, f'{project}.bugzoo.yml')) as f:
        bug_data = yaml.load(f, Loader=yaml.FullLoader)
        neg_num = 0
        pos_num = 0
        for data in bug_data['bugs']:
            if data['name'].split(':')[-1] == case:
                neg_num = int(data['test-harness']['failing'])
                pos_num = int(data['test-harness']['passing'])
                break
        else:
            raise Exception("TEST NUM NOT FOUND")
    return neg_num, pos_num



def branch_print(project, case):
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

    print("[*] Extracting branch of : %s-%s" % (project, case))

    # run docker
    cmd = [f'{RUN_DOCKER_SCRIPT}', f'{project}-{case}', '-d', '--rm', '--name', f'{project}-{case}-branch']
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

    docker_id = f'{project}-{case}-branch'

    run_cmd_and_check(
        ['docker', 'exec', docker_id, '/bugfixer/localizer/main.exe', '-engine', 'branch_print', '.'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    neg_num, _ = get_test_num(project, case)

    for i in range(neg_num):
        test_num = i+1
        run_cmd_and_check(
            ['timeout', '1m', 'docker', 'exec', '-w', '/experiment', docker_id, 'bash', '-c', f'./test.sh n{test_num} || true'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        
        run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f"cat /experiment/coverage_data/tmp/*.txt | tr -d '\\000' > /experiment/coverage_data/coverage.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        
        os.makedirs(COVERAGE_DIR / project / case, exist_ok=True)
        
        run_cmd_and_check(
            ['docker', 'cp', f'{docker_id}:/experiment/coverage_data/coverage.txt', f"{str(COVERAGE_DIR / project / case / ('branch_n' +str(test_num)+ '.txt'))}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        
        run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f"rm -f /experiment/coverage_data/tmp/*.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)  

    run_cmd_and_check(['docker', 'kill', f'{docker_id}'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)


def main():
    for project in benchmark:
        for case in benchmark[project]:
            branch_print(project, case)


if __name__ == '__main__':
    main()
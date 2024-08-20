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
COVERAGE_DIR = PROJECT_HOME / 'flex_output'
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



def coverage_extract(project, case):
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

    print("[*] Extracting coverage of : %s-%s" % (project, case))

    # run docker
    cmd = [f'{RUN_DOCKER_SCRIPT}', f'{project}-{case}', '-d', '--rm', '--name', f'{project}-{case}-coverage']
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

    docker_id = f'{project}-{case}-coverage'

    run_cmd_and_check(
        ['docker', 'exec', docker_id, '/bugfixer/localizer/main.exe', '-engine', 'ochiai', '.'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    os.makedirs(COVERAGE_DIR / project / case, exist_ok=True)
    
    run_cmd_and_check(
        ['docker', 'cp', f'{docker_id}:/experiment/localizer-out/result_ochiai.txt', f"{str(COVERAGE_DIR / project / case / 'result_ochiai.txt')}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL) 

    run_cmd_and_check(['docker', 'kill', f'{docker_id}'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)


def main():
    for project in benchmark:
        for case in benchmark[project]:
            coverage_extract(project, case)


if __name__ == '__main__':
    main()
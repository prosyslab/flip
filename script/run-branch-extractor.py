#!/usr/bin/env python3

from parse import *
import os
import yaml
from pathlib import Path
from asyncio.subprocess import DEVNULL
import logging
from benchmark import benchmark

PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flip_output'
YML_DIR = PROJECT_HOME / 'benchmark'


RUN_DOCKER_SCRIPT = PROJECT_HOME / 'bin/run-docker.py'

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


def main():
    for project in benchmark:
        for case in benchmark[project]:
            
            neg_num, _ = get_test_num(project, case)
            for i in range(neg_num):
                test_num = i+1
                if not os.path.exists(COVERAGE_DIR / project / case / f"branch_n{test_num}.txt"):
                    continue
                branch_info = set()
                with open(COVERAGE_DIR / project / case / f"branch_n{test_num}.txt", 'r') as f:
                    lines = f.readlines()
                    for j in range(len(lines)):
                        if j+1 >= len(lines):
                            continue
                        if (':' not in lines[j]) or (lines[j+1].strip() not in ["True", "False"]):
                            continue
                        branch_info.add((lines[j].strip(), eval(lines[j+1].strip())))
                os.makedirs(COVERAGE_DIR / project / case / 'branch', exist_ok=True)
                branch_file = open(COVERAGE_DIR / project / case / 'result_branch.txt', 'w')
                branch_neg_file = open(COVERAGE_DIR / project / case / 'result_branch_neg.txt', 'w')
                for (sig, is_pos) in branch_info:
                    if is_pos:
                        branch_file.write(sig+'\n')
                    else:
                        branch_neg_file.write(sig+'\n')
                branch_file.close()
                branch_neg_file.close()
                


if __name__ == '__main__':
    main()
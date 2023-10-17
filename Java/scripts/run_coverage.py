#!/usr/bin/env python3

import subprocess
from parse import *
from tqdm import tqdm
import os
import logging
import parmap
import random
import sys
from benchmark import benchmark


def get_coverage(run_info):
    project, case = run_info

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
        # try:
        #     process.check_returncode()
        # except subprocess.CalledProcessError:
        #     pass
    # print(f"{project}-{case}-{method} START")
    with open(f"/flip/test/coverage/{project}/{case}/test_method_relevant.txt", 'r') as f:
        for line in (f.readlines()):
            method = line.strip()
            # if os.path.exists(f"/flip/test/coverage/{project}/{case}/coverage/" + method + ".xml"):
            #     continue
            os.chdir(f"/flip/test/{project}/{case}")

            cmd = ['defects4j', 'coverage', '-w',
                   f"/flip/test/{project}/{case}", '-t', method, '-i', f'/flip/test/coverage/{project}/{case}/classes']

            try:
                run_cmd_and_check(cmd,
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)

                # method_name = parse("{}::{}", method)[1]

                os.makedirs(
                    f"/flip/test/coverage/{project}/{case}/coverage", exist_ok=True)

                os.rename(f"/flip/test/{project}/{case}/coverage.xml",
                          f"/flip/test/coverage/{project}/{case}/coverage/{method}.xml")
            except:
                pass
            # print(f"{project}-{case}-{method} END")


def get_coverage_process(params):
    for i, param in enumerate(params):
        # if i > 1000:
        # print(i)
        get_coverage(param)


def split_list(lst, length):
    result = [[] for i in range(length)]
    for i in range(len(lst)):
        result[i % length].append(lst[i])
    return result


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = str(i+1)
        if os.path.exists(f"/flip/test/{project}/{case}"):
            work_list.append((project, case))

    print(len(work_list))
    num_process = 60
    random.shuffle(work_list)
    split_work_list = split_list(work_list, num_process)
    print(len(split_work_list[-1]))
    parmap.map(get_coverage_process, split_work_list,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

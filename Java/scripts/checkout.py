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


def checkout(run_info):
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
    project, case = run_info

    os.makedirs(f"/flip/test/{project}", exist_ok=True)

    cmd = f"rm -rf /flip/test/{project}/{case}".split(' ')
    run_cmd_and_check(cmd)

    cmd = ['defects4j', 'checkout', '-p', project, '-v',
           f"{case}b", '-w', f'/flip/test/{project}/{case}']
    run_cmd_and_check(cmd)

    if os.path.exists(f"/flip/test/{project}/{case}"):

        os.chdir(f"/flip/test/{project}/{case}")

        cmd = ['defects4j', 'export', '-p',
               'tests.relevant', '-o', 'test_relevant']
        run_cmd_and_check(cmd)

        cmd = "defects4j export -p tests.trigger -o neg_test".split(' ')
        run_cmd_and_check(cmd)

        # cmd = "defects4j export -p tests.trigger -o neg_test".split(' ')
        # run_cmd_and_check(cmd)

        cmd = "defects4j export -p classes.relevant -o classes".split(' ')
        run_cmd_and_check(cmd)


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = str(i+1)
        work_list.append((project, case))
        # checkout(project, case)
    num_process = 60
    random.shuffle(work_list)
    parmap.map(checkout, work_list,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

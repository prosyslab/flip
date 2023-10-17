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


def get_method(project, case, class_name, target):
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

    def zero_or_more_string(text):
        return text
    zero_or_more_string.pattern = r".*"

    class_path = f"/flip/test/{project}/{case}/{target}/" + \
        class_name.replace('.', '/') + '.class'

    # if not os.path.exists(class_path):
    #     class_path = f"/flip/test/{project}/{case}/build-tests/" + \
    #         class_name.replace('.', '/') + '.class'

    cmd = ['javap', class_path]
    p = run_cmd_and_check(cmd, capture_output=True)

    output = p.stdout.decode('utf-8')
    method_list = output.splitlines()

    with open(f"/flip/test/{project}/{case}/test_method_relevant.txt", 'a') as f:
        for method in method_list:
            parse_line = parse("  public void {}(){:z}", method, {
                               "z": zero_or_more_string})
            if parse_line:
                method_name = parse_line[0]
                f.write(f"{class_name}::{method_name}\n")


def get_method_case(run_info):
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
        try:
            process.check_returncode()
        except subprocess.CalledProcessError:
            logging.error(f'{project}-{case} failure: {" ".join(cmd)}')
        return process

    os.makedirs(f"/flip/test/coverage/{project}/{case}", exist_ok=True)

    if os.path.exists(f"/flip/test/{project}/{case}"):
        os.chdir(f"/flip/test/{project}/{case}")
        cmd = f"defects4j compile -w /flip/test/{project}/{case}".split(
            " ")
        run_cmd_and_check(cmd)
        cmd = f"defects4j export -p dir.bin.tests -w /flip/test/{project}/{case}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        target = p.stdout.decode('utf-8')
        with open(f"/flip/test/{project}/{case}/test_relevant", 'r') as f:
            for line in tqdm(f.readlines()):
                class_name = line.strip()
                get_method(project, case, class_name, target)
        os.rename(f"/flip/test/{project}/{case}/test_relevant",
                  f"/flip/test/coverage/{project}/{case}/test_relevant")
        os.rename(f"/flip/test/{project}/{case}/neg_test",
                  f"/flip/test/coverage/{project}/{case}/neg_test")
        # os.rename(f"/flip/test/{project}/{case}/test_method.txt",
        #           f"/flip/test/coverage/{project}/{case}/test_method.txt")
        os.rename(f"/flip/test/{project}/{case}/test_method_relevant.txt",
                  f"/flip/test/coverage/{project}/{case}/test_method_relevant.txt")
        os.rename(f"/flip/test/{project}/{case}/classes",
                  f"/flip/test/coverage/{project}/{case}/classes")


def main():
    project = sys.argv[1]
    case = ""
    work_list = []

    for i in benchmark[project]:
        case = str(i+1)
        work_list.append((project, case))

    num_process = 60
    random.shuffle(work_list)
    parmap.map(get_method_case, work_list,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import subprocess
from parse import *
import os
import logging
import parmap
import random
import sys
from benchmark import benchmark


def run_error_print(run_info):
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
    # branch_info = set()
    # for filename in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
    #     if filename.startswith("branch"):
    #         with open(f"/flip/test/coverage/{project}/{case}/fail/{filename}", "r") as f:
    #             lines = f.readlines()
    #             for i in range(len(lines)):
    #                 line = lines[i].strip()
    #                 if i+1 >= len(lines):
    #                     break
    #                 cond = lines[i+1].strip()
    #                 if i % 2 == 0:
    #                     parse_line = parse("({}:{})", line)
    #                     filename, lineno = os.path.basename(
    #                         parse_line[0]), parse_line[1]
    #                     branch_info.add((filename, lineno, cond))
    #                 else:
    #                     continue

    os.makedirs(f"/flip/test/{project}", exist_ok=True)

    # for filename, lineno, cond in branch_info:
    os.chdir(f"/flip/test")
    cmd = f"rm -rf /flip/test/{project}/{case}".split(' ')
    run_cmd_and_check(cmd)

    cmd = f"rm -rf /flip/tmp/{project}/{case}".split(' ')
    run_cmd_and_check(cmd)
    os.makedirs(f"/flip/tmp/{project}/{case}", exist_ok=True)

    cmd = f"defects4j checkout -p {project} -v {case}b -w /flip/test/{project}/{case}".split(
        ' ')
    run_cmd_and_check(cmd)

    if os.path.exists(f"/flip/test/{project}/{case}"):

        cmd = f"defects4j compile -w /flip/test/{project}/{case}".split(
            ' ')
        run_cmd_and_check(cmd)

        # cmd = f"defects4j export -p dir.src.classes -w /flip/test/{project}/{case}".split(
        #     " ")
        # p = run_cmd_and_check(cmd, capture_output=True)
        # src = p.stdout.decode('utf-8')

        # cmd = f"defects4j export -p dir.bin.classes -w /flip/test/{project}/{case}".split(
        #     " ")
        # p = run_cmd_and_check(cmd, capture_output=True)
        # target = p.stdout.decode('utf-8')

        # cmd = ["mvn", "exec:java",
        #        f"-Dexec.args=fail /flip/test/{project}/{case}/{src} /flip/test/{project}/{case}/{target} /flip/tmp/{project}/{case} {filename} {lineno} {cond}"]
        # run_cmd_and_check(cmd)

        # os.chdir(f"/flip/test/{project}/{case}")

        # cmd = f"../../patch.sh".split(' ')
        # run_cmd_and_check(cmd)

        # os.chdir(f"/flip/test")

        # cmd = f"rm -rf /flip/tmp/{project}/{case}".split(' ')
        # run_cmd_and_check(cmd)
        # os.makedirs(f"/flip/tmp/{project}/{case}", exist_ok=True)

        # cmd = ["mvn", "exec:java",
        #        f"-Dexec.args=callsequence /flip/test/{project}/{case}/{src} /flip/test/{project}/{case}/{target} /flip/tmp/{project}/{case}"]
        # run_cmd_and_check(cmd)

        os.chdir(f"/flip/test/{project}/{case}")

        # cmd = "defects4j export -p classes.relevant -o classes".split(' ')
        # run_cmd_and_check(cmd)

        # cmd = "defects4j export -p tests.trigger -o neg_test".split(' ')
        # run_cmd_and_check(cmd)

        # cmd = f"/flip/test/patch/{project}/patch.sh".split(' ')
        # run_cmd_and_check(cmd)

        # cmd = f"defects4j compile -w /flip/test/{project}/{case}".split(
        #     ' ')
        # run_cmd_and_check(cmd)

        with open(f"/flip/test/coverage/{project}/{case}/neg_test", "r") as f:
            for i, line in enumerate(f.readlines()):
                method = line.strip()

                cmd = ['timeout', '60', 'defects4j', 'test', '-w',
                       f"/flip/test/{project}/{case}", '-t', method]
                run_cmd_and_check(cmd)
                if os.path.exists(f"/flip/test/{project}/{case}/failing_tests"):
                    os.makedirs(
                        f"/flip/test/coverage/{project}/{case}/fail", exist_ok=True)
                    os.rename(f"/flip/test/{project}/{case}/failing_tests",
                              f"/flip/test/coverage/{project}/{case}/fail/failing_tests-{i}")

    os.chdir("/flip/test")


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = i + 1
        # run_call_print(("Math", case))
        work_list.append((project, case))
    num_process = 40
    random.shuffle(work_list)
    # split_work_list = split_list(work_list, num_process)
    parmap.map(run_error_print, work_list,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import subprocess
from parse import *
import os
import logging
import parmap
import random
import sys
from benchmark import benchmark


def run_flip_pass(run_info):
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
    project, case, coverage, filename, lineno, cond, pass_method_list = run_info

    # os.makedirs(f"/flip/test/{project}", exist_ok=True)

    src = ""
    target = ""

    if (filename, lineno) not in coverage:
        return
    nef, nep = coverage[(filename, lineno)]
    if int(nef) < 1 or int(nep) < 1:
        return
    if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/pass") and os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/fail") and len(os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/pass")) + len(os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/fail")) == len(pass_method_list):
        return

    os.chdir("/flip/test")
    cmd = f"rm -rf /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
        ' ')
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
    os.makedirs(
        f"/flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}", exist_ok=True)

    cmd = f"rm -rf /flip/tmp/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
        ' ')
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
    os.makedirs(
        f"/flip/tmp/fail/{project}/{case}/{filename}/{lineno}/{cond}", exist_ok=True)

    cmd = f"defects4j checkout -p {project} -v {case}b -w /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
        ' ')
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

    if os.path.exists(f"/flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}"):

        os.chdir(
            f"/flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}")

        # cmd = f"defects4j export -p tests.trigger -o /flip/test/{project}/{case}/neg_test".split(
        #     ' ')
        # run_cmd_and_check(cmd)

        cmd = f"defects4j compile -w /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
            ' ')
        run_cmd_and_check(cmd,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

        if len(src) == 0:
            cmd = f"defects4j export -p dir.src.classes -w /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
                " ")
            p = run_cmd_and_check(cmd, capture_output=True)
            src = p.stdout.decode('utf-8')

        if len(target) == 0:
            cmd = f"defects4j export -p dir.bin.classes -w /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
                " ")
            p = run_cmd_and_check(cmd, capture_output=True)
            target = p.stdout.decode('utf-8')

        os.chdir("/flip/test")

        cmd = ["mvn", "exec:java",
               f"-Dexec.args=fail /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/{src} /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/{target} /flip/tmp/fail/{project}/{case}/{filename}/{lineno}/{cond} {filename} {lineno} {cond}"]
        run_cmd_and_check(cmd,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

        os.chdir(
            f"/flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}")

        # cmd = f"defects4j export -p classes.relevant -o /flip/test/coverage/{project}/{case}/classes".split(
        #     ' ')
        # run_cmd_and_check(cmd)

        cmd = f"/flip/test/patch/{project}/patch.sh".split(' ')
        run_cmd_and_check(cmd,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

        cmd = f"defects4j compile -w /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
            ' ')
        run_cmd_and_check(cmd,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

        # with open(f"/flip/test/coverage/{project}/{case}/test_method_relevant.txt", "r") as f:
        for i, method in pass_method_list:
            # method = line.strip()
            # with open(f"/flip/test/coverage/{project}/{case}/neg_test", 'r') as neg:
            #     if method in list(map(lambda x: x.strip(), neg.readlines())):
            #         continue

            if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/pass/coverage-{i}.xml") or os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/fail/coverage-{i}.xml"):
                continue

            cmd = ['timeout', '60', 'defects4j', 'coverage', '-w',
                   f"/flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}", '-t', method, '-i', f'/flip/test/coverage/{project}/{case}/classes']
            run_cmd_and_check(cmd,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
            if os.path.exists(f"/flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/coverage.xml"):
                result = "pass" if os.path.getsize(
                    f"/flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/failing_tests") > 0 else "fail"
                os.makedirs(
                    f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/{result}", exist_ok=True)
                os.rename(f"/flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/coverage.xml",
                          f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/{result}/coverage-{i}.xml")
    cmd = f"rm -rf /flip/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
        ' ')
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

    return


def split_list(lst, length):
    result = [[] for i in range(length)]
    for i in range(len(lst)):
        result[i % length].append(lst[i])
    return result


def read_coverage(cov_path):
    result = dict()
    with open(cov_path) as f:
        for line in f.readlines():
            class_name, line_num, nef, nep, score = parse(
                "{}:{}\t{} {} {}", line.strip())
            filename = f"{class_name.split('.')[-1]}.java"
            result[(filename, line_num)] = (nef, nep)
    return result


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = i + 1
        if not os.path.exists(f"/flip/test/coverage/{project}/{case}/result_ochiai.txt"):
            continue
        if not os.path.exists(f"/flip/test/coverage/{project}/{case}/fail"):
            continue
        coverage = read_coverage(
            f"/flip/test/coverage/{project}/{case}/result_ochiai.txt")
        branch_info = set()

        pass_method_list = []

        with open(f"/flip/test/coverage/{project}/{case}/test_method_relevant.txt", "r") as f, open(f"/flip/test/coverage/{project}/{case}/neg_test", 'r') as neg:
            for i, line in enumerate(f.readlines()):
                method = line.strip()
                if method in list(map(lambda x: x.strip(), neg.readlines())):
                    continue
                pass_method_list.append((i, method))
        for filename in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
            if filename.startswith("branch"):
                with open(f"/flip/test/coverage/{project}/{case}/fail/{filename}", "r") as f:
                    lines = f.readlines()
                    for i in range(min(len(lines), 10000)):
                        line = lines[i].strip()
                        if i+1 >= len(lines):
                            break
                        cond = lines[i+1].strip()
                        if cond not in ["true", "false"]:
                            continue
                        parse_line = parse("({}:{})", line)
                        if parse_line != None:
                            filename, lineno = os.path.basename(
                                parse_line[0]), parse_line[1]
                            branch_info.add((filename, lineno, cond))
                        else:
                            continue
        for filename, lineno, cond in branch_info:
            work_list.append((project, case, coverage, filename,
                             lineno, cond, pass_method_list))
    num_process = 60
    random.shuffle(work_list)
    parmap.map(run_flip_pass, work_list,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

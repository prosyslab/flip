#!/usr/bin/env python3

import subprocess
from parse import *
import os
import logging
import parmap
import random
import sys
from benchmark import benchmark


def run_flip_fail(run_info):
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
    project, case, filename, lineno, cond = run_info

    os.makedirs(f"/spoon_test/test/{project}", exist_ok=True)

    # with open(f"/spoon_test/test/coverage/{project}/{case}/neg_test", 'r') as f:
    #     neg_num = len(f.readlines())
    #     if os.path.exists(f"/spoon_test/test/coverage/{project}/{case}/fail") and os.path.exists(f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}/{lineno}") and len(list(filter(lambda x: "coverage" in x, os.listdir(f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}/{lineno}")))) == neg_num:
    #         return

    os.chdir("/spoon_test/test")
    cmd = f"rm -rf /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
        ' ')
    run_cmd_and_check(cmd)

    cmd = f"rm -rf /spoon_test/tmp/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
        ' ')
    run_cmd_and_check(cmd)
    os.makedirs(
        f"/spoon_test/tmp/fail/{project}/{case}/{filename}/{lineno}/{cond}", exist_ok=True)

    cmd = f"defects4j checkout -p {project} -v {case}b -w /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
        ' ')
    run_cmd_and_check(cmd)

    if os.path.exists(f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}"):

        os.chdir(
            f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}")

        # cmd = f"defects4j export -p tests.trigger -o /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/neg_test".split(
        #     ' ')
        # run_cmd_and_check(cmd)

        cmd = f"defects4j compile -w /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
            ' ')
        run_cmd_and_check(cmd)

        cmd = f"defects4j export -p dir.src.classes -w /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        src = p.stdout.decode('utf-8')

        cmd = f"defects4j export -p dir.bin.classes -w /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        target = p.stdout.decode('utf-8')

        os.chdir("/spoon_test/test")

        cond_flip = "false" if cond == "true" else "true"

        cmd = ["mvn", "exec:java",
               f"-Dexec.args=fail /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/{src} /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/{target} /spoon_test/tmp/fail/{project}/{case}/{filename}/{lineno}/{cond} {filename} {lineno} {cond_flip}"]
        run_cmd_and_check(cmd)

        os.chdir(
            f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}")

        # cmd = f"defects4j export -p classes.relevant -o /spoon_test/test/coverage/{project}/{case}/classes".split(
        #     ' ')
        # run_cmd_and_check(cmd)

        src_path = f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/{src}"
        for base, folders, files in os.walk(src_path):
            for file in files:
                if file.endswith(".java"):
                    # if relative_error_file != "src/com/google/javascript/jscomp/AnalyzePrototypeProperties.java":
                    #     continue
                    instrumented_file_path = os.path.join(base, file)
                    relative_path = os.path.relpath(instrumented_file_path, f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}")
                    origin_file_path = os.path.join(f"/spoon_test/test/{project}/{case}", relative_path)

                    code = []
                    with open(origin_file_path, 'r') as origin_file, open(instrumented_file_path, 'r') as instrumented_file:
                        import_a = []
                        for line in origin_file:
                            if line.strip().startswith("import "):
                                import_a.append(line.strip())

                        code_b_before = []
                        import_b = []
                        code_b_after = []
                        package_passed = False
                        for line in instrumented_file:
                            if line.strip().startswith("import "):
                                import_b.append(line.strip())
                            else:
                                if package_passed:
                                    code_b_after.append(line)
                                else:
                                    code_b_before.append(line)
                                if line.startswith("package"):
                                    package_passed = True

                        new_imports = list(import_a)
                        for import_line in import_b:
                            class_name = import_line.split('.')[-1]
                            for import_line_orig in import_a:
                                if class_name in import_line_orig:
                                    break
                            else:
                                new_imports.append(import_line)
                        # new_imports = list(set(import_a).union(set(import_b)))
                        new_imports = list(filter(lambda x: x.split(' ')[1][0].islower(), new_imports))
                        new_imports = list(map(lambda x: f"{x}\n", new_imports))

                        # print(code_b_before)
                        code = code_b_before + new_imports + code_b_after

                        

                    with open(instrumented_file_path, 'w') as instrumented_file:
                        for line in code:
                            instrumented_file.write(line)

        cmd = f"/spoon_test/test/patch/{project}/{case}/patch.sh".split(' ')
        run_cmd_and_check(cmd)

        cmd = f"defects4j compile -w /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
            ' ')
        p = run_cmd_and_check(cmd)
        if p.returncode != 0:
            return

        with open(f"/spoon_test/test/coverage/{project}/{case}/neg_test", "r") as f:
            for i, line in enumerate(f.readlines()):
                method = line.strip()

                if os.path.exists(f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}/{lineno}/coverage-{i}.xml") and os.path.exists(f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}/{lineno}/failing_tests-{i}.xml"):
                    continue

                # cmd = ['timeout', '60', 'defects4j', 'test', '-w',
                #        f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}", '-t', method]
                cmd = ['timeout', '600', 'defects4j', 'coverage', '-w',
                       f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}", '-t', method, '-i', f'/spoon_test/test/coverage/{project}/{case}/classes']
                run_cmd_and_check(cmd)
                if os.path.exists(f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/coverage.xml"):
                    os.makedirs(
                        f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}/{lineno}", exist_ok=True)
                    os.rename(f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/coverage.xml",
                              f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}/{lineno}/coverage-{i}.xml")
                if os.path.exists(f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/failing_tests"):
                    os.makedirs(
                        f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}/{lineno}", exist_ok=True)
                    os.rename(f"/spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}/failing_tests",
                              f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}/{lineno}/failing_tests-{i}")

    cmd = f"rm -rf /spoon_test/test/fail/{project}/{case}/{filename}/{lineno}/{cond}".split(
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


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = i + 1
        branch_info = set()
        if not os.path.exists(f"/spoon_test/test/coverage/{project}/{case}/fail"):
            continue
        for filename in os.listdir(f"/spoon_test/test/coverage/{project}/{case}/fail"):
            if filename.startswith("branch"):
                with open(f"/spoon_test/test/coverage/{project}/{case}/fail/{filename}", "r") as f:
                    lines = f.readlines()
                    for i in range(len(lines)):
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
            work_list.append((project, case, filename, lineno, cond))
    print(len(work_list))
    num_process = 20
    random.shuffle(work_list)
    parmap.map(run_flip_fail, work_list,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

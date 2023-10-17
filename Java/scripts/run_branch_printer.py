#!/usr/bin/env python3

import subprocess
from parse import *
import os
import logging
import random
import parmap
import sys
from benchmark import benchmark


def run_branch_printer(run_info):
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

    os.chdir("/flip/test")
    cmd = f"rm -rf /flip/test/branch/{project}/{case}".split(' ')
    run_cmd_and_check(cmd)

    cmd = f"rm -rf /flip/tmp/branch/{project}/{case}".split(' ')
    run_cmd_and_check(cmd)
    os.makedirs(f"/flip/tmp/branch/{project}/{case}", exist_ok=True)

    cmd = f"defects4j checkout -p {project} -v {case}b -w /flip/test/branch/{project}/{case}".split(
        ' ')
    run_cmd_and_check(cmd)

    if os.path.exists(f"/flip/test/branch/{project}/{case}"):
        
        os.chdir(f"/flip/test/branch/{project}/{case}")

        # cmd = "defects4j export -p tests.trigger -o neg_test".split(' ')
        # run_cmd_and_check(cmd)

        # with open(f"/flip/test/coverage/{project}/{case}/neg_test", 'r') as f:
        #     neg_num = len(f.readlines())
        #     if os.path.exists(f"/flip/test/coverage/{project}/{case}/fail") and len(list(filter(lambda x: "branch" in x, os.listdir(f"/flip/test/coverage/{project}/{case}/fail")))) == neg_num:
        #         return

        cmd = f"defects4j compile -w /flip/test/branch/{project}/{case}".split(
            ' ')
        run_cmd_and_check(cmd)

        cmd = f"defects4j export -p dir.src.classes -w /flip/test/branch/{project}/{case}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        src = p.stdout.decode('utf-8')

        cmd = f"defects4j export -p dir.bin.classes -w /flip/test/branch/{project}/{case}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        target = p.stdout.decode('utf-8')

        os.chdir("/flip/test")

        cmd = ["mvn", "exec:java",
               f"-Dexec.args=branch /flip/test/branch/{project}/{case}/{src} /flip/test/branch/{project}/{case}/{target} /flip/tmp/branch/{project}/{case}"]
        run_cmd_and_check(cmd)

        os.chdir(f"/flip/test/branch/{project}/{case}")

        # cmd = "defects4j export -p classes.relevant -o classes".split(' ')
        # run_cmd_and_check(cmd)
        src_path = f"/flip/test/branch/{project}/{case}/{src}"
        for base, folders, files in os.walk(src_path):
            for file in files:
                if file.endswith(".java"):
                    # if relative_error_file != "src/com/google/javascript/jscomp/AnalyzePrototypeProperties.java":
                    #     continue
                    instrumented_file_path = os.path.join(base, file)
                    relative_path = os.path.relpath(instrumented_file_path, f"/flip/test/branch/{project}/{case}")
                    origin_file_path = os.path.join(f"/flip/test/{project}/{case}", relative_path)

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

        cmd = f"/flip/test/patch/{project}/{case}/patch.sh".split(' ')
        run_cmd_and_check(cmd)

        cmd = f"defects4j compile -w /flip/test/branch/{project}/{case}".split(
            ' ')
        run_cmd_and_check(cmd)

        with open(f"/flip/test/coverage/{project}/{case}/neg_test", "r") as f:
            for i, line in enumerate(f.readlines()):

                # if os.path.exists(f"/flip/test/coverage/{project}/{case}/fail/branch-{i}.txt"):
                #     continue
                method = line.strip()

                cmd = ['timeout', '60', 'defects4j', 'test', '-w',
                       f"/flip/test/branch/{project}/{case}", '-t', method]
                run_cmd_and_check(cmd)

                if os.path.exists(f"/flip/test/branch/{project}/{case}/branch.txt"):
                    # open(f"/flip/test/branch/{project}/{case}/branch.txt", 'a').close()
                    os.makedirs(
                        f"/flip/test/coverage/{project}/{case}/fail", exist_ok=True)
                    os.rename(f"/flip/test/branch/{project}/{case}/branch.txt",
                              f"/flip/test/coverage/{project}/{case}/fail/branch-{i}.txt")
    
    cmd = f"rm -rf /flip/test/branch/{project}/{case}".split(
        ' ')

    os.chdir("/flip/test")


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = i + 1
        work_list.append((project, case))

    num_process = 60
    random.shuffle(work_list)
    parmap.map(run_branch_printer, work_list,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

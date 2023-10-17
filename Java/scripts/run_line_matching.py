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


def line_matching_delete(run_info):
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
    project, case, filename, lineno = run_info

    # os.chdir(f"/flip/test/{project}/{case}")
    if os.path.exists(f"/flip/test/coverage/{project}/{case}/delete/{filename}/{lineno}/vimdiff_line_matching.json"):
        return
    # os.path.exists(f"/flip/test/coverage/{project}/{case}/delete/{filename}/{lineno}/result_ochiai6.txt"):
    if True:

        os.makedirs(
            f'/flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}', exist_ok=True)
        os.makedirs(
            f'/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}', exist_ok=True)

        cmd = f"rm -rf /flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}".split(
            " ")
        run_cmd_and_check(cmd)

        cmd = f"rm -rf /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        run_cmd_and_check(cmd)

        cmd = f"rm -rf /flip/tmp/line/{project}/{case}/{filename}/{lineno}".split(
            ' ')
        run_cmd_and_check(cmd)
        os.makedirs(
            f"/flip/tmp/line/{project}/{case}/{filename}/{lineno}", exist_ok=True)

        cmd = ['defects4j', 'checkout', '-p', project, '-v',
               f"{case}b", '-w', f'/flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}']
        run_cmd_and_check(cmd)
        cmd = ['defects4j', 'checkout', '-p', project, '-v',
               f"{case}b", '-w', f'/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}']
        run_cmd_and_check(cmd)
        os.chdir(
            f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")
        cmd = f"defects4j compile -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            ' ')
        run_cmd_and_check(cmd)

        cmd = f"defects4j export -p dir.src.classes -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        src = p.stdout.decode('utf-8')

        cmd = f"defects4j export -p dir.bin.classes -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        target = p.stdout.decode('utf-8')

        os.chdir("/flip/test")

        cmd = ["mvn", "exec:java",
               f"-Dexec.args=delete /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{src} /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{target} /flip/tmp/line/{project}/{case}/{filename}/{lineno} {filename} {lineno} true"]
        run_cmd_and_check(cmd)

        os.chdir(
            f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")

        cmd = f"/flip/test/patch/{project}/patch.sh".split(
            ' ')
        run_cmd_and_check(cmd)

        os.chdir(
            f"/flip/test/coverage/{project}/{case}/delete/{filename}/{lineno}")

        cmd = f"/flip/test/vimdiff_line_matching.py /flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}/{src} /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{src} vimdiff.html".split(
            " ")
        run_cmd_and_check(cmd)


def line_matching_remove(run_info):
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
    project, case, filename, lineno = run_info

    # os.chdir(f"/flip/test/{project}/{case}")
    if os.path.exists(f"/flip/test/coverage/{project}/{case}/remove/{filename}/{lineno}/vimdiff_line_matching.json"):
        return
    # os.path.exists(f"/flip/test/coverage/{project}/{case}/remove/{filename}/{lineno}/result_ochiai6.txt"):
    if True:

        os.makedirs(
            f'/flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}', exist_ok=True)
        os.makedirs(
            f'/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}', exist_ok=True)

        cmd = f"rm -rf /flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}".split(
            " ")
        run_cmd_and_check(cmd)

        cmd = f"rm -rf /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        run_cmd_and_check(cmd)

        cmd = f"rm -rf /flip/tmp/line/{project}/{case}/{filename}/{lineno}".split(
            ' ')
        run_cmd_and_check(cmd)
        os.makedirs(
            f"/flip/tmp/line/{project}/{case}/{filename}/{lineno}", exist_ok=True)

        cmd = ['defects4j', 'checkout', '-p', project, '-v',
               f"{case}b", '-w', f'/flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}']
        run_cmd_and_check(cmd)
        cmd = ['defects4j', 'checkout', '-p', project, '-v',
               f"{case}b", '-w', f'/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}']
        run_cmd_and_check(cmd)
        os.chdir(
            f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")
        cmd = f"defects4j compile -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            ' ')
        run_cmd_and_check(cmd)

        cmd = f"defects4j export -p dir.src.classes -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        src = p.stdout.decode('utf-8')

        cmd = f"defects4j export -p dir.bin.classes -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        target = p.stdout.decode('utf-8')

        os.chdir("/flip/test")

        cmd = ["mvn", "exec:java",
               f"-Dexec.args=remove /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{src} /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{target} /flip/tmp/line/{project}/{case}/{filename}/{lineno} {filename} {lineno} true"]
        run_cmd_and_check(cmd)

        os.chdir(
            f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")

        cmd = f"/flip/test/patch/{project}/patch.sh".split(
            ' ')
        run_cmd_and_check(cmd)

        os.chdir(
            f"/flip/test/coverage/{project}/{case}/remove/{filename}/{lineno}")

        cmd = f"/flip/test/vimdiff_line_matching.py /flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}/{src} /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{src} vimdiff.html".split(
            " ")
        run_cmd_and_check(cmd)


def line_matching_fail(run_info):
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
    project, case, filename, lineno = run_info

    # os.chdir(f"/flip/test/{project}/{case}")
    if os.path.exists(f"/flip/test/coverage/{project}/{case}/fail/{filename}/{lineno}/vimdiff_line_matching.json"):
        return
    # os.path.exists(f"/flip/test/coverage/{project}/{case}/fail/{filename}/{lineno}/result_ochiai6.txt"):
    if True:

        os.makedirs(
            f'/flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}', exist_ok=True)
        os.makedirs(
            f'/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}', exist_ok=True)

        cmd = f"rm -rf /flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}".split(
            " ")
        run_cmd_and_check(cmd)

        cmd = f"rm -rf /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        run_cmd_and_check(cmd)

        cmd = f"rm -rf /flip/tmp/line/{project}/{case}/{filename}/{lineno}".split(
            ' ')
        run_cmd_and_check(cmd)
        os.makedirs(
            f"/flip/tmp/line/{project}/{case}/{filename}/{lineno}", exist_ok=True)

        cmd = ['defects4j', 'checkout', '-p', project, '-v',
               f"{case}b", '-w', f'/flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}']
        run_cmd_and_check(cmd)
        cmd = ['defects4j', 'checkout', '-p', project, '-v',
               f"{case}b", '-w', f'/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}']
        run_cmd_and_check(cmd)
        os.chdir(
            f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")
        cmd = f"defects4j compile -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            ' ')
        run_cmd_and_check(cmd)

        cmd = f"defects4j export -p dir.src.classes -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        src = p.stdout.decode('utf-8')

        cmd = f"defects4j export -p dir.bin.classes -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        target = p.stdout.decode('utf-8')

        os.chdir("/flip/test")

        cmd = ["mvn", "exec:java",
               f"-Dexec.args=fail /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{src} /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{target} /flip/tmp/line/{project}/{case}/{filename}/{lineno} {filename} {lineno} true"]
        run_cmd_and_check(cmd)

        os.chdir(
            f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")
        
        src_path = f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{src}"
        for base, folders, files in os.walk(src_path):
            for file in files:
                if file.endswith(".java"):
                    # if relative_error_file != "src/com/google/javascript/jscomp/AnalyzePrototypeProperties.java":
                    #     continue
                    instrumented_file_path = os.path.join(base, file)
                    relative_path = os.path.relpath(instrumented_file_path, f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")
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

        cmd = f"/flip/test/patch/{project}/{case}/patch.sh".split(
            ' ')
        run_cmd_and_check(cmd)

        os.chdir(
            f"/flip/test/coverage/{project}/{case}/fail/{filename}/{lineno}")

        cmd = f"/flip/test/vimdiff_line_matching.py /flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}/{src} /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{src} vimdiff.html {filename}".split(
            " ")
        run_cmd_and_check(cmd)


def line_matching_pass(run_info):
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
    project, case, filename, lineno = run_info
    if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/vimdiff_line_matching.json"):
        return
    if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}/result_ochiai3.txt"):
        os.makedirs(
            f'/flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}', exist_ok=True)
        os.makedirs(
            f'/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}', exist_ok=True)

        cmd = f"rm -rf /flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}".split(
            " ")
        run_cmd_and_check(cmd)

        cmd = f"rm -rf /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        run_cmd_and_check(cmd)

        cmd = f"rm -rf /flip/tmp/line/{project}/{case}/{filename}/{lineno}".split(
            ' ')
        run_cmd_and_check(cmd)
        os.makedirs(
            f"/flip/tmp/line/{project}/{case}/{filename}/{lineno}", exist_ok=True)

        cmd = ['defects4j', 'checkout', '-p', project, '-v',
               f"{case}b", '-w', f'/flip/tmp/line_matching/{project}/{case}/{filename}/{lineno}']
        run_cmd_and_check(cmd)
        cmd = ['defects4j', 'checkout', '-p', project, '-v',
               f"{case}b", '-w', f'/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}']
        run_cmd_and_check(cmd)
        os.chdir(
            f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")
        cmd = f"defects4j compile -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            ' ')
        run_cmd_and_check(cmd)

        cmd = f"defects4j export -p dir.src.classes -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        src = p.stdout.decode('utf-8')

        cmd = f"defects4j export -p dir.bin.classes -w /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}".split(
            " ")
        p = run_cmd_and_check(cmd, capture_output=True)
        target = p.stdout.decode('utf-8')

        os.chdir("/flip/test")

        cmd = ["mvn", "exec:java",
               f"-Dexec.args=fail /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{src} /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}/{target} /flip/tmp/line/{project}/{case}/{filename}/{lineno} {filename} {lineno} true"]
        run_cmd_and_check(cmd)

        os.chdir(
            f"/flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno}")

        cmd = f"/flip/test/patch/{project}/patch.sh".split(
            ' ')
        run_cmd_and_check(cmd)

        os.chdir(
            f"/flip/test/coverage/{project}/{case}/pass/{filename}/{lineno}")

        cmd = f"/flip/test/vimdiff_line_matching.py /flip/tmp/line_matching/{project}/{case}/{filename}/{lineno} /flip/tmp/line_matching/{project}/{case}_inst/{filename}/{lineno} vimdiff.html".split(
            " ")
        run_cmd_and_check(cmd)


def main():
    project = sys.argv[1]
    work_list_delete = []
    work_list_remove = []
    work_list_fail = []
    work_list_pass = []
    for i in benchmark[project]:
        case = str(i+1)
        if os.path.exists(f"/flip/test/coverage/{project}/{case}/fail"):
            for filename in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
                if not filename.endswith(".java"):
                    continue
                for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/fail/{filename}"):
                    work_list_fail.append((project, case, filename, lineno))
        if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass"):
            for filename in os.listdir(f"/flip/test/coverage/{project}/{case}/pass"):
                if not filename.endswith(".java"):
                    continue
                for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{filename}"):
                    work_list_pass.append((project, case, filename, lineno))
    num_process = 40
    random.shuffle(work_list_fail)
    parmap.map(line_matching_fail, work_list_fail,
               pm_pbar=True, pm_processes=num_process)
    random.shuffle(work_list_pass)
    parmap.map(line_matching_pass, work_list_pass,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

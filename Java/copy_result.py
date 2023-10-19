#!/usr/bin/env python3

import subprocess
import os
import logging


def main():
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
            logging.error(f'cmd failure: {" ".join(cmd)}')
        return process
    container1 = sys.argv[1]
    container2 = sys.argv[2]
    project = sys.argv[3]

    for i in benchmark[project]:
        case = str(i+1)
        os.makedirs(f"./___tmp_flip_result___/{project}/{case}", exist_ok=True)
        cmd = f"docker cp {container1}:/flip/test/coverage/{project}/{case}/result_ochiai_final.txt ./__tmp_result__/{project}/{case}/result_ochiai.txt".split(' ')
        run_cmd_and_check(cmd)
        cmd = f"docker cp ./__tmp_result__ {container2}:/SMARTFL/ochiai".split(' ')
        run_cmd_and_check(cmd)


if __name__ == "__main__":
    main()
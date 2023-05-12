#!/usr/bin/env python3

from parse import *
import os
from pathlib import Path
import subprocess
from asyncio.subprocess import DEVNULL
import logging
import multiprocessing
import parmap
from time import sleep
from tqdm import tqdm
from benchmark import benchmark
import random


PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flip_output'

RUN_DOCKER_SCRIPT = PROJECT_HOME / 'script/run-docker.py'

logging.basicConfig(
    level=logging.INFO,
    format=
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S")



def function_printer(project, case):
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

    print("[*] Printing function of : %s-%s" % (project, case))

    # run docker
    cmd = [f'{RUN_DOCKER_SCRIPT}', f'{project}-{case}', '-d', '--rm', '--name', f'{project}-{case}-function-printer']
    cmd = cmd + ['--mem', '40g'] if project == 'python' else cmd
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

    docker_id = f'{project}-{case}-function-printer'
    sleep(5)
    
    run_cmd_and_check(
        ['timeout', '10m', 'docker', 'exec', docker_id, '/bugfixer/localizer/main.exe', '-engine', 'function_print', '.'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
      
    run_cmd_and_check(
        ['docker', 'cp', f'{docker_id}:/experiment/function_list.txt', f"{str(COVERAGE_DIR / project / case / 'function_list.txt')}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    run_cmd_and_check(['docker', 'kill', f'{docker_id}'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)


def read_signal_list(signal_list_file):
    result = []
    for line in signal_list_file:
        parse_line = parse("{}:{}", line.strip())
        if parse_line != None:
            result.append((os.path.basename(parse_line[0]), parse_line[1]))
    return result
    

def main():
    for project in benchmark:
        for case in benchmark[project]:
            function_printer(project, case)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3

from parse import *
import os
from pathlib import Path
import subprocess
from asyncio.subprocess import DEVNULL
import logging
import multiprocessing

from benchmark import benchmark

PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flip_output'

RUN_DOCKER_SCRIPT = PROJECT_HOME / 'script/run-docker.py'

logging.basicConfig(
    level=logging.INFO,
    format=
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S")



def read_signal_list(signal_list_file):
    result = []
    for line in signal_list_file:
        parse_line = parse("{}:{}\t{} {} {}", line.strip())
        if parse_line != None:
            result.append(parse_line)
    return result


def write_signal_list(signal_list_file, signal_list):
    for line in signal_list:
        signal_list_file.write(f"{line[0]}:{line[1]}\t{line[2]} {line[3]} {line[4]}\n")
        # print(f"{line[0]}:{line[1]}\t0 0")


def filter_signal(project, case, signal_path, output_path, is_pos):
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

    print("[*] Filter signal of : %s-%s" % (project, case))

    # run docker
    
    if is_pos:
        docker_id = f'{project}-{case}-filter-pos'
    else:
        docker_id = f'{project}-{case}-filter-neg'
    
    cmd = [f'{RUN_DOCKER_SCRIPT}', f'{project}-{case}', '-d', '--rm', '--name', docker_id]
    
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
    

    run_cmd_and_check(
        ['docker', 'cp', f'{signal_path}', f'{docker_id}:/experiment/signal_list.txt'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    run_cmd_and_check(
        ['docker', 'cp', f"{str(COVERAGE_DIR / project / case / 'result_ochiai.txt')}", f'{docker_id}:/experiment/coverage.txt'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    run_cmd_and_check(
        ['docker', 'exec', docker_id, '/bugfixer/localizer/main.exe', '-engine', 'filter', '.'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    run_cmd_and_check(
        ['docker', 'cp', f'{docker_id}:/experiment/signal_list_filter.txt', f"{str(output_path)}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    run_cmd_and_check(['docker', 'kill', f'{docker_id}'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
    
    signal_list_file = open(output_path)
    signal_list = list(set(read_signal_list(signal_list_file)))
    signal_list_file.close()

    signal_list_file = open(output_path, 'w')
    write_signal_list(signal_list_file, signal_list)
    signal_list_file.close()



# def read_signal_list(signal_list_file):
#     result = []
#     for line in signal_list_file:
#         parse_line = parse("{}:{}\t{} {}", line.strip())
#         if parse_line != None:
#             result.append(parse_line)
#     return result


def main():
    for project in benchmark:
        for case in benchmark[project]:
            
            if os.path.exists(COVERAGE_DIR / project / case / 'result_signal.txt') and os.path.getsize(COVERAGE_DIR / project / case / 'result_signal.txt') > 2:
                signal_path = COVERAGE_DIR / project / case / 'result_signal.txt'
                output_path = COVERAGE_DIR / project / case / 'result_signal_filter.txt'
                filter_signal(project, case, str(signal_path), output_path, True)
                signal_file = open(signal_path)
                signal_list = read_signal_list(signal_file)
                for line in signal_list:
                    os.makedirs(COVERAGE_DIR / project / case / 'value' / line[0] / line[1], exist_ok=True)
                signal_file.close()                

            if os.path.exists(COVERAGE_DIR / project / case / 'result_signal_neg.txt') and os.path.getsize(COVERAGE_DIR / project / case / 'result_signal_neg.txt') > 2:
                signal_path = COVERAGE_DIR / project / case / 'result_signal_neg.txt'
                output_path = COVERAGE_DIR / project / case / 'result_signal_neg_filter.txt'
                filter_signal(project, case, str(signal_path), output_path, False)
                signal_file = open(signal_path)
                signal_list = read_signal_list(signal_file)
                for line in signal_list:
                    os.makedirs(COVERAGE_DIR / project / case / 'value' / line[0] / line[1], exist_ok=True)
                signal_file.close()



if __name__ == '__main__':
    main()
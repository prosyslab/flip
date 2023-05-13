#!/usr/bin/env python3

from parse import *
import os
from pathlib import Path
import subprocess
from asyncio.subprocess import DEVNULL
import logging
import multiprocessing

import yaml
import random

from benchmark import benchmark


PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flip_output'
YML_DIR = PROJECT_HOME / 'benchmark'

RUN_DOCKER_SCRIPT = PROJECT_HOME / 'script/run-docker.py'

logging.basicConfig(
    level=logging.INFO,
    format=
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S")


def get_test_num(project, case):
    with open(os.path.join(YML_DIR, project, f'{project}.bugzoo.yml')) as f:
        bug_data = yaml.load(f, Loader=yaml.FullLoader)
        neg_num = 0
        pos_num = 0
        for data in bug_data['bugs']:
            # print(data)
            if data['name'].split(':')[-1] == case:
                neg_num = int(data['test-harness']['failing'])
                pos_num = int(data['test-harness']['passing'])
                # print('FIND!!')
                break
        else:
            raise Exception("TEST NUM NOT FOUND")
    return neg_num, pos_num


def read_signal_file(signal_file):
    result = []
    for line in signal_file:
        parse_line = parse("{}:{}\t{} {} {}", line.strip())
        if parse_line != None:
            if (parse_line[0], parse_line[1]) in result:
                continue
            result.append((parse_line[0], parse_line[1]))
    result = list(map(lambda x: (x[0], *x[1]), enumerate(result)))
    return result


def main():
    for project in benchmark:
        for case in benchmark[project]:
            
            if not os.path.exists(COVERAGE_DIR / project / case / 'value'):
                continue 

            _, pos_num = get_test_num(project, case)

            signal_file = open(COVERAGE_DIR / project / case / 'result_signal_filter.txt')
            signal_list = read_signal_file(signal_file)
            signal_neg_file = open(COVERAGE_DIR / project / case / 'result_signal_neg_filter.txt')
            signal_neg_list = read_signal_file(signal_neg_file)
            os.makedirs(COVERAGE_DIR / project / case / 'value' / 'assume', exist_ok=True)

            rate_100_filter = []
            for (i, sig_file, sig_line) in signal_list:
                sig_file = os.path.basename(sig_file)
                if os.path.exists(COVERAGE_DIR / project / case / 'value' / sig_file / sig_line / 'result_ochiai_assume.txt'):
                    assume_result_file = open(COVERAGE_DIR / project / case / 'value' / sig_file / sig_line / 'result_ochiai_assume.txt')
                    assume_keep_rate = 100
                    for line in assume_result_file:
                        parse_line = parse("{}:{}\t{} {} {} {}", line.strip())
                        if parse_line == None:
                            continue
                        assume_keep_rate_tmp = (pos_num - (float(parse_line[3]) - float(parse_line[5])))/pos_num*100
                        if assume_keep_rate_tmp < assume_keep_rate:
                            assume_keep_rate = assume_keep_rate_tmp
                    if assume_keep_rate >= 100:
                        rate_100_filter.append((sig_file, sig_line))
            
            rate_100_filter_neg = []
            for (i, sig_file, sig_line) in signal_neg_list:
                sig_file = os.path.basename(sig_file)
                if os.path.exists(COVERAGE_DIR / project / case / 'value' / sig_file / sig_line / 'result_ochiai_assume.txt'):
                    assume_result_file = open(COVERAGE_DIR / project / case / 'value' / sig_file / sig_line / 'result_ochiai_assume.txt')
                    assume_keep_rate = 100
                    for line in assume_result_file:
                        parse_line = parse("{}:{}\t{} {} {} {}", line.strip())
                        if parse_line == None:
                            continue
                        assume_keep_rate_tmp = (pos_num - (float(parse_line[3]) - float(parse_line[5])))/pos_num*100
                        if assume_keep_rate_tmp < assume_keep_rate:
                            assume_keep_rate = assume_keep_rate_tmp
                    if assume_keep_rate >= 100:
                        rate_100_filter_neg.append((sig_file, sig_line))

            signal_100_list = (rate_100_filter + rate_100_filter_neg)
            
            if len(signal_100_list) > 0:
                combi_result = dict()
                for (sig_file, sig_line) in signal_100_list:
                    with open(COVERAGE_DIR / project / case / 'value' / sig_file / sig_line / 'result_ochiai_assume.txt') as assume_result_file:
                        for line in assume_result_file:
                            parse_line = parse("{}:{}\t{} {} {} {}", line.strip())
                            if parse_line==None:
                                continue
                            file, line, neg, pos, _, _ = parse_line
                            if (file, line) not in combi_result:
                                combi_result[(file, line)] = (0, 0)
                            combi_result[(file, line)] = (0, combi_result[(file, line)][1] + float(pos))
                
                os.makedirs(COVERAGE_DIR / project / case / 'value' / 'assume', exist_ok=True)
                
                with open(COVERAGE_DIR / project / case / 'value' / 'assume' / 'result_ochiai_assume_multi.txt', 'w') as result_file:
                    for ground in combi_result:
                        combi_result[ground] = (0, combi_result[ground][1] / len(signal_100_list))
                        result_file.write(f"{ground[0]}:{ground[1]}\t{combi_result[ground][0]} {combi_result[ground][1]} 0.0 0\n")


if __name__ == '__main__':
    main()
#!/usr/bin/env python3

import argparse
from parse import *
import os
import yaml
from pathlib import Path
import shutil
from benchmark import benchmark

PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flip_output'
YML_DIR = PROJECT_HOME / 'benchmark'


def get_neg_num(project, case):
    with open(os.path.join(YML_DIR, project, f'{project}.bugzoo.yml')) as f:
        bug_data = yaml.load(f, Loader=yaml.FullLoader)
        neg_num = 0
        for data in bug_data['bugs']:
            # print(data)
            if data['name'].split(':')[-1] == case:
                neg_num = int(data['test-harness']['failing'])
                # print('FIND!!')
                break
        else:
            raise Exception(f"{project}-{case}: NEG NUM NOT FOUND")
    return neg_num


def parse_result_file(file_name):
    result = dict()
    result_file = open(file_name)
    for i, line in enumerate(result_file):
        parse_line = parse("{}:{}\t{} {} {} {}", line.strip())
        if parse_line==None:
            print("ERROR:", line)
            continue
        file, line, neg, pos = parse_line[0], parse_line[1], parse_line[2], parse_line[3]
        if file not in result:
            result[file] = []
        result[file].append((int(line), int(float(neg)), int(float(pos))))
    return result


def sort_coverage(coverage):
    for file in coverage:
        coverage[file] = sorted(coverage[file], key = lambda x: x[0])
    return coverage


def extract_signal(coverage, max):
    count = 0
    signal_list = dict()
    signal_neg_list = dict()
    for file in coverage:
        signal_list[file]=[]
        signal_neg_list[file]=[]
        temp = coverage[file][0]
        for line in coverage[file]:
            if temp[1] == max and temp[1] == line[1] and temp[2] > line[2]:
                # print(temp, line)
                signal_list[file].append((temp, line, round((temp[2]-line[2])/temp[2], 3)))
                count += 1
            elif temp[1] == max and line[1] == 0 and temp[2] >= line[2]:
                signal_neg_list[file].append((temp, line, round(line[2]/temp[2], 3)))
                count += 1
            temp = line
    print("count:", count)
    return signal_list, signal_neg_list


def print_signal(signal_list, output_file):
    with open(output_file, 'w') as f:
        for file in signal_list:
            for sig in signal_list[file]:
                before, after, score = sig
                f.write(f"{file}:{before[0]}\t{before[1]} {before[2]} {score}\n")
                # f.write(f"{file}:{after[0]}\t{after[1]} {after[2]}\n\n")


def read_signal_file(signal_file):
    result = []
    for i, line in enumerate(signal_file):
        parse_line = parse("{}:{}\t{} {}", line.strip())
        if parse_line != None:
            result.append((parse_line[0], parse_line[1]))
    return result


def main():
    parser = argparse.ArgumentParser(description='Extract signal')
    for project in benchmark:
        for case in benchmark[project]:
            
            file_name = os.path.join(COVERAGE_DIR, project, case, "result_ochiai.txt")
            output_name = os.path.join(COVERAGE_DIR, project, case, "result_signal.txt")
            output_neg_name = os.path.join(COVERAGE_DIR, project, case, "result_signal_neg.txt")
            if not os.path.exists(file_name):
                continue
            max = get_neg_num(project, case)

            coverage = parse_result_file(file_name) # per file
            coverage = sort_coverage(coverage)
            print(project, case)
            signal_list, signal_neg_list = extract_signal(coverage, max)
            print_signal(signal_list, output_name)
            print_signal(signal_neg_list, output_neg_name)
            

if __name__ == '__main__':
    main()
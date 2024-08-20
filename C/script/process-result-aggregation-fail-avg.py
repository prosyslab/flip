#!/usr/bin/env python3

import os
import argparse
import yaml
import math
from parse import *
from pathlib import Path
from benchmark import benchmark, patch_location

PROJECT_HOME = Path(__file__).resolve().parent.parent
YML_DIR = os.path.join(PROJECT_HOME, 'benchmark')
COVERAGE_DIR = PROJECT_HOME / 'flex_result' / 'aggregation' / 'failing'

nef_sum = 0
nef_num = 0

all_sum = 0
all_num = 0

def ochiai (nef, nep, nnf, nnp):
    denom1 = nef + nnf
    denom2 = nef + nep
    denom = math.sqrt(denom1 * denom2)
    if denom == 0:
        return 0
    return nef / denom

def tarantula (nef, nep, nnf, nnp):
    neg_num = nef+nnf
    pos_num = nep + nnp
    num = nef / neg_num
    denom = num + nep / pos_num
    if denom == 0:
        return 0
    return num / denom


def dstar (nef, nep, nnf, nnp):
    neg_num = nef+nnf
    pos_num = nep + nnp
    num = nef * nef
    denom = nnf + nep
    if denom == 0:
        return 1000000
    return num / denom

def read_function_list(project, case):
    function_list = {}
    with open(COVERAGE_DIR / project / case / 'function_list.txt', 'r') as f:
        for line in f:
            parse_line = parse("{}:{}", line.strip())
            filename, lineno = os.path.basename(parse_line[0]), int(parse_line[1])
            if filename not in function_list:
                function_list[filename] = []
            function_list[filename].append(lineno)
        for filename in function_list:
            function_list[filename].sort()
    return function_list


def find_function_line(function_list, filename, lineno):
    if os.path.basename(filename) not in function_list:
        raise Exception("filename not in function list")
    for i, function_line in enumerate(function_list[os.path.basename(filename)]):
        if function_line > lineno:
            return i - 1
    return len(function_list[os.path.basename(filename)]) - 1

def make_patch_location_function(function_list, project, case):
    patch_location_fun = {}
    tmp_result = []
    for location in patch_location[project][case]:
        if not location[0].endswith(".c"):
            continue
        new_location = (location[0], function_list[location[0]][find_function_line(function_list, location[0], location[1])])
        tmp_result.append(new_location)
    patch_location_fun[project] = {}
    patch_location_fun[project][case] = tmp_result
    return patch_location_fun


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

def open_result(project, case, result_file):
    result_path = os.path.join(COVERAGE_DIR, project, case, result_file)
    result_file = open(result_path, 'r')
    return result_file


def get_rank_list(project, case, result_file):
    global nef_num, nef_sum, all_num, all_sum
    file = open_result(project, case, result_file)
    rank_list = []
    neg_num , pos_num = get_test_num(project, case)
    max_nef = 0
    for i, line in enumerate(file):
        split_line = parse("{}:{},{},{}", line.strip())
        rank, ground = i + 1, (os.path.basename(split_line[0]),
                                                      int(split_line[1]))
        nef = float(split_line[2])
        nep = float(split_line[3])
        nnf = neg_num - nef
        nnp = pos_num - nep
        score = ochiai(nef, nep, nnf, nnp)
        rank_list.append((rank, score, ground))
        if nef > 0:
            all_num += 1
            all_sum += nef
        if ground in patch_location[project][case]:
            if nef > max_nef:
                max_nef = nef

    # function_list = read_function_list(project, case)
    # func_rank_dict = {}
    # for rank, score, ground in rank_list:
    #     filename, lineno = ground
    #     # (location[0], function_list[location[0]][find_function_line(function_list, location[0], location[1])])
    #     if os.path.basename(filename) not in function_list:
    #         func_rank_dict[ground] = score
    #         continue
    #     new_ground = (filename, function_list[os.path.basename(filename)][find_function_line(function_list, filename, lineno)])
    #     if new_ground not in func_rank_dict:
    #         func_rank_dict[new_ground] = score
    #     else:
    #         func_score = func_rank_dict[new_ground]
    #         if score < func_score and score > 0:
    #             func_rank_dict[new_ground] = score
    # rank_list = []
    # for ground in func_rank_dict:
    #     rank_list.append((0, func_rank_dict[ground], ground))

    rank_list.sort(key=lambda x: -(x[1]))
    rank_list = [(j+1, x[1], x[2]) for j, x in enumerate(rank_list)]
    
    nef_num += 1
    nef_sum += max_nef
    file.close()
    return rank_list


def get_answer_index(project, case, rank_list):
    # patch_location_fun = make_patch_location_function(read_function_list(project, case), project, case)
    # patch_location = patch_location_fun
    for rank, score, ground in rank_list:
        if ground in patch_location[project][case]:
            return score, rank
    return 2.0, -1


def get_same_rank(rank_list, answer_score):
    start = -1

    for rank, score, _ in rank_list:
        if score == answer_score:
            if start < 0:
                start = rank
        elif score < answer_score:
            return start, rank - 1
    #print(start, i)
    return start, len(rank_list)


def calculate_info(rank, start, end):
    return end, end - start + 1, len(rank)


def get_one_result(project, case, result_file):
    try:
        rank_list = get_rank_list(project, case, result_file)
        answer_score, answer_index = get_answer_index(project, case, rank_list)
        start, end = get_same_rank(rank_list, answer_score)
        rank, tie, total = calculate_info(rank_list, start, end)
        return rank, tie, total
    except FileNotFoundError:
        return 0, 0, 0


def get_result(args, result_file):
    result = {}

    project, case = args.project, args.case

    if project:
        if case:
            result[project] = {
                case: get_one_result(project, case, result_file)
            }
        else:
            temp_project = {}
            for case in benchmark[project]:
                temp_project[case] = get_one_result(project, case, result_file)
            result[project] = temp_project
    else:
        for project in benchmark:
            temp_project = {}
            for case in benchmark[project]:
                temp_project[case] = get_one_result(project, case, result_file)
            result[project] = temp_project
    return result


def print_result(result_list):
    #print(result)
    new_result = {}
    print("Project\tCase\tRank")
    for result in result_list:
        for project in result:
            if project not in new_result:
                new_result[project] = {}
            for case in result[project]:
                if case not in new_result[project]:
                    new_result[project][case] = []
                new_result[project][case].append(str(result[project][case][0]))
    for project in new_result:
        for case in new_result[project]:
            print(project + "\t" + case + "\t" +
                  "\t".join(new_result[project][case]))


def main():

    parser = argparse.ArgumentParser(
        description='Get result data of project-case')
    parser.add_argument('-p', '--project', type=str)
    parser.add_argument('-c', '--case', type=str)
    args = parser.parse_args()
    result = get_result(args, 'cov_result.txt')
    print_result([result])


if __name__ == '__main__':
    main()

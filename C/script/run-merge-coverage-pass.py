#!/usr/bin/env python3

import os
import argparse
from parse import *
from benchmark import benchmark, patch_location, opt_case
# from benchmark import benchmark
# from benchmark import patch_location_fun as patch_location
from pathlib import Path
import math
import yaml
# import gspread
from time import sleep


PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flex_output'
YML_DIR = PROJECT_HOME / 'benchmark'


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


def open_result(project, case, result_file, default_file):
    result_file = open(result_file, 'r')
    default_file = open(default_file, 'r')
    return result_file, default_file


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
    if filename not in function_list:
        raise Exception("filename not in function list")
    for i, function_line in enumerate(function_list[filename]):
        if function_line > lineno:
            return i - 1
    return len(function_list[filename]) - 1

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


def get_rank_list(project, case, result_file, default_file):
    result_file, default_file = open_result(project, case, result_file, default_file)
    neg_num , pos_num = get_test_num(project, case)

    rank_list = []
    default_neg_cov = {}
    assert_neg_cov = {}
    neg_nonzero = 0
    for i, line in enumerate(default_file):
        split_line = parse("{}:{}\t{} {} {} {}", line.strip())
        file, line, neg = split_line[0], int(split_line[1]), float(split_line[2])
        
        default_neg_cov[(file, line)] = neg
    total_num = 0
    weird_num = 0
    for i, line in enumerate(result_file):
        split_line = parse("{}:{}\t{} {} {} {}", line.strip())
        if case not in opt_case and float(split_line[3]) < 1:
            continue
        
        rank, score, ground = i + 1, float(split_line[-2]), (split_line[0], int(split_line[1]))

        nef = default_neg_cov[ground] if ground in default_neg_cov else 0
        nep = float(split_line[3])
        if nef == 0 and nep == 0:
            weird_num += 1
            continue
        total_num += 1
        nnf = neg_num - nef
        nnp = pos_num - nep
        score = ochiai(nef, nep, nnf, nnp)
        
        rank = int(rank)
        score = float(score)
        rank_list.append((score, ground, (nef, nep)))
    rank_list.sort(key=lambda x: -(x[0]))
        
    rank_list = [(j+1, x[0], x[1], x[2]) for j, x in enumerate(rank_list)]
    rank_dict = {}

    # function_list = read_function_list(project, case)
    # func_rank_dict = {}
    # for rank, score, ground, cov in rank_list:
    #     filename, lineno = ground
    #     # (location[0], function_list[location[0]][find_function_line(function_list, location[0], location[1])])
    #     if filename not in function_list:
    #         func_rank_dict[ground] = (score, cov)
    #         continue
    #     new_ground = (filename, function_list[filename][find_function_line(function_list, filename, lineno)])
    #     if new_ground not in func_rank_dict:
    #         func_rank_dict[new_ground] = (score, cov)
    #     else:
    #         func_score = func_rank_dict[new_ground][0]
    #         if score < func_score and score > 0:
    #             func_rank_dict[new_ground] = (score, cov)
    # rank_list = []
    # for ground in func_rank_dict:
    #     rank_list.append((0, func_rank_dict[ground][0], ground, func_rank_dict[ground][1]))
    
    rank_list.sort(key=lambda x: -(x[1]))
    rank_list = [(j+1, x[1], x[2], x[3]) for j, x in enumerate(rank_list)]


    result_file.close()
    cov_result_path = COVERAGE_DIR / project / case / "result_ochiai_final.txt"
    os.makedirs(os.path.dirname(cov_result_path), exist_ok=True)
    
    with open(cov_result_path, 'w') as cov_result_file:
        for _, score, (filename, lineno), cov in rank_list:
            cov_result_file.write("{}:{},{},{}\n".format(filename, lineno, cov[0], cov[1]))
    
    return rank_list


def get_answer_index(project, case, rank_list):
    # patch_location_fun = make_patch_location_function(read_function_list(project, case), project, case)
    # patch_location = patch_location_fun
    for rank, score, ground, _ in rank_list:
        if (os.path.basename(ground[0]), ground[1]) in patch_location[project][case]:
            return score, rank
    return 2.0, -1


def get_same_rank(rank_list, answer_score):
    start = -1

    for rank, score, _, _ in rank_list:
        if score == answer_score:
            if start < 0:
                start = rank
        elif score < answer_score:
            return start, rank - 1
    return start, len(rank_list)


def calculate_info(rank, start, end):
    return end, end - start + 1, len(rank)


def get_one_result(project, case, result_file, default_file):
    try:
        rank_list = get_rank_list(project, case, result_file, default_file)
        answer_score, answer_index = get_answer_index(project, case, rank_list)
        start, end = get_same_rank(rank_list, answer_score)
        rank, tie, total = calculate_info(rank_list, start, end)
        return rank, tie, total
    except FileNotFoundError:
        return 0, 0, 0


def get_result(project, case, result_file, default_file):
    result = {}

    if project:
        if case:
            result[project] = {
                case: get_one_result(project, case, result_file, default_file)
            }
        else:
            temp_project = {}
            for case in benchmark[project]:
                temp_project[case] = get_one_result(project, case, result_file, default_file)
            result[project] = temp_project
    else:
        for project in benchmark:
            temp_project = {}
            for case in benchmark[project]:
                temp_project[case] = get_one_result(project, case, result_file, default_file)
            result[project] = temp_project
    return result


def print_result(result_list):
    new_result = {}
    for result in result_list:
        for project in result:
            if project not in new_result:
                new_result[project] = {}
            for case in result[project]:
                if case not in new_result[project]:
                    new_result[project][case] = []
                new_result[project][case].append("\t".join(
                    map(str, result[project][case])))
    for project in new_result:
        for case in new_result[project]:
            print(project + "\t" + case + "\t" +
                  "\t".join(new_result[project][case]))


def roundTraditional(val, digits):
    return round(val+10**(-len(str(val))-1), digits)


def main():
    parser = argparse.ArgumentParser(
        description='Get result data of project-case')
    parser.add_argument('-p', '--project', type=str)
    parser.add_argument('-c', '--case', type=str)
    parser.add_argument('-e', '--engine', type=str)
    args = parser.parse_args()


    print("Project\tCase\tRank\tTie\tTotal")
    for project in benchmark:
        for case in benchmark[project]:
            if not os.path.exists(COVERAGE_DIR / project / case / 'value'):
                continue
            origin_path = os.path.join(COVERAGE_DIR, project, case, 'result_ochiai.txt')
            result_file = os.path.join(COVERAGE_DIR, project, case, 'value', 'assume', 'result_ochiai_assume_multi.txt')
            if not os.path.exists(result_file):
                result_file = origin_path
            default_file = origin_path
            result = get_result(project, case, result_file, default_file)
            print_result([result])


if __name__ == '__main__':
    main()

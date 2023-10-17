#!/usr/bin/env python3

import subprocess
from parse import *
from tqdm import tqdm
import os
import xml.etree.ElementTree as elemTree
import math
import filecmp
import json
import sys
from benchmark import benchmark


def read_coverage(coverage_path):
    coverage = dict()

    with open(coverage_path, 'r') as f:
        for line in f.readlines():
            parse_line = parse("{}:{}\t{} {} {}", line.strip())
            if parse_line != None:
                classname, line_num, nef, nep, score = parse_line
                if '$' in classname:
                    classname = classname.split('$')[0]
                if classname not in coverage:
                    coverage[classname] = dict()
                coverage[classname][line_num] = [float(nef), float(nep)]
    return coverage


def get_neg_test(neg_test_path):
    neg_test_list = []
    with open(neg_test_path) as f:
        neg_test_list = list(map(lambda x: x.strip(), f.readlines()))
    return neg_test_list


def ochiai(nef, nep, nnf, nnp):
    denom1 = nef + nnf
    denom2 = nef + nep
    denom = math.sqrt(denom1 * denom2)
    if denom == 0:
        return 0
    return nef / denom


def pass_oracle(project, case, targetname, lineno):
    # if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass"):
    #     for targetname in os.listdir(f"/flip/test/coverage/{project}/{case}/pass"):
    #         if os.path.isdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}") and targetname.endswith(".java"):
    #             # print(targetname)
    #             for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}"):
    if not os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/pass"):
        return False
    elif not os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/fail"):
        return True
    elif len(os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/pass"))/len(os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/fail")) >= 0.9:
        return True
    return False


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = str(i+1)
        if os.path.exists(f"/flip/test/coverage/{project}/{case}/result_ochiai.txt"):
            origin_coverage = read_coverage(
                f"/flip/test/coverage/{project}/{case}/result_ochiai.txt")

            pass_coverage = dict()
            fail_coverage = dict()
            remove_coverage = dict()
            delete_coverage = dict()

            neg_test_list = get_neg_test(
                f"/flip/test/coverage/{project}/{case}/neg_test")
            coverage = dict()

            cov_file_list = os.listdir(
                f"/flip/test/coverage/{project}/{case}/coverage")

            neg_num = len(neg_test_list)
            pos_num = len(cov_file_list)-neg_num

            if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass"):
                pass_num = 0
                for targetname in os.listdir(f"/flip/test/coverage/{project}/{case}/pass"):
                    if os.path.isdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}") and targetname.endswith(".java"):
                        for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}"):
                            pass_cov_path = f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/result_ochiai.txt"
                            tmp_pass_coverage = dict()
                            if os.path.exists(pass_cov_path):
                                tmp_pass_coverage = read_coverage(
                                    pass_cov_path)
                                with open(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/line_matching.json", 'r') as line_matching_file:
                                    line_mapping = json.load(
                                        line_matching_file)
                                for class_name in tmp_pass_coverage:
                                    print(class_name.split('.'))
                                    if class_name not in pass_coverage:
                                        pass_coverage[class_name] = dict()
                                    for line_num in tmp_pass_coverage[class_name]:
                                        print(project, case, targetname,
                                              lineno, line_num)
                                        mapped_line = str(line_mapping['changed_files'][f"{class_name.split('.')[-1]}.java"][str(line_num)] if f"{class_name.split('.')[-1]}.java" in line_mapping['changed_files'] and str(
                                            line_num) in line_mapping['changed_files'][f"{class_name.split('.')[-1]}.java"] else line_num)
                                        if mapped_line not in pass_coverage[class_name]:
                                            pass_coverage[class_name][mapped_line] = [
                                                0, 0]

                                        pass_coverage[class_name][mapped_line][0] += tmp_pass_coverage[class_name][line_num][0]
                                        pass_coverage[class_name][mapped_line][1] += tmp_pass_coverage[class_name][line_num][1]
                                pass_num += 1
                for class_name in pass_coverage:
                    for line_num in pass_coverage[class_name]:
                        pass_coverage[class_name][line_num][0] = pass_coverage[class_name][line_num][0] / pass_num
                        pass_coverage[class_name][line_num][1] = pass_coverage[class_name][line_num][1] / pass_num
            if os.path.exists(f"/flip/test/coverage/{project}/{case}/fail"):
                fail_num = 0
                for targetname in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
                    if os.path.isdir(f"/flip/test/coverage/{project}/{case}/fail/{targetname}") and targetname.endswith(".java"):
                        for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/fail/{targetname}"):
                            fail_cov_path = f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/result_ochiai.txt"
                            tmp_fail_coverage = dict()
                            if os.path.exists(fail_cov_path):
                                tmp_fail_coverage = read_coverage(
                                    fail_cov_path)
                                with open(f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/vimdiff_line_matching.json", 'r') as line_matching_file:
                                    line_mapping = json.load(
                                        line_matching_file)
                                for class_name in tmp_fail_coverage:
                                    if class_name not in fail_coverage:
                                        fail_coverage[class_name] = dict()
                                    for line_num in tmp_fail_coverage[class_name]:
                                        mapped_line = str(line_mapping['changed_files'][f"{class_name.split('.')[-1]}.java"][str(line_num)] if f"{class_name.split('.')[-1]}.java" in line_mapping['changed_files'] and str(
                                            line_num) in line_mapping['changed_files'][f"{class_name.split('.')[-1]}.java"] else line_num)
                                        if mapped_line in remove_coverage:
                                            continue
                                        if mapped_line not in fail_coverage[class_name]:
                                            fail_coverage[class_name][mapped_line] = tmp_fail_coverage[class_name][line_num]
                                        fail_coverage[class_name][mapped_line][0] = min(
                                            tmp_fail_coverage[class_name][line_num][0], fail_coverage[class_name][mapped_line][0])
                                        fail_coverage[class_name][mapped_line][1] = min(
                                            tmp_fail_coverage[class_name][line_num][1], fail_coverage[class_name][mapped_line][1])
                                mapped_tmp_fail_coverage = dict()
                                for class_name in tmp_fail_coverage:
                                    mapped_tmp_fail_coverage[class_name] = dict(
                                    )
                                    for line_num in tmp_fail_coverage[class_name]:
                                        mapped_line = str(line_mapping['changed_files'][f"{class_name.split('.')[-1]}.java"][str(line_num)] if f"{class_name.split('.')[-1]}.java" in line_mapping['changed_files'] and str(
                                            line_num) in line_mapping['changed_files'][f"{class_name.split('.')[-1]}.java"] else line_num)
                                        mapped_tmp_fail_coverage[class_name][
                                            mapped_line] = tmp_fail_coverage[class_name][line_num]
                                for class_name in fail_coverage:
                                    for line_num in fail_coverage[class_name]:
                                        if class_name in mapped_tmp_fail_coverage and line_num in mapped_tmp_fail_coverage[class_name]:
                                            continue
                                        else:
                                            fail_coverage[class_name][line_num][0] = 0
                                fail_num += 1
            for class_name in origin_coverage:
                for line_num in origin_coverage[class_name]:
                    if class_name in pass_coverage and line_num in pass_coverage[class_name]:
                        origin_coverage[class_name][line_num][1] = max(
                            pass_coverage[class_name][line_num][1], origin_coverage[class_name][line_num][1])
                    if class_name in fail_coverage and line_num in fail_coverage[class_name]:
                        origin_coverage[class_name][line_num][0] = min(
                            fail_coverage[class_name][line_num][0], origin_coverage[class_name][line_num][0])
                    elif len(fail_coverage) > 0:
                        origin_coverage[class_name][line_num][0] = 0

            fl_result = []

            for class_name in origin_coverage:
                for line_num in origin_coverage[class_name]:
                    nef, nep = origin_coverage[class_name][line_num]
                    nnf, nnp = neg_num - nef, pos_num - nep
                    score = ochiai(nef, nep, nnf, nnp)
                    fl_result.append(
                        (class_name, line_num, nef, nep, score))

            fl_result.sort(key=lambda x: -x[-1])

            with open(f"/flip/test/coverage/{project}/{case}/result_ochiai_final.txt", 'w') as f:
                for line in fl_result:
                    f.write(
                        f"{line[0]}:{line[1]}\t{line[2]} {line[3]} {line[4]}\n")


if __name__ == "__main__":
    main()

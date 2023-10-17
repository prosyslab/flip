#!/usr/bin/env python3

import subprocess
from parse import *
from tqdm import tqdm
import os
import xml.etree.ElementTree as elemTree
import math
import parmap
import random
import sys
from benchmark import benchmark


def read_coverage(coverage_path):
    # print(coverage_path)
    tree = elemTree.parse(coverage_path)
    root = tree.getroot()
    packages = root.find("packages")

    coverage = dict()

    for package in packages:
        package_name = package.attrib['name']
        classes = package.find('classes')
        for class_ in classes:
            class_name = class_.attrib['name']
            if class_name not in coverage:
                coverage[class_name] = dict()
            lines = class_.find('lines')
            for line in lines:
                line_num = int(line.attrib['number'])
                hits = int(line.attrib['hits'])
                if hits > 0:
                    coverage[class_name][line_num] = hits
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


def run_fl(run_info):
    project, case = run_info

    neg_test_list = get_neg_test(
        f"/flip/test/coverage/{project}/{case}/neg_test")
    coverage = dict()

    cov_file_list = os.listdir(
        f"/flip/test/coverage/{project}/{case}/coverage")

    neg_num = len(neg_test_list)
    pos_num = len(cov_file_list)-neg_num

    for cov_file in tqdm(cov_file_list):
        method = os.path.splitext(cov_file)[0]
        try:
            tmp_coverage = read_coverage(os.path.join(
                f"/flip/test/coverage/{project}/{case}/coverage", cov_file))
            for class_name in tmp_coverage:
                if class_name not in coverage:
                    coverage[class_name] = dict()
                for line_num in tmp_coverage[class_name]:
                    if line_num not in coverage[class_name]:
                        coverage[class_name][line_num] = [0, 0]
                    if method in neg_test_list:
                        coverage[class_name][line_num][0] += 1
                    else:
                        coverage[class_name][line_num][1] += 1
        except:
            continue

    fl_result = []

    for class_name in coverage:
        for line_num in coverage[class_name]:
            nef, nep = coverage[class_name][line_num]
            nnf, nnp = neg_num - nef, pos_num - nep
            score = ochiai(nef, nep, nnf, nnp)
            fl_result.append(
                (class_name, line_num, nef, nep, score))

    fl_result.sort(key=lambda x: -x[-1])

    with open(f"/flip/test/coverage/{project}/{case}/result_ochiai.txt", 'w') as f:
        for line in fl_result:
            f.write(
                f"{line[0]}:{line[1]}\t{line[2]} {line[3]} {line[4]}\n")


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = str(i+1)
        # if os.path.exists(f"/flip/test/{project}/{case}") and not os.path.exists(f"/flip/test/coverage/{project}/{case}/result_ochiai.txt"):
        work_list.append((project, case))

    num_process = 60
    random.shuffle(work_list)
    # split_work_list = split_list(work_list, num_process)
    parmap.map(run_fl, work_list,
               pm_pbar=True, pm_processes=num_process)


if __name__ == "__main__":
    main()

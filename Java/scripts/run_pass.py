#!/usr/bin/env python3

import subprocess
from parse import *
from tqdm import tqdm
import os
import xml.etree.ElementTree as elemTree
import math
import filecmp
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
    elif len(os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/pass"))/(len(os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/fail"))+len(os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/pass"))) >= 0.5:
        return True
    return False


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = str(i+1)
        if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass"):

            # neg_test_list = get_neg_test(
            #     f"/flip/test/coverage/{project}/{case}/neg_test")
            # coverage = dict()

            # neg_num = len(neg_test_list)
            # pos_num = len(cov_file_list)-neg_num

            # filename_list = []
            # for filename in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
            #     # print(filename)
            #     if filename.startswith("call"):
            #         filename_list.append(filename)

            for targetname in os.listdir(f"/flip/test/coverage/{project}/{case}/pass"):
                if os.path.isdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}") and targetname.endswith(".java"):
                    for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/pass/{targetname}"):
                        if pass_oracle(project, case, targetname, lineno):
                            coverage = dict()

                            cov_file_list_fail = list(map(lambda x: os.path.join(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/fail", x), filter(lambda x: "coverage" in x, os.listdir(
                                f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/fail")))) if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/fail") else []

                            cov_file_list_pass = list(map(lambda x: os.path.join(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/pass", x), filter(lambda x: "coverage" in x, os.listdir(
                                f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/pass")))) if os.path.exists(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/pass") else []

                            cov_file_list = cov_file_list_fail + cov_file_list_pass

                            for cov_file in cov_file_list:
                                # method = os.path.splitext(cov_file)[0]
                                try:
                                    tmp_coverage = read_coverage(cov_file)
                                    for class_name in tmp_coverage:
                                        if class_name not in coverage:
                                            coverage[class_name] = dict()
                                        for line_num in tmp_coverage[class_name]:
                                            if line_num not in coverage[class_name]:
                                                coverage[class_name][line_num] = [
                                                    0, 0]
                                            coverage[class_name][line_num][1] += 1
                                except:
                                    continue
                            print(project, case, targetname,
                                  lineno, len(coverage))
                            fl_result = []

                            for class_name in coverage:
                                for line_num in coverage[class_name]:
                                    nef, nep = coverage[class_name][line_num]
                                    # nnf, nnp = neg_num - nef, pos_num - nep
                                    # score = ochiai(nef, nep, nnf, nnp)
                                    fl_result.append(
                                        (class_name, line_num, nef, nep, 0.0))

                            # fl_result.sort(key=lambda x: -x[-1])

                            with open(f"/flip/test/coverage/{project}/{case}/pass/{targetname}/{lineno}/result_ochiai.txt", 'w') as f:
                                for line in fl_result:
                                    f.write(
                                        f"{line[0]}:{line[1]}\t{line[2]} {line[3]} {line[4]}\n")


if __name__ == "__main__":
    main()

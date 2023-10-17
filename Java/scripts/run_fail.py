#!/usr/bin/env python3

import subprocess
from parse import *
from tqdm import tqdm
import os
import xml.etree.ElementTree as elemTree
import math
import filecmp
import json
from difflib import SequenceMatcher
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


def compare_call_sequence(project, case, targetname, lineno, filename_list):
    i = 0
    # filename_list = []
    # for filename in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
    #     # print(filename)
    #     if filename.startswith("call"):
    #         filename_list.append(filename)
    # for targetname in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
    #     if os.path.isdir(f"/flip/test/coverage/{project}/{case}/fail/{targetname}") and targetname.endswith(".java"):
    # print(targetname)
    # for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/fail/{targetname}"):
    check = True
    for filename in filename_list:
        if os.path.exists(f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/{filename}"):
            # with open(f"/flip/test/coverage/{project}/{case}/{filename}", 'r') as origin and open(f"/flip/test/coverage/{project}/{case}/{targetname}/{lineno}/{filename}", 'r') as mutant:
            if filecmp.cmp(f"/flip/test/coverage/{project}/{case}/fail/{filename}", f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/{filename}"):
                # with open(f"/flip/test/coverage/{project}/{case}/fail/{filename}") as origin, open(f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/{filename}") as branch:
                #     origin_call_sequence = origin.readlines()
                #     branch_call_sequence = branch.readlines()
                #     if SequenceMatcher(None, origin_call_sequence, branch_call_sequence).ratio() >= 0.99:
                continue
                # print("same callsequence detected")
        check = False
        break
    return check


def compare_error(project, case, targetname, lineno, filename_list):
    i = 0
    # filename_list = []
    # for filename in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
    #     # print(filename)
    #     if filename.startswith("call"):
    #         filename_list.append(filename)
    # for targetname in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
    #     if os.path.isdir(f"/flip/test/coverage/{project}/{case}/fail/{targetname}") and targetname.endswith(".java"):
    # print(targetname)
    # for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/fail/{targetname}"):
    check = True
    if filename_list == []:
        check = False
    with open(f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/vimdiff_line_matching.json", 'r') as line_matching_file:
        line_mapping = json.load(
            line_matching_file)
    for filename in filename_list:
        if os.path.exists(f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/{filename}"):
            # with open(f"/flip/test/coverage/{project}/{case}/{filename}", 'r') as origin and open(f"/flip/test/coverage/{project}/{case}/{targetname}/{lineno}/{filename}", 'r') as mutant:
            # if filecmp.cmp(f"/flip/test/coverage/{project}/{case}/fail/{filename}", f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/{filename}"):
            with open(f"/flip/test/coverage/{project}/{case}/fail/{filename}") as origin, open(f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/{filename}") as branch:
                origin_call_sequence = origin.readlines()
                branch_call_sequence = branch.readlines()
                # and SequenceMatcher(None, origin_call_sequence, branch_call_sequence).ratio() >= 0.9:
                # if (targetname, lineno) == ("PoissonDistributionImpl.java", "93"):
                #     print(origin_call_sequence[1], branch_call_sequence[1])
                if len(origin_call_sequence) >= 2 and len(branch_call_sequence) >= 2 and origin_call_sequence[1] == branch_call_sequence[1]:
                    for i in range(2, len(origin_call_sequence)):
                        # if "at " in origin_call_sequence[i] and "org." in origin_call_sequence[i] and "->" not in origin_call_sequence[i] and "at " in branch_call_sequence[i] and "org." in branch_call_sequence[i] and "->" not in branch_call_sequence[i]:
                        # print(branch_call_sequence[i])
                        origin_parse_line = parse(
                            "{}({}:{}){}", origin_call_sequence[i])
                        branch_parse_line = parse(
                            "{}({}:{}){}", branch_call_sequence[i])
                        # print(branch_call_sequence[i])
                        # print(branch_call_sequence[-1])
                        if origin_parse_line == None or branch_parse_line == None:
                            continue
                        _, origin_error_file, origin_error_lineno, _ = origin_parse_line
                        _, branch_error_file, branch_error_lineno, _ = branch_parse_line

                        mapped_line = str(line_mapping['changed_files'][branch_error_file][branch_error_lineno] if branch_error_file in line_mapping['changed_files'] and str(
                            branch_error_lineno) in line_mapping['changed_files'][branch_error_file] else branch_error_lineno)

                        if origin_error_file == branch_error_file and mapped_line == origin_error_lineno:
                            continue
                        else:
                            return False
                else:
                    return False
            # print("same callsequence detected")
        # check = False
        # break
        else:
            return False
    return check


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = str(i+1)
        # if case != '62':
        #     continue
        if os.path.exists(f"/flip/test/coverage/{project}/{case}/fail"):

            # neg_test_list = get_neg_test(
            #     f"/flip/test/coverage/{project}/{case}/neg_test")
            # coverage = dict()

            # neg_num = len(neg_test_list)
            # pos_num = len(cov_file_list)-neg_num

            filename_list_call = []
            filename_list_error = []
            for filename in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
                # print(filename)
                if filename.startswith("failing"):
                    filename_list_error.append(filename)
                if filename.startswith("call"):
                    filename_list_call.append(filename)
            # print(project, case)
            for targetname in os.listdir(f"/flip/test/coverage/{project}/{case}/fail"):
                if targetname != "VarCheck.java":
                    continue
                if os.path.isdir(f"/flip/test/coverage/{project}/{case}/fail/{targetname}") and targetname.endswith(".java"):
                    for lineno in os.listdir(f"/flip/test/coverage/{project}/{case}/fail/{targetname}"):
                        print(project, case, targetname, lineno)
                        # and compare_call_sequence(project, case, targetname, lineno, filename_list_call):
                        if compare_error(project, case, targetname, lineno, filename_list_error) and compare_call_sequence(project, case, targetname, lineno, filename_list_call):
                            # print(project, case, targetname, lineno)
                            coverage = dict()

                            cov_file_list = list(filter(lambda x: "coverage" in x and not x.endswith(".bak"), os.listdir(
                                f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}")))

                            for cov_file in cov_file_list:
                                # method = os.path.splitext(cov_file)[0]
                                try:
                                    tmp_coverage = read_coverage(os.path.join(
                                        f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}", cov_file))
                                    for class_name in tmp_coverage:
                                        if class_name not in coverage:
                                            coverage[class_name] = dict()
                                        for line_num in tmp_coverage[class_name]:
                                            if line_num not in coverage[class_name]:
                                                coverage[class_name][line_num] = [
                                                    0, 0]
                                            coverage[class_name][line_num][0] += 1
                                except:
                                    continue

                            fl_result = []

                            for class_name in coverage:
                                for line_num in coverage[class_name]:
                                    nef, nep = coverage[class_name][line_num]
                                    # nnf, nnp = neg_num - nef, pos_num - nep
                                    # score = ochiai(nef, nep, nnf, nnp)
                                    fl_result.append(
                                        (class_name, line_num, nef, nep, 1.0))

                            # fl_result.sort(key=lambda x: -x[-1])

                            with open(f"/flip/test/coverage/{project}/{case}/fail/{targetname}/{lineno}/result_ochiai.txt", 'w') as f:
                                for line in fl_result:
                                    f.write(
                                        f"{line[0]}:{line[1]}\t{line[2]} {line[3]} {line[4]}\n")


if __name__ == "__main__":
    main()

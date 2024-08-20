#!/usr/bin/env python3

import subprocess
from parse import *
from tqdm import tqdm
import os
import xml.etree.ElementTree as elemTree
import math
import filecmp
from benchmark import patch_location, benchmark
import sys


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
                coverage[classname][line_num] = [
                    float(nef), float(nep), float(score)]
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


def main():
    project = sys.argv[1]
    work_list = []
    for i in benchmark[project]:
        case = str(i+1)

        if case not in patch_location[project]:
            print(f"{project}\t{case}\t-\t-")
            continue

        answers = patch_location[project][case]

        if os.path.exists(f"/flip/test/coverage/{project}/{case}/result_ochiai_final.txt"):
            coverage = read_coverage(
                f"/flip/test/coverage/{project}/{case}/result_ochiai_final.txt")

            fl_result = []

            for class_name in coverage:
                for line_num in coverage[class_name]:
                    nef, nep, score = coverage[class_name][line_num]
                    # nnf, nnp = neg_num - nef, pos_num - nep
                    # score = ochiai(nef, nep, nnf, nnp)
                    fl_result.append(
                        (class_name, line_num, nef, nep, score))

            fl_result.sort(key=lambda x: -x[-1])
            scores = []
            # print(answers)
            for answer_file, answer_line in answers:
                infos = list(
                    filter(lambda x: answer_file == x[0] and answer_line == int(x[1]), fl_result))
                infos.sort(key=lambda x: -x[-1])
                # print(infos)
                if len(infos) < 1:
                    continue
                scores.append(infos[0][-1])
            if len(scores) < 1:
                print(f"{project}\t{case}\t-\t-")
                continue
            max_score = max(scores)

            combine_rank = sum(x[-1] > max_score for x in fl_result) + 1
            rank = sum(x[-1] >= max_score for x in fl_result)
            tie = sum(x[-1] == max_score for x in fl_result)
            t_f = sum(x == max_score for x in scores)
            t = tie

            denom = math.comb(t, t_f)

            combine_rank = int(combine_rank +
                               sum([k * math.comb((t-k-1), t_f-1) /
                                    denom for k in range(1, t-t_f+1)]))

            print(f"{project}\t{case}\t{combine_rank}")

            # for line in enumerate(fl_result):
        else:
            print(f"{project}\t{case}\t-")


if __name__ == "__main__":
    main()

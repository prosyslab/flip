#!/usr/bin/env python3

import argparse
from datetime import datetime
import logging
import os
import subprocess
import sys
import yaml
import json

PROJECT_HOME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LOCALIZER_HOME = os.path.join(PROJECT_HOME, "flex")
LOCALIZER_BIN_DIR = os.path.join(LOCALIZER_HOME, "_build/default/src")
MANYBUGS_HOME = os.path.join(PROJECT_HOME, "benchmark")

DOCKER_IN_DIR = '/bugfixer'

logging.basicConfig(level=logging.INFO, \
                    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s", \
                    datefmt="%H:%M:%S")


def initialize(args):
    global bug_desc_file
    if args.timestamp:
        timestamp = args.timetamp
    else:
        timestamp = datetime.today().strftime('%Y%m%d-%H:%M:%S')
    out_dir = os.path.join('bugfixer-out', timestamp)
    bug_desc_file = os.path.join(PROJECT_HOME, out_dir, 'bug_desc.json')
    os.makedirs(out_dir, exist_ok=True)


def find_bug_desc(bugzoo, program, bug_id):
    for item in bugzoo:
        if item['name'] == 'manybugs:{}:{}'.format(program, bug_id) \
            or item['name'] == 'corebench:{}:{}'.format(program, bug_id):
            print(item)
            return item

    return None


def preprocess_bug_desc(program, bug_id):
    yml = os.path.join(MANYBUGS_HOME, program, program + '.bugzoo.yml')
    with open(yml) as f:
        bugzoo = yaml.load(f, Loader=yaml.FullLoader)
    bug_desc = find_bug_desc(bugzoo['bugs'], program, bug_id)
    if bug_desc == None:
        print("Unknown bug id")

    with open(bug_desc_file, 'w') as f:
        json.dump(bug_desc, f)


def run_docker(args, program, bug_id):
    cmd = [
        'docker', 'run', '-it', '-v',
        "{}:{}".format(LOCALIZER_BIN_DIR,
                       os.path.join(DOCKER_IN_DIR, 'localizer')), '--mount',
        'type=bind,source={},destination={}'.format(
            bug_desc_file, os.path.join(DOCKER_IN_DIR, 'bug_desc.json'))
    ]
    if args.rm:
        cmd.append('--rm')
    if args.detached:
        cmd.append('-d')
    if args.name:
        cmd.append('--name')
        cmd.append(args.name)
    if args.cpuset_cpus:
        cmd.append('--cpuset-cpus')
        cmd.append(args.cpuset_cpus)
    if args.mem:
        cmd.append('-m')
        cmd.append(args.mem)
    if args.outdir:
        cmd.append('-v')
        cmd.append("{}:{}".format(args.outdir, "/experiment/output"))
    cmd += [
        '2023flip/benchmark:{}-{}'.format(program, bug_id), '/bin/bash'
    ]
    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rm', action='store_true')
    parser.add_argument('-d', action='store_true', dest='detached')
    parser.add_argument('--timestamp', type=str)
    parser.add_argument('--bic', action='store_true')
    parser.add_argument('target', type=str)
    parser.add_argument('--name', type=str)
    parser.add_argument('--outdir', type=str)
    parser.add_argument('--cpuset-cpus', type=str)
    parser.add_argument('--mem', type=str)
    parser.add_argument('--corebench', action='store_true')
    args = parser.parse_args()
    initialize(args)
    program = args.target.split('-')[0]
    bug_id = args.target[len(program) + 1:]
    preprocess_bug_desc(program, bug_id)
    run_docker(args, program, bug_id)


if __name__ == '__main__':
    main()

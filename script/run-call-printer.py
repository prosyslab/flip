#!/usr/bin/env python3

from parse import *
import os
from pathlib import Path
import subprocess
from asyncio.subprocess import DEVNULL
import logging
from time import sleep
from benchmark import benchmark
import yaml


PROJECT_HOME = Path(__file__).resolve().parent.parent
COVERAGE_DIR = PROJECT_HOME / 'flip_output'
YML_DIR = PROJECT_HOME / 'benchmark'

RUN_DOCKER_SCRIPT = PROJECT_HOME / 'script/run-docker.py'

logging.basicConfig(
    level=logging.INFO,
    format=
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S")



def inject_error(project, case, env_signal_list, neg_num):
    def run_cmd_and_check(cmd,
                          *,
                          capture_output=False,
                          text=False,
                          stdout=None,
                          stderr=None):
        process = subprocess.run(cmd,
                                 capture_output=capture_output,
                                 text=text,
                                 stdout=stdout,
                                 stderr=stderr)
        try:
            process.check_returncode()
        except subprocess.CalledProcessError:
            logging.error(f'{project}-{case} failure: {" ".join(cmd)}')
        return process

    print("[*] Injecting error call of : %s-%s" % (project, case))

    # run docker
    cmd = [f'{RUN_DOCKER_SCRIPT}', f'{project}-{case}', '-d', '--rm', '--name', f'{project}-{case}-call']
    cmd = cmd + ['--mem', '40g'] if project == 'python' else cmd
    run_cmd_and_check(cmd,
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)

    docker_id = f'{project}-{case}-call'
    sleep(5)

    run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'touch /experiment/signal_list.txt'])

    run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f'touch /experiment/signal_neg_list.txt'])
    
    for (inject_file, inject_line, is_pos) in env_signal_list:
        if is_pos:
            run_cmd_and_check(
                ['docker', 'exec', docker_id, 'bash', '-c', f'echo {inject_file}:{inject_line} >> /experiment/signal_list.txt'])
        else:
            run_cmd_and_check(
                ['docker', 'exec', docker_id, 'bash', '-c', f'echo {inject_file}:{inject_line} >> /experiment/signal_neg_list.txt'])
    
    run_cmd_and_check(
        ['timeout', '60m', 'docker', 'exec', docker_id, '/bugfixer/localizer/main.exe', '-engine', 'error_coverage', '-fun_level', '.'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    run_cmd_and_check(
        ['docker', 'exec', '-w', '/experiment', docker_id, 'bash', '-c', f'echo "#!/bin/bash\nexport __ENV_SIGNAL=\$1\n./test.sh \$2" > run.sh'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    
    run_cmd_and_check(
        ['docker', 'exec', '-w', '/experiment', docker_id, 'bash', '-c', f'chmod 755 run.sh'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    for i in range(neg_num):
        test_num = i+1
        os.makedirs(COVERAGE_DIR / project / case / 'value' / 'call', exist_ok=True)
        
        run_cmd_and_check(
            ['timeout', '1m', 'docker', 'exec', '-w', '/experiment', docker_id, 'bash', '-c', f'./run.sh DUMMY n{test_num} || true'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        
        run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f"cat /experiment/coverage_data/tmp/*.txt | tr -d '\\000' > /experiment/coverage_data/coverage.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        
        run_cmd_and_check(
            ['docker', 'cp', f'{docker_id}:/experiment/coverage_data/coverage.txt', f"{str(COVERAGE_DIR / project / case / 'value' / 'call' / ('n' + str(test_num) + '.txt'))}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        
        run_cmd_and_check(
            ['docker', 'exec', docker_id, 'bash', '-c', f"rm -f /experiment/coverage_data/tmp/*.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)    
    
    run_cmd_and_check(['docker', 'kill', f'{docker_id}'],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)


def read_signal_list(signal_list_file):
    result = []
    for line in signal_list_file:
        parse_line = parse("{}:{}", line.strip())
        if parse_line != None:
            result.append((os.path.basename(parse_line[0]), parse_line[1]))
    return result


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
    

def main():
    for project in benchmark:
        for case in benchmark[project]:
            
            neg_num, _ = get_test_num(project, case)
            if not os.path.exists(COVERAGE_DIR / project / case / 'branch'):
                continue
            if not os.path.exists(COVERAGE_DIR / project / case / 'result_branch.txt'):
                continue
            if not os.path.exists(COVERAGE_DIR / project / case / 'result_branch_neg.txt'):
                continue
            signal_list_file = open(COVERAGE_DIR / project / case / 'result_branch.txt')
            signal_list = read_signal_list(signal_list_file)
            signal_list_file.close()
            signal_list_neg_file = open(COVERAGE_DIR / project / case / 'result_branch_neg.txt')
            signal_list_neg = read_signal_list(signal_list_neg_file)
            signal_list_neg_file.close()
            env_signal_list = []

            for (inject_file, inject_line) in signal_list:
                env_signal_list.append((inject_file, inject_line, True))
            for (inject_file, inject_line) in signal_list_neg:
                env_signal_list.append((inject_file, inject_line, False))
            inject_error(project, case, env_signal_list, neg_num)


if __name__ == '__main__':
    main()
# Flip

Flip is a framework for fault localization using counterfactual execution

## Requirements

We assume that Flip is executed with the following environment settings.
- Ubuntu 20.04
- Opam 2.1.0 +
- Docker

## Installation

Run the following command to install Flip:
```
$ ./build.sh
```
The above command will install all the dependencies and Flip.

## Running benchmark docker

```
$ ./script/run-docker.py <project>-<case> [--rm]
```

You can run a docker container of benchmark using `run-docker.py`.

If you want, you can use `--rm` option for removing the container when it is exited.

## Collecting branch information

```
# Following commands are running in the docker container.

$ cd /experiment
$ /bugfixer/localizer/main.exe -engine branch_print .
$ ./test.sh [failing test case]  # The name of failing test case should be n1, n2, ...
$ cat /experiment/coverage_data/tmp/*  > /experiment/branch.txt  # This is result file of branch information.
```

The result file contains the following branch statement information.
- branch statement location
- executed branch by failing test case. (True branch / False branch)

## Extract call sequence

It requires two files (`/experiment/signal_list.txt`, `/experiment/signal_neg_list.txt`) that contain a branch list.

- `signal_list.txt` : It contains branches that failing test case executes true branch.

- `signal_neg_list.txt` : It contains branches that failing test case executes false branch.

Note that, please describe all branch candidates in the above files.

```
# Following commands are running in the docker container.

$ cd /experiment
$ /bugfixer/localizer/main.exe -engine error_coverage -fun_level .
$ export __ENV_SIGNAL=<filename>:<line number>  # By this environment variable, you can choose target branch. If you want original call sequence, set dummy environment variable. ex) export __ENV_SIGNAL=DUMMY
$ ./test.sh [failing test case]  # The name of failing test case should be n1, n2, ...
$ cat /experiment/coverage_data/tmp/*  > /experiment/call.txt  # This is result file of call sequence information.
```

## Running passing experiment

It requires two files (`/experiment/signal_list.txt`, `/experiment/signal_neg_list.txt`) that contain a branch.

- `signal_list.txt` : It contains a branch statement information that failing test case executes true branch.

- `signal_neg_list.txt` : It contains a branch statement information that failing test case executes false branch.

Contents should satisfy the following rules.
- Format of branch is `<filename>:<line number>`
- If you choose either one of branch that executes true/false branch, the other file keeps empty.

```
# Following commands are running in the docker container.

$ cd /experiment
$ /bugfixer/localizer/main.exe -engine assume [-mmap] . # -mmap option is for optimized instrumentation.
```

The result file is stored at `/experiment/localizer-out/result.txt`

The format of `result.txt` is the following one.

`<filename>:<line number>   <failing coverage spectrum> <passing coverage spectrum> <score> <number of passed test case>`


## Running failing experiment

It requires two files (`/experiment/signal_list.txt`, `/experiment/signal_neg_list.txt`) that contain a branch list.

- `signal_list.txt` : It contains branches that failing test case executes true branch.

- `signal_neg_list.txt` : It contains branches that failing test case executes false branch.

Note that, please describe all branch candidates in the above files.

```
# Following commands are running in the docker container.

$ cd /experiment
$ /bugfixer/localizer/main.exe -engine error_coverage [-mmap] . 
$ export __ENV_SIGNAL=<filename>:<line number>  # By this environment variable, you can choose target branch.
$ /bugfixer/localizer/main.exe -engine error_run .
```

The result file is stored at `/experiment/localizer-out/result.txt`

The format of `result.txt` is the same as passing experiment one.


## Experiment data

Our experimental data is given in `flip_result`

It contains data with the following structure.
```
├─ main_result
|   ├─ stmt
|   |   ├─ project
|   |   |   ├─ case
|   |   |   |   └─ cov_result.txt
|   |   |   └─  ...
|   |   └─ ...
|   |
|   └─ function
|
├─ oracle
|
├─ passing
|
├─ failing
|
└─ ...
```
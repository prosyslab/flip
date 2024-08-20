## System Requirements

We assume that Flex is executed with the following environment settings.
- Ubuntu 20.04
- Opam 2.1.0 +
- Docker
- python 3.8+
- pip3

## Directory structure

```
├─ README.md                        <- The top-level README (this file)
|
├─ Makefile                         <- Makefile for compiling Flex
|
├─ build.sh                         <- Installation script for Flex
|
├─ benchmark                        <- Benchmark information
|   ├─ <project>
|   |   └─ <project>.bugzoo.yml     <- The information data file for each benchmark project
|   └─ ...
├─ cil                              <- Cil framework for instrumentaion of C programs
|
├─ flex                             <- Our implementation of Flex
|
├─ flex_result                      <- Our experimental data
|
└─ script                           <- Scripts for reproducing our experiments 
```

## Installation

Run the following command to install Flex:
```
$ ./build.sh
```
The above command will install all the dependencies and build Flex.

Note that It would take some time.

<!-- ## Running benchmark docker

```
$ ./script/run-docker.py <project>-<case> [--rm]
```

You can run a docker container of benchmark using `run-docker.py`.

If you need, you can use `--rm` option to remove the container when it is exited. -->


## Reproducing the main experiments (Table 4)

```sh
# If you want to reproduce whole experimental data,
# Statement-level FL results
$ ./script/run-main-stmt.sh
# Function-level FL results
$ ./script/run-main-function.sh

# If you want to reproduce results with given data (./flex_result)
# Statement-level FL results
$ ./script/process-result-main-stmt.py -p <project> -c <case>
# Function-level FL results
$ ./script/process-result-main-function.py -p <project> -c <case>
```

To reproduce our main experimental data, you can execute the above commands.

Note that It would take some time to reproduce whole experimental data.

The format of the results is the following.
```
Project     Case    Rank
<project>   <case>  <rank of fault>
...
```
If you want to reproduce a specific benchmark with given data, you can execute with `-p` and `-c` arguments.

If you cannot execute scripts, please use sudo command.
For example, `sudo ./script/run-main-stmt.sh`

## Reproducing the experiments for approximated oracle with different thresholds (Table 5, 6)

```sh
# If you want to reproduce whole experimental data,
# Approximated oracle with P_100 (Table 5)
$ ./script/run-oracle-pass-100.sh
# Approximated oracle with F_90 (Table 6)
$ ./script/run-oracle-fail-90.sh

# If you want to reproduce results with given data (./flex_result)
# Approximated oracle with P_100 (Table 5)
$ ./script/process-result-oracle-pass-100.py -p <project> -c <case>
# Approximated oracle with F_90 (Table 6)
$ ./script/process-result-oracle-fail-90.py -p <project> -c <case>
```

To reproduce table 5 and 6, you can execute the above commands.

Note that It would take some time to reproduce whole experimental data.

The format of the result is the same as the main results.

## Reproducing the experiments for different aggregation schemes (Table 7)

```sh
# If you want to reproduce whole experimental data,
# Flex with P_max scheme
$ ./script/run-oracle-pass-max.sh
# Flex with F_avg scheme
$ ./script/run-oracle-fail-avg.sh

# If you want to reproduce results with given data (./flex_result)
# Flex with P_max scheme
$ ./script/process-result-aggregation-pass-max.py -p <project> -c <case>
# Flex with F_avg scheme
$ ./script/process-result-aggregation-fail-avg.py -p <project> -c <case>
```

To reproduce table 7, you can execute the above commands.

Note that It would take some time to reproduce whole experimental data.

The format of the result is the same as the main results.

## Reproducing the experiments for impact analysis of P_pass and P_fail (Table 8)
```sh
# If you want to reproduce whole experimental data,
# Flex only with P_pass
$ ./script/run-oracle-pass-only.sh
# Flex only with P_fail
$ ./script/run-oracle-fail-only.sh

# If you want to reproduce results with given data (./flex_result)
# Flex only with P_pass
$ ./script/process-result-pass-only.py -p <project> -c <case>
# Flex only with P_fail
$ ./script/process-result-fail-only.py -p <project> -c <case>
```

To reproduce table 8, you can execute the above commands.

Note that It would take some time to reproduce whole experimental data.

The format of the result is the same as the main results.

## Experiment data

Our experimental data are given in `flex_result`.
It contains data with the following structure.
```
├─ main_result                          <- Results for main experiments (Table 4)
|   ├─ stmt                             <- Results for statement-level FL
|   |   ├─ <project>                      
|   |   |   ├─ <case>
|   |   |   |   └─ cov_result.txt       <- Result file for each benchmark case
|   |   |   └─  ...
|   |   └─ ...
|   └─ function                         <- Results for function-level FL
|       ├─ ...
|
├─ oracle                               <- Results for approximated oracle with different thresholds (Table 6, 7)
|   ├─ passing                          <- Results for approximated oracle with P_100 (Table 6)
|   |
|   └─ failing                          <- Results for approximated oracle with F_90 (Table 7)
|
├─ aggregation                          <- Results for different aggregation schemes (Table 8) 
|   ├─ passing                          <- Results for Flex with P_max scheme
|   |
|   └─ failing                          <- Results for Flex with F_avg scheme
|
├─ passing                              <- Results for impact analysis of P_pass (Table 9)
|
└─ failing                              <- Results for impact analysis of P_fail (Table 9)
```



<!-- ## Collecting branch information

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

The format of `result.txt` is the same as passing experiment one. -->



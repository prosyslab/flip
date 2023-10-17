## System Requirements

We assume that Flip is executed with the following environment settings.
- Ubuntu 20.04
- Docker

## Directory structure

```
├─ README.md                        <- The top-level README (this file)
|
├─ Dockerfile                       <- Dockerfile for Flip
|
├─ patch                            <- Patch files for the compilation
|
├─ flip                             <- Our implementation of Flip
|
├─ flip_result                      <- Our experimental data
|
└─ scripts                          <- Scripts for reproducing our experiments 
```

## Installation

Run the following command to build and run docker image:
```sh
$ docker build -t flip .
$ docker run -it flip /bin/bash
```

## Reproducing the main experiments (Table 5)

```sh
$ ./checkout.py <Chart|Closure|Lang|Math|Time>
$ ./get_method.py <Chart|Closure|Lang|Math|Time>
$ ./run_coverage.py <Chart|Closure|Lang|Math|Time>
$ ./run_branch_printer.py <Chart|Closure|Lang|Math|Time>
$ ./flip_fail.py <Chart|Closure|Lang|Math|Time>
$ ./flip_pass.py <Chart|Closure|Lang|Math|Time>
$ ./run_origin_error_printer.py <Chart|Closure|Lang|Math|Time>
$ ./run_line_matching.py <Chart|Closure|Lang|Math|Time>
$ ./run_fail.py <Chart|Closure|Lang|Math|Time>
$ ./run_final.py <Chart|Closure|Lang|Math|Time>
$ ./process_result.py <Chart|Closure|Lang|Math|Time>
```

To reproduce our main experimental data, you can execute the above commands.

Note that It would take some time to reproduce whole experimental data.

The format of the results is the following.
```
Project     Case    Rank
<project>   <case>  <rank of fault>
...
```

## Experiment data

TBD
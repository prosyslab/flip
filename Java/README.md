## System Requirements

We assume that Flex is executed with the following environment settings.
- Ubuntu 20.04
- Docker

## Directory structure

```
├─ README.md                        <- The top-level README (this file)
|
├─ Dockerfile                       <- Dockerfile for Flex
|
├─ patch                            <- Patch files for the compilation
|
├─ flex                             <- Our implementation of Flex
|
├─ flex_result                      <- Our experimental data
|
└─ scripts                          <- Scripts for reproducing our experiments 
```

## Installation

Run the following command to build and run docker image:
```sh
$ docker build -t flex .
```

Run the following command to build and run docker image for SmartFL:
```sh
$ docker build -t smartfl -f Dockerfile-smartfl .
```

## Reproducing the main experiments of Flex (Table 5)

```sh
$ docker run -it --name flex-experiment flex /bin/bash

# In the docker container,
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

## Reproducing the main experiments of Flex with SmartFL (Table 5)

```sh
$ docker run -it --name flex-smartfl-experiment smartfl /bin/bash

# In your local bash,
$ ./copy_result.py flex-experiment flex-smartfl-experiment <Chart|Closure|Lang|Math|Time>

# In the docker container,
$ python3 s.py testproj <Chart|Closure|Lang|Math|Time>
$ python3 s.py fliptestproj <Chart|Closure|Lang|Math|Time>
```

To reproduce our main experimental data, you can execute the above commands.

Note that It would take some time to reproduce whole experimental data.

The format of the results is the following.

Note that -3 means failure.

```
<project><case> result ranking: <rank of fault>
...
```

## Experiment data

Our experimental data are given in `flip_result`.
It contains data with the following structure.
```
├─ <project>                      
|   ├─ <case>
|   |   └─ result_ochiai.txt       <- Result file with Ochiai for each benchmark case (Table 5)

```
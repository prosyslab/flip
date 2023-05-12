#!/bin/bash

# extract original coverage
./script/run-coverage-extractor.py || true

# extract failing coverage
./script/run-branch-printer.py || true
./script/run-branch-extractor.py || true
./script/run-error-branch-injector.py || true
./script/run-error-call-printer.py || true
./script/run-call-printer.py || true
./script/run-error-branch-multi.py || true

# extract passing coverage
./script/run-signal-extractor.py || true
./script/run-signal-filter.py || true
./script/run-assume-injector.py || true
./script/run-assume-multi-max.py || true

# merge both coverage
./script/run-merge-coverage.py || true

# process result
./script/process-result.py --name result_ochiai_final.txt || true

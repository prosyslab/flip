#!/usr/bin/env bash

set -e

export OPAMYES=1

NCPU="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)"
OCAML_VERSION="4.13.0"
OPAM_SWITCH=program-repair-project-$OCAML_VERSION

opam init --compiler=$OCAML_VERSION -j $NCPU --no-setup

switch_exists=no
for installed_switch in $(opam switch list --short); do
  if [[ "$installed_switch" == "$OPAM_SWITCH" ]]; then
    switch_exists=yes
    break
  fi
done

if [ "$switch_exists" = "no" ]; then
  opam switch create $OPAM_SWITCH $OCAML_VERSION
else
  opam switch $OPAM_SWITCH
fi

eval $(SHELL=bash opam config env --switch=$OPAM_SWITCH)

# build flex
opam pin add cil cil -n
opam install -j $NCPU dune batteries cil ppx_compare ocamlformat ocamlgraph merlin yojson xmlm

make

# install python dependencies
yes | pip3 install -r requirements.txt

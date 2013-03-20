#!/bin/bash

# Exclude external scripts
GREP_EXCLUDE='tools/(pylint_stoq|pep8|reindent).py'
PYFLAKES_BIN='pyflakes'
PEP8_BIN=`dirname $0`/pep8.py
# We probably don't want to fix these for now
# E501 - line too long
# TODO
# E125 - continuation line does not distinguish itself from next logical line
# E711 - comparison to None should be 'if cond is not None:'
# E712 - comparison to True should be 'if cond is True:' or 'if cond:'
PEP8_ARGS="--count --repeat \
           --ignore=E501,E125,E711,E712"


run() {
  FILES=`echo "$1" | egrep ".py$" | grep -Ev "$GREP_EXCLUDE"`

  if [ -z "$FILES" ]; then
    # This is ok. We don't have modified files on tree
    exit 0
  fi

  $PYFLAKES_BIN $FILES &&
  $PEP8_BIN $PEP8_ARGS $FILES

  exit $?

}

_run_all () {
  run "`git ls-files | egrep '.py$'`"
}

_run_modified () {
  run "`git status --porcelain | cut -c 4-`"
}


case "$1" in
  -m | --modified )
    _run_modified;;
  * )
    _run_all;;
esac

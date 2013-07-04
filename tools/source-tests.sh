#!/bin/bash

# Exclude external scripts
GREP_EXCLUDE='tools/(pylint_stoq|pep8|reindent).py'
PYFLAKES_BIN='pyflakes'
PEP8_BIN=`dirname $0`/pep8.py
# We probably don't want to fix these for now
# E125 - continuation line does not distinguish itself from next logical line
PEP8_ARGS="--count --repeat \
           --ignore=E125 --max-line-length=120"


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
  run "`git ls-files '*.py'`"
}

_run_staged() {
  run "`git diff --name-only --diff-filter=ACM --cached`"
}

_run_modified () {
  run "`git diff --name-only --diff-filter=ACM HEAD`"
}


case "$1" in
  -s | --staged )
    _run_staged;;
  -m | --modified )
    _run_modified;;
  * )
    _run_all;;
esac

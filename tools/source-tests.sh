#!/bin/bash

# Exclude external scripts
GREP_EXCLUDE='tools/(pep8|reindent).py'
PYFLAKES_BIN='pyflakes'
PEP8_BIN=`dirname $0`/pep8.py
# We probably don't want to fix these for now
# E261 - inline comment should have two spaces before
# E501 - line too long
# TODO
# E121 - continuation line indentation is not a multiple of four
# E122 - continuation line missing indentation or outdented
# E123 - closing bracket does not match indentation of opening bracket's line
# E124 - closing bracket does not match visual indentation
# E126 - continuation line over-indented for hanging indent
# E125 - continuation line does not distinguish itself from next logical line
# E127 - continuation line over-indented for visual indent
# E128 - continuation line under-indented for visual indent
# E262 - inline comment should start with '# '
# E711 - comparison to None should be 'if cond is not None:'
# E712 - comparison to True should be 'if cond is True:' or 'if cond:'
PEP8_ARGS="--count --repeat \
           --ignore=E261,E501,E121,E122,E123,E124,E125,E126,E127,E128,E262,E711,E712"


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

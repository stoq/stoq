#!/bin/sh

#
# TODO - We want these but they require some work
#
# W0302 - Module too long
# W0622 - Redefined built-in variable
# W0222 - Signature differs from overriden method
#
TODO="W0302,W0621,W0622,W0222"

#
# Disabled - We don't like this ones, turn them off
#
# F0202 - Bug in pylint
# F0203 - Bug in pylint (Unable to resolve gtk.XXXX)
# E0211 - Method has no argument - Interfaces
# E0213 - Method should have "self" as first argument - Interfaces
# E0201 - Access to undefined member - breaks gtk'
# W0201 - Attribute 'loaded_uis' defined outside __init__
# W0212 - Method could be a function (SQLObject from/to_python)
# W0221 - Arguments number differs from overriden method
# W0223 - Method 'add' is abstract in class 'xxx' but is not overriden
# W0232 - Class has no __init__ method
# W0511 - FIXME/TODO/XXX
# E0611 - Pylint is confused about GTK
# W0613 - Unused argument
# W0704 - Except doesn't do anything
#
DISABLE="E0201,E0211,E0213,F0202,F0203,W0201,W0212,W0221,W0223,W0232,W0511,E0611,W0613,W0704"

MSGS="$TODO,$DISABLE"
DIRECTORY="stoqlib"

pylint \
  --dummy-variables=unused,_ \
  --disable-all \
  --include-ids=y \
  --enable-variables=y \
  --enable-exceptions=y \
  --enable-miscellaneous=y \
  --enable-format=y \
  --enable-classes=y \
  --disable-msg=$MSGS \
  --reports=n \
  --enable-metrics=n \
  $DIRECTORY

VERSION=$(shell egrep ^version stoq/__init__.py|cut -d\" -f2)
PACKAGE=stoq

include common/async.mk


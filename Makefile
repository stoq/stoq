VERSION=$(shell BUILD=1 python -c "import stoq; print stoq.version")
PACKAGE=stoq
DEBPACKAGE=python-kiwi
WEBDOC_DIR=/mondo/htdocs/stoq.com.br/doc/devel
SCHEMADIR=/mondo/htdocs/stoq.com.br/devel/schema/

apidocs:
	make -C docs/api/stoq pickle html devhelp
	make -C docs/api/stoqlib pickle html devhelp

schemadocs:
	schemaspy -t pgsql -host anthem -db $(USER) -u $(USER) -s public -o $(SCHEMADIR)

manual:
	mkdir html
	yelp-build html -o html help/pt_BR

web: apidocs
	scp -r apidocs async.com.br:$(WEBDOC_DIR)/stoqlib-tmp
	ssh async.com.br rm -fr $(WEBDOC_DIR)/stoqlib
	ssh async.com.br mv $(WEBDOC_DIR)/stoqlib-tmp $(WEBDOC_DIR)/stoqlib
	scp stoqlib.pickle async.com.br:$(WEBDOC_DIR)/stoqlib

pep8:
	trial stoqlib.test.test_pep8

pyflakes:
	trial stoqlib.test.test_pyflakes

pylint:
	pylint --load-plugins tools/pylint_stoq -E \
	    stoqlib/domain/*.py \
	    stoqlib/domain/payment/*.py

check:
	LC_ALL=C trial stoq stoqlib

include async.mk

.PHONY: TAGS

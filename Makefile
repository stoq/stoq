VERSION=$(shell BUILD=1 python -c "import stoq; print stoq.version")
PACKAGE=stoq
DEBPACKAGE=python-kiwi
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
	scp -r docs/api/stoq/_build/html doc.stoq.com.br:/var/www/stoq.com.br/doc/api/stoq
	scp -r docs/api/stoqlib/_build/html doc.stoq.com.br:/var/www/stoq.com.br/doc/api/stoqlib

pep8:
	trial stoqlib.test.test_pep8

pyflakes:
	trial stoqlib.test.test_pyflakes

pylint:
	pylint --load-plugins tools/pylint_stoq -E \
	    stoqlib/domain/*.py \
	    stoqlib/domain/payment/*.py

check:
	LC_ALL=C LANG=C LANGUAGE=C trial stoq stoqlib

include async.mk

.PHONY: TAGS

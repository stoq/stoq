VERSION=$(shell BUILD=1 python -c "import stoq; print stoq.version")
PACKAGE=stoq
DEBPACKAGE=python-kiwi
SCHEMADIR=/mondo/htdocs/stoq.com.br/devel/schema/
JS_AD="http://pagead2.googlesyndication.com/pagead/show_ads.js"

apidocs:
	make -C docs/api html

manual:
	mkdir -p docs/manual/pt_BR/_build/html
	yelp-build html -o docs/manual/pt_BR/_build/html docs/manual/pt_BR

upload-apidocs:
	tar cfJ - -C docs/api/_build/html . | ssh dragon2 "tar xfJ - -C /var/www/stoq.com.br/doc/api/stoq"

upload-manual:
	tar cfJ - -C docs/manual/pt_BR/_build/html . | ssh dragon.async.com.br "tar xfJ - -C /var/www/stoq.com.br/doc/manual"

schemadocs:
	schemaspy -t pgsql -host anthem -db $(USER) -u $(USER) -s public -o $(SCHEMADIR) \
	    -X '(.*\.te_created_id)|(.*\.te_modified_id)' -norows
	sed -i "s|$(JS_AD)||" $(SCHEMADIR)/*html
	sed -i "s|$(JS_AD)||" $(SCHEMADIR)/tables/*html


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

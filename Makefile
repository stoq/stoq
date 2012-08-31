GVERSION=$(shell BUILD=1 python -c "import stoq; print stoq.short_version")
PACKAGE=stoq
DEBPACKAGE=python-kiwi
SCHEMADIR=/mondo/htdocs/stoq.com.br/devel/schema/
JS_AD="http://pagead2.googlesyndication.com/pagead/show_ads.js"
API_DOC_DIR=dragon2:/var/www/stoq.com.br/doc/api/stoq/$(VERSION)/
MANUAL_DOC_DIR=dragon2:/var/www/stoq.com.br/doc/manual/$(VERSION)/
TEST_MODULES=stoq stoqlib

apidocs:
	make -C docs/api html

manual:
	mkdir -p docs/manual/pt_BR/_build/html
	yelp-build html -o docs/manual/pt_BR/_build/html docs/manual/pt_BR

upload-apidocs:
	cd docs/api/_build/html && rsync -avz --del . $(API_DOC_DIR)

upload-manual:
	cd docs/manual/pt_BR/_build/html && rsync -avz --del . $(MANUAL_DOC_DIR)

schemadocs:
	schemaspy -t pgsql -host anthem -db $(USER) -u $(USER) -s public -o $(SCHEMADIR) \
	    -X '(.*\.te_created_id)|(.*\.te_modified_id)' -norows
	sed -i "s|$(JS_AD)||" $(SCHEMADIR)/*html
	sed -i "s|$(JS_AD)||" $(SCHEMADIR)/tables/*html


pep8:
	nosetests stoqlib/test/test_pep8.py

pyflakes:
	nosetests stoqlib/test/test_pyflakes.py

pylint:
	pylint --load-plugins tools/pylint_stoq -E \
	    stoqlib/domain/*.py \
	    stoqlib/domain/payment/*.py

check:
	rm -f .noseids
	python runtests.py --failed $(TEST_MODULES)

check-failed:
	python runtests.py --failed $(TEST_MODULES)

coverage:
	python runtests.py \
	    --with-xcoverage \
	    --with-xunit \
	    --cover-package=stoq,stoqlib \
	    --cover-erase \
	    --cover-inclusive \
	    $(TEST_MODULES)

external: external/tinycss external/cssselect external/weasyprint
	
external/cssselect:
	wget http://pypi.python.org/packages/source/c/cssselect/cssselect-0.7.1.tar.gz -P external
	tar -xzvf external/cssselect-0.7.1.tar.gz -C external
	ln -s cssselect-0.7.1/cssselect external/cssselect
	
external/tinycss:
	wget http://pypi.python.org/packages/source/t/tinycss/tinycss-0.2.tar.gz -P external
	tar -xzvf external/tinycss-0.2.tar.gz  -C external
	ln -s tinycss-0.2/tinycss external/tinycss
	
external/weasyprint:
	wget http://pypi.python.org/packages/source/W/WeasyPrint/WeasyPrint-0.14.tar.gz -P external
	tar -xzvf external/WeasyPrint-0.14.tar.gz  -C external
	ln -s WeasyPrint-0.14/weasyprint external/weasyprint

include async.mk

.PHONY: TAGS

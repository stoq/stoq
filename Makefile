PACKAGE=stoq
SCHEMADIR=/mondo/htdocs/stoq.com.br/devel/schema/
JS_AD="http://pagead2.googlesyndication.com/pagead/show_ads.js"
API_DOC_DIR=dragon2:/var/www/stoq.com.br/doc/api/stoq/$(VERSION)/
MANUAL_DOC_DIR=dragon2:/var/www/stoq.com.br/doc/manual/$(VERSION)/
TEST_MODULES=stoq stoqlib plugins tests

diff:
	bzr diff -r tag:latest..

log:
	bzr log -r tag:latest..

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
	nosetests tests/test_pep8.py

pyflakes:
	nosetests tests/test_pyflakes.py

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
	tools/validatecoverage

external:
	@cat requirements.txt | \
	    grep -v -e '^#' | \
	    PYTHONPATH=external/ xargs -n 1 \
	    easy_install -x -d external

include async.mk

.PHONY: external TAGS

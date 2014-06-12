PACKAGE=stoq
SCHEMADIR=/mondo/htdocs/stoq.com.br/devel/schema/
JS_AD="http://pagead2.googlesyndication.com/pagead/show_ads.js"
API_DOC_DIR=dragon2:/var/www/stoq.com.br/doc/api/stoq/$(VERSION)/
MANUAL_DOC_DIR=dragon2:/var/www/stoq.com.br/doc/manual/$(VERSION)/
TEST_MODULES=stoq stoqlib plugins tests

# http://stackoverflow.com/questions/2214575/passing-arguments-to-make-run
# List of command that takes test_modules arguments via make
TEST_MODULES_CMD=check check-failed
ifneq (,$(findstring $(firstword $(MAKECMDGOALS)),$(TEST_MODULES_CMD)))
  _TEST_ARGS=$(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(_TEST_ARGS):;@:)
  ifneq (,$(_TEST_ARGS))
    TEST_MODULES=$(_TEST_ARGS)
  endif
else
endif

howto:
	make -C docs/howto html

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

clean:
	@find . -iname '*pyc' -delete

check: clean check-source
	@echo "Running $(TEST_MODULES) unittests"
	@rm -f .noseids
	@python runtests.py --failed $(TEST_MODULES)

check-failed: clean
	python runtests.py --failed $(TEST_MODULES)

coverage: clean check-source-all
	python runtests.py \
	    --with-xcoverage \
	    --with-xunit \
	    --cover-package=stoq,stoqlib,plugins \
	    --cover-erase \
	    --cover-inclusive \
	    $(TEST_MODULES) && \
	tools/validatecoverage coverage.xml && \
	git show|tools/diff-coverage jenkins-test/stoq-$$VERSION/coverage.xml

jenkins: check-source-all
	unset STOQLIB_TEST_QUICK && \
	VERSION=`python -c "from stoq import version; print version"` && \
	rm -fr jenkins-test && \
	python setup.py -q sdist -d jenkins-test && \
	cd jenkins-test && \
	tar xfz stoq-$$VERSION.tar.gz && \
	cd stoq-$$VERSION && \
	python runtests.py \
	    --with-xcoverage \
	    --with-xunit \
	    --cover-package=stoq,stoqlib,plugins \
	    --cover-erase \
	    --cover-inclusive \
	    $(TEST_MODULES) && \
	cd ../.. && \
	tools/validatecoverage jenkins-test/stoq-$$VERSION/coverage.xml && \
	git show|tools/diff-coverage jenkins-test/stoq-$$VERSION/coverage.xml

include utils/utils.mk
.PHONY: howto apidocs manual upload-apidocs upload-manual schemadocs
.PHONY: clean check check-failed coverage jenkins external deb

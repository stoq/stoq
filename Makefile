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


# # We probably don't want to fix these for now
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
# E271 - multiple spaces after keyword
# E502 - the backslash is redundant between brackets
# E711 - comparison to None should be 'if cond is not None:'
# E712 - comparison to True should be 'if cond is True:' or 'if cond:'
pep8:
	@CHANGED=`bzr diff|lsdiff|egrep '.py$$'|xargs -I '{}' sh -c 'test -e {} && echo {}'|xargs -r echo`; \
	if test -n "$$CHANGED"; then \
	    echo "Running PEP8 for $$CHANGED"; \
	    python tools/pep8.py --count --repeat \
	--ignore=E261,E501,E121,E122,E123,E124,E125,E126,E127,E128,E262,E271,E502,E711,E712 $$CHANGED; \
	else \
	    echo "Not running PEP8, no changed files"; \
	fi


pyflakes:
	@CHANGED=`bzr diff|lsdiff|egrep '.py$$'|xargs -I '{}' sh -c 'test -e {} && echo {}'|xargs -r echo`; \
	if test -n "$$CHANGED"; then \
	    echo "Running Pyflakes for $$CHANGED"; \
	    pyflakes $$CHANGED; \
	else \
	    echo "Not running Pyflakes, no changed files"; \
	fi

pylint:
	pylint --load-plugins tools/pylint_stoq -E \
	    stoqlib/domain/*.py \
	    stoqlib/domain/payment/*.py

check: pyflakes pep8
	@echo "Running $(TEST_MODULES) unittests"
	@rm -f .noseids
	@python runtests.py --failed $(TEST_MODULES)

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

jenkins: pep8 pyflakes
	python runtests.py \
	    --with-xunit \
	    $(TEST_MODULES)
	tools/validatecoverage

external:
	@cat requirements.txt | \
	    grep -v -e '^#' | \
	    PYTHONPATH=external/ xargs -n 1 \
	    easy_install -x -d external

include async.mk

.PHONY: external TAGS

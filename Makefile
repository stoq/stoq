TEST_MODULES=stoqlib tests

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

lint-diff-only:
	git diff --name-only --diff-filter=ACM HEAD | grep "*.py" | xargs pyflakes
	git diff --name-only --diff-filter=ACM HEAD | grep "*.py" | xargs pycodestyle

lint:
	pyflakes $(TEST_MODULES)
	pycodestyle $(TEST_MODULES)

check: clean lint-diff-only
	@echo "Running $(TEST_MODULES) unittests"
	@rm -f .noseids
	@python3 runtests.py --exclude-dir=stoqlib/pytests --failed $(TEST_MODULES)
	@pytest

coverage: clean lint
	python3 runtests.py \
	    --with-xcoverage \
	    --with-xunit \
	    --cover-package=stoqlib \
	    --cover-erase \
	    --cover-inclusive \
		--exclude-dir=stoqlib/pytests \
		--exclude-dir=utils \
	    $(TEST_MODULES)
	pytest --cov=stoqlib/ --cov-append
	coverage xml --omit "**/test/*.py,stoqlib/pytests/*"
	utils/validatecoverage.py coverage.xml
	PYTHONIOENCODING=utf8 git show | python3 utils/diff-coverage coverage.xml

test:
	python3 runtests.py $(TEST_MODULES) \
		--exclude-dir=stoqlib/pytests \
		--exclude-dir=utils \
		--with-xunit
	pytest

include utils/utils.mk
.PHONY: dist deb wheel debsource wheel-upload
.PHONY: clean clean-eggs clean-build clean-docs

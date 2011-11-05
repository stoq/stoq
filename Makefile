VERSION=$(shell BUILD=1 python -c "import stoq; print stoq.version")
PACKAGE=stoq
DEBPACKAGE=python-kiwi
WEBDOC_DIR=/mondo/htdocs/stoq.com.br/doc/devel
SCHEMADIR=/mondo/htdocs/stoq.com.br/devel/schema/

stoqlib.pickle:
	pydoctor --project-name="Stoqlib" \
		 --add-package=stoqlib \
		 -o stoqlib.pickle stoqlib

apidocs: stoqlib.pickle
	make -C ../stoqdrivers stoqdrivers.pickle
	pydoctor --project-name="Stoqlib" \
		 --make-html \
		 --extra-system=../stoqdrivers/stoqdrivers.pickle:../stoqdrivers \
		 -p stoqlib.pickle

schemadocs:
	schemaspy -t pgsql -host anthem -db $(USER) -u $(USER) -s public -o $(SCHEMADIR)

web: apidocs
	scp -r apidocs async.com.br:$(WEBDOC_DIR)/stoqlib-tmp
	ssh async.com.br rm -fr $(WEBDOC_DIR)/stoqlib
	ssh async.com.br mv $(WEBDOC_DIR)/stoqlib-tmp $(WEBDOC_DIR)/stoqlib
	scp stoqlib.pickle async.com.br:$(WEBDOC_DIR)/stoqlib

pep8:
	pep8 stoq stoqlib

pyflakes:
	pyflakes stoq stoqlib plugins

check:
	LC_ALL=C trial stoq stoqlib

include async.mk

.PHONY: stoqlib.pickle TAGS

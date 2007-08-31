VERSION=$(shell egrep ^version stoqlib/__init__.py|cut -d\" -f2)
PACKAGE=stoqlib
DEBPACKAGE=python-kiwi
WEBDOC_DIR=/mondo/htdocs/stoq.com.br/doc/devel
SCHEMADIR=/mondo/htdocs/stoq.com.br/devel/schema/

include common/async.mk

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

clean:
	rm -fr $(BUILDDIR)
	rm -f MANIFEST
	rm -fr stoqdrivers.pickle

tests:
	tools/runtests

.PHONY: stoqlib.pickle

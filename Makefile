VERSION=$(shell egrep ^__version__ stoqdrivers/__init__.py|perl -pe 's/[\(\)]/\"/g'|perl -pe "s/, /./g"|cut -d\" -f2)
PACKAGE=stoqdrivers
WEBDOC_DIR=/mondo/htdocs/stoq.com.br/doc/devel
TESTDLDIR=/mondo/htdocs/stoq.com.br/download/test

include common/async.mk

stoqdrivers.pickle:
	pydoctor --project-name="Stoqdrivers" \
		 --add-package=stoqdrivers \
		 -o stoqdrivers.pickle stoqdrivers

apidocs: stoqdrivers.pickle
	pydoctor --project-name="Stoqdrivers" \
		 --make-html \
		 -p stoqdrivers.pickle

web: apidocs
	cp -r apidocs $(WEBDOC_DIR)/stoqdrivers-tmp
	rm -fr $(WEBDOC_DIR)/stoqdrivers
	mv $(WEBDOC_DIR)/stoqdrivers-tmp $(WEBDOC_DIR)/stoqdrivers
	cp stoqdrivers.pickle $(WEBDOC_DIR)/stoqdrivers

clean:
	debclean
	rm -fr $(BUILDDIR)
	rm -f MANIFEST
	rm -fr stoqdrivers.pickle

.PHONY: clean stoqdrivers.pickle

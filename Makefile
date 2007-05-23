VERSION=$(shell egrep ^__version__ stoqdrivers/__init__.py|perl -pe 's/[\(\)]/\"/g'|perl -pe "s/, /./g"|cut -d\" -f2)
BUILDDIR=tmp
PACKAGE=stoqdrivers
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog|egrep ^Version|cut -d\  -f2|cut -d: -f2)
DLDIR=/mondo/htdocs/stoq.com.br/download/ubuntu
TARBALL_DIR=/mondo/htdocs/stoq.com.br/download/sources
WEBDOC_DIR=/mondo/htdocs/stoq.com.br/doc/devel
TESTDLDIR=/mondo/htdocs/stoq.com.br/download/test

stoqdrivers.pickle:
	pydoctor --project-name="Stoqdrivers" \
		 --add-package=stoqdrivers \
		 -o stoqdrivers.pickle stoqdrivers

apidocs: stoqdrivers.pickle
	pydoctor --project-name="Stoqdrivers" \
		 --make-html \
		 -p stoqdrivers.pickle

sdist:
	kiwi-i18n -p $(PACKAGE) -c
	python setup.py -q sdist

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/$(TARBALL)
	cd $(BUILDDIR)/$(PACKAGE)-$(VERSION) && debuild -S
	rm -fr $(BUILDDIR)/$(PACKAGE)-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

rpm: sdist
	mkdir -p build
	rpmbuild --define="_sourcedir `pwd`/dist" \
	         --define="_srcrpmdir `pwd`/dist" \
	         --define="_rpmdir `pwd`/dist" \
	         --define="_builddir `pwd`/build" \
                 -ba stoqdrivers.spec
	mv dist/noarch/* dist
	rm -fr dist/noarch

upload:
	cp dist/$(TARBALL) $(TARBALL_DIR)
	for suffix in "gz" "dsc" "build" "changes" "deb"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(DLDIR); \
	done
	/mondo/local/bin/update-apt-directory $(DLDIR)

web: apidocs
	cp -r apidocs $(WEBDOC_DIR)/stoqdrivers-tmp
	rm -fr $(WEBDOC_DIR)/stoqdrivers
	mv $(WEBDOC_DIR)/stoqdrivers-tmp $(WEBDOC_DIR)/stoqdrivers
	cp stoqdrivers.pickle $(WEBDOC_DIR)/stoqdrivers

tags:
	find -name \*.py|xargs ctags

TAGS:
	find -name \*.py|xargs etags

nightly:
	/mondo/local/bin/build-svn-deb

clean:
	debclean
	rm -fr $(BUILDDIR)
	rm -f MANIFEST
	rm -fr stoqdrivers.pickle

release: clean sdist

release-tag:
	svn cp -m "Tag $(VERSION)" . svn+ssh://async.com.br/pub/stoqdrivers/tags/stoqdrivers-$(VERSION)

test-upload:
	cp dist/$(PACKAGE)*_$(DEBVERSION)*.deb $(TESTDLDIR)/ubuntu
	cp dist/$(PACKAGE)-$(VERSION)*.rpm $(TESTDLDIR)/fedora
	for suffix in "gz" "dsc" "build" "changes"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(TESTDLDIR)/ubuntu; \
	done
	/mondo/local/bin/update-apt-directory $(TESTDLDIR)/ubuntu

.PHONY: sdist deb upload tags TAGS nightly clean release release-deb release-tag upload stoqdrivers.pickle

VERSION=$(shell egrep ^version stoqlib/__init__.py|cut -d\" -f2)
BUILDDIR=tmp
PACKAGE=stoqlib
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog|egrep ^Version|cut -d\  -f2)
DLDIR=/mondo/htdocs/stoq.com.br/download/ubuntu
TARBALL_DIR=/mondo/htdocs/stoq.com.br/download/sources
WEBDOC_DIR=/mondo/htdocs/stoq.com.br/doc/devel
TESTDLDIR=/mondo/htdocs/stoq.com.br/download/test

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
                 -ba stoqlib.spec
	mv dist/noarch/* dist
	rm -fr dist/noarch

web: apidocs
	cp -r apidocs $(WEBDOC_DIR)/stoqlib-tmp
	rm -fr $(WEBDOC_DIR)/stoqlib
	mv $(WEBDOC_DIR)/stoqlib-tmp $(WEBDOC_DIR)/stoqlib
	cp stoqlib.pickle $(WEBDOC_DIR)/stoqlib

upload:
	cp dist/$(TARBALL) $(TARBALL_DIR)
	for suffix in "gz" "dsc" "build" "changes" "deb"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(DLDIR); \
	done
	/mondo/local/bin/update-apt-directory $(DLDIR)

test-upload:
	cp dist/$(PACKAGE)*_$(DEBVERSION)*.deb $(TESTDLDIR)/ubuntu
	cp dist/$(PACKAGE)-$(VERSION)*.rpm $(TESTDLDIR)/fedora
	for suffix in "gz" "dsc" "build" "changes"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(TESTDLDIR)/ubuntu; \
	done
	/mondo/local/bin/update-apt-directory $(TESTDLDIR)/ubuntu

release: clean sdist

release-deb:
	debchange -i "New release"

release-tag:
	svn cp -m "Tag $(VERSION)" . svn+ssh://async.com.br/pub/stoqlib/tags/stoqlib-$(VERSION)

tags:
	find -name \*.py|xargs ctags

TAGS:
	find -name \*.py|xargs etags

nightly:
	/mondo/local/bin/build-svn-deb

clean:
	rm -fr $(BUILDDIR)
	rm -f MANIFEST
	rm -fr stoqdrivers.pickle

tests:
	tools/runtests

.PHONY: sdist deb upload tags TAGS nightly clean stoqlib.pickle

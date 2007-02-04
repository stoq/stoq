VERSION=$(shell egrep ^version stoqlib/__init__.py|cut -d\" -f2)
BUILDDIR=tmp
PACKAGE=stoqlib
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog|egrep ^Version|cut -d\  -f2)
DLDIR=/mondo/htdocs/download.stoq.com.br/ubuntu
TARBALL_DIR=/mondo/htdocs/download.stoq.com.br/sources

sdist:
	kiwi-i18n -p $(PACKAGE) -c
	python setup.py -q sdist

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/$(TARBALL)
	cd $(BUILDDIR)/$(PACKAGE)-$(VERSION) && debuild
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

upload:
	cp dist/$(TARBALL) $(TARBALL_DIR)
	for suffix in "gz" "dsc" "build" "changes" "deb"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(DLDIR); \
	done
	/mondo/local/bin/update-apt-directory $(DLDIR)

tags:
	find -name \*.py|xargs ctags

TAGS:
	find -name \*.py|xargs etags

nightly:
	/mondo/local/bin/build-svn-deb

.PHONY: sdist deb upload tags TAGS nightly

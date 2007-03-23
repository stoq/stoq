VERSION=$(shell egrep ^__version__ stoqdrivers/__init__.py|perl -pe 's/[\(\)]/\"/g'|perl -pe "s/, /./g"|cut -d\" -f2)
BUILDDIR=tmp
PACKAGE=stoqdrivers
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog|egrep ^Version|cut -d\  -f2|cut -d: -f2)
DLDIR=/mondo/htdocs/download.stoq.com.br/ubuntu
TARBALL_DIR=/mondo/htdocs/download.stoq.com.br/sources

sdist: dist/$(TARBALL)
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
                 -ba stoqdrivers.spec
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

clean:
	debclean
	rm -fr $(BUILDDIR)
	rm -f MANIFEST

release: clean sdist release-deb deb

release-deb:
	debchange -v 1:$(VERSION)-1 "New release"

release-tag:
	svn cp -m "Tag $(VERSION)" . svn+ssh://svn.async.com.br/pub/stoqdriver/tags/stoqdrivers-$(VERSION)

.PHONY: sdist deb upload tags TAGS nightly clean release release-deb

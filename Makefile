VERSION=$(shell egrep ^version stoqlib/__init__.py|cut -d\" -f2)
BUILDDIR=tmp
PACKAGE=stoqlib
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog |grep Version|cut -d: -f3)
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

upload:
	cp dist/$(TARBALL) $(TARBALL_DIR)
	for suffix in "gz" "dsc" "build" "changes" "deb"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(DLDIR); \
	done
	cd $(DLDIR) && \
	  rm -f Release Release.gpg && \
	  dpkg-scanpackages . /dev/null > $(DLDIR)/Packages && \
	  dpkg-scansources . /dev/null > $(DLDIR)/Sources && \
	  apt-ftparchive release . > $(DLDIR)/Release && \
	  gpg -abs -o Release.gpg Release

tags:
	find -name \*.py|xargs ctags

TAGS:
	find -name \*.py|xargs etags

.PHONY: sdist deb tags TAGS

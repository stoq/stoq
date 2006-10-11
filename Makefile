VERSION=$(shell egrep ^__version__ stoqdrivers/__init__.py|perl -pe 's/[\(\)]/\"/g'|perl -pe "s/, /./g"|cut -d\" -f2)
BUILDDIR=tmp
PACKAGE=stoqdrivers
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog |grep Version|cut -d: -f3)
DLDIR=/mondo/htdocs/download.stoq.com.br/ubuntu

sdist:
	kiwi-i18n -c
	python setup.py -q sdist

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/$(TARBALL)
	cd $(BUILDDIR)/$(PACKAGE)-$(VERSION); debuild
	rm -fr $(BUILDDIR)/$(PACKAGE)-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

upload:
	for suffix in "gz" "dsc" "build" "changes" "deb"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(DLDIR); \
	done
	cd $(DLDIR) && \
	  dpkg-scanpackages . /dev/null | gzip -c > $(DLDIR)/Packages.gz && \
	  dpkg-scansources . /dev/null | gzip -c > $(DLDIR)/Sources.gz && \
	  rm -f Release Release.gpg && \
	  apt-ftparchive release . > $(DLDIR)/Release && \
	  gpg -abs -o Release.gpg Release

tags:
	find -name \*.py|xargs ctags

TAGS:
	find -name \*.py|xargs etags

.PHONY: sdist deb upload tags TAGS

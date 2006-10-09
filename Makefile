VERSION=$(shell egrep ^__version__ stoqdrivers/__init__.py|perl -pe 's/[\(\)]/\"/g'|perl -pe "s/, /./g"|cut -d\" -f2)
BUILDDIR=tmp
PACKAGE=stoqdrivers
TARBALL=$(PACKAGE)-$(VERSION).tar.gz

sdist:
	kiwi-i18n -c
	python setup.py -q sdist

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/$(TARBALL)
	cd $(BUILDDIR)/$(PACKAGE)-$(VERSION); debuild -uc -us
	rm -fr $(BUILDDIR)/$(PACKAGE)-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

.PHONY: sdist deb

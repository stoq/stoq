VERSION=$(shell egrep ^version stoqlib/__init__.py|cut -d\" -f2)
BUILDDIR=tmp
PACKAGE=stoqlib
TARBALL=$(PACKAGE)-$(VERSION).tar.gz

sdist:
	kiwi-i18n -c
	python setup.py -q sdist

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/$(TARBALL)
	cd $(BUILDDIR)/$(PACKAGE)-$(VERSION) && debuild
	rm -fr $(BUILDDIR)/$(PACKAGE)-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

tags:
	find -name \*.py|xargs ctags

TAGS:
	find -name \*.py|xargs etags

.PHONY: sdist deb tags TAGS

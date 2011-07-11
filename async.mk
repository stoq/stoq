#
# Copyright (C) 2007-2011 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Johan Dahlin                <jdahlin@async.com.br>
#
#
# Common Makefile rules for all Async packages
# 

DEBVERSION=$(shell dpkg-parsechangelog -ldebian/changelog|egrep ^Version|cut -d\  -f2)
TARBALL=$(PACKAGE)-$(VERSION).tar.gz
BUILDDIR=tmp
DOWNLOADWEBDIR=/mondo/htdocs/stoq.com.br/download
TARBALL_DIR=$(DOWNLOADWEBDIR)/sources
TESTDLDIR=$(DOWNLOADWEBDIR)/test
UPDATEAPTDIR=/mondo/local/bin/update-apt-directory

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/$(TARBALL)
	cd $(BUILDDIR) && ln -s ../dist/$(TARBALL) $(PACKAGE)_$(VERSION).orig.tar.gz
	cd $(BUILDDIR)/$(PACKAGE)-$(VERSION) && debuild
	rm -fr $(BUILDDIR)/$(PACKAGE)-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

sdist:
	kiwi-i18n -p $(PACKAGE) -c
	python setup.py -q sdist

rpm: sdist
	rpmbuild -ta --sign dist/$(TARBALL)

upload:
	scp dist/$(TARBALL) async.com.br:$(TARBALL_DIR)
	for suffix in "gz" "dsc" "build" "changes" "deb"; do \
	  scp dist/$(PACKAGE)_$(VERSION)*."$$suffix" async.com.br:$(DOWNLOADWEBDIR)/ubuntu; \
	done
	ssh async.com.br $(UPDATEAPTDIR) $(DOWNLOADWEBDIR)/ubuntu

test-upload:
	cp dist/$(PACKAGE)*_$(DEBVERSION)*.deb $(TESTDLDIR)/ubuntu
	cp dist/$(PACKAGE)-$(VERSION)*.rpm $(TESTDLDIR)/fedora
	for suffix in "gz" "dsc" "build" "changes"; do \
	  cp dist/$(PACKAGE)_$(DEBVERSION)*."$$suffix" $(TESTDLDIR)/ubuntu; \
	done
	$(UPDATEAPTDIR) $(TESTDLDIR)/ubuntu

release: clean sdist

release-deb:
	debchange -v $(VERSION)-1 "New release"

release-tag:
	bzr tag $(VERSION)

ubuntu-package: deb
	cp /mondo/pbuilder/edgy/result/$(PACKAGE)_$(DEBVERSION)_all.deb $(DOWNLOADWEBDIR)/ubuntu
	$(UPDATEAPTDIR) $(DOWNLOADWEBDIR)/ubuntu

tags:
	find -name \*.py|xargs ctags

TAGS:
	find -name \*.py|xargs etags

nightly:
	/mondo/local/bin/build-svn-deb

ChangeLog:
	svn2cl --reparagraph -i --authors common/authors.xml

.PHONY: sdist deb upload tags TAGS nightly ChangeLog

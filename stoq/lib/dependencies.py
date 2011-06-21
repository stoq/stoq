# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Check Stoq dependencies"""

import gettext

_ = gettext.gettext

DATEUTIL_REQUIRED = (1, 4, 1)
GAZPACHO_REQUIRED = (0, 6, 6)
GTK_REQUIRED = (2, 16, 0)
KIWI_REQUIRED = (1, 9, 27)
MAKO_REQUIRED = (0, 2, 5)
PIL_REQUIRED = (1, 1, 5)
PSYCOPG_REQUIRED = (2, 0, 5)
PYGTK_REQUIRED = (2, 16, 0)
REPORTLAB_REQUIRED = (2, 4)
STOQDRIVERS_REQUIRED = (0, 9, 8)
STOQLIB_REQUIRED = (0, 9, 15, 99)
TRML2PDF_REQUIRED = (1, 2)
ZOPE_INTERFACE_REQUIRED = (3, 0)


def _tuple2str(tpl):
    return '.'.join(map(str, tpl))


class DependencyChecker(object):
    def __init__(self):
        self.text_mode = False

    def check(self):
        # First make it possible to open up a graphical interface,
        # so we can display error messages
        self._check_pygtk(PYGTK_REQUIRED, GTK_REQUIRED)
        self._check_kiwi(KIWI_REQUIRED)
        self._check_zope_interface(ZOPE_INTERFACE_REQUIRED)
        self._check_psycopg(PSYCOPG_REQUIRED)
        self._check_gazpacho(GAZPACHO_REQUIRED)
        self._check_pil(PIL_REQUIRED)
        self._check_reportlab(REPORTLAB_REQUIRED, REPORTLAB_REQUIRED)
        self._check_trml2pdf(TRML2PDF_REQUIRED)
        self._check_dateutil(DATEUTIL_REQUIRED)
        self._check_mako(MAKO_REQUIRED)
        self._check_stoqlib(STOQLIB_REQUIRED)
        self._check_stoqdrivers(STOQDRIVERS_REQUIRED)

    def _error(self, title, msg):
        if self.text_mode:
            msg = msg.replace('<b>', '').replace('</b>', '')
            raise SystemExit("ERROR: %s\n\n%s" % (title, msg))

        # Can't use Kiwi here, so create a simple Gtk dialog
        import gtk
        dialog = gtk.MessageDialog(parent=None, flags=0,
                                   type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_OK,
                                   message_format=title)
        dialog.format_secondary_markup(msg)
        dialog.run()
        raise SystemExit

    def _missing(self, project, url=None, version=None):
        msg = _("""<b>%s</b> could not be found on your system.
%s %s or higher is required for Stoq to run.

You can find a recent version of %s on it's homepage at\n%s""") % (
            project, project, _tuple2str(version),
            project, url)

        self._error(_("Missing dependency"), msg)

    def _too_old(self, project, url=None, required=None, found=None):
        msg = _("""<b>%s</b> was found on your system, but it is too old for Stoq to be able to run. %s %s was found, but %s is required.

You can find a recent version of %s on it's homepage at\n%s""") % (
            project, project, found, _tuple2str(required),
            project, url)

        self._error(_("Out-dated dependency"), msg)

    def _incompatible(self, project, url=None, required=None, found=None):
        msg = _("""<b>%s</b> was found on your system, but its version, %s incompatible with Stoq, you need to downgrade to %s for Stoq to work.

You can find an older version of %s on it's homepage at\n%s""") % (
            project, found, _tuple2str(required),
            project, url)

        self._error(_("Incompatible dependency"), msg)

    def _check_pygtk(self, pygtk_version, gtk_version):
        try:
            import gtk
            gtk # stuid pyflakes
        except ImportError:
            try:
                import pygtk
                # This modifies sys.path
                pygtk.require('2.0')
                # Try again now when pygtk is imported
                import gtk
            except ImportError:
                # Can't display a dialog here since gtk is not available
                raise SystemExit("ERROR: PyGTK not found, can't start Stoq")

        if gtk.pygtk_version < pygtk_version:
            self._too_old(project="PyGTK+",
                          url="http://www.pygtk.org/",
                          found=_tuple2str(gtk.pygtk_version),
                          required=pygtk_version)

        if gtk.gtk_version < gtk_version:
            self._too_old(project="Gtk+",
                          url="http://www.gtk.org/",
                          found=_tuple2str(gtk.gtk_version),
                          required=gtk_version)

    def _check_kiwi(self, version):
        # Kiwi
        try:
            import kiwi
        except ImportError:
            self._missing(project="Kiwi",
                          url='http://www.async.com.br/projects/kiwi/',
                          version=version)

        kiwi_version = kiwi.__version__.version
        if kiwi_version < version:
            self._too_old(project="Kiwi",
                          url='http://www.async.com.br/projects/kiwi/',
                          found=_tuple2str(kiwi_version),
                          required=version)

    def _check_zope_interface(self, version):
        try:
            import zope.interface
        except ImportError:
            self._missing(project='ZopeInterface',
                          url='http://www.zope.org/Products/ZopeInterface',
                          version=version)

    def _check_psycopg(self, version):
        try:
            import psycopg2
        except ImportError:
            self._missing(
                project="psycopg - PostgreSQL Database adapter for Python",
                url='http://www.initd.org/projects/psycopg2',
                version=version)

        psycopg2_version = psycopg2.__version__.split(' ', 1)[0]
        if tuple(map(int, psycopg2_version.split('.'))) < version:
            self._too_old(
                project="psycopg - PostgreSQL Database adapter for Python",
                url='http://www.initd.org/projects/psycopg2',
                found=psycopg2_version,
                required=version)

    def _check_stoqdrivers(self, version):
        try:
            import stoqdrivers
        except ImportError:
            self._missing(project="Stoqdrivers",
                          url='http://www.stoq.com.br',
                          version=version)

        stoqdrivers_version = stoqdrivers.__version__
        if stoqdrivers_version < version:
            self._too_old(project="Stoqdrivers",
                          url='http://www.stoq.com.br',
                          found=_tuple2str(stoqdrivers_version),
                          required=version)

    def _check_stoqlib(self, version):
        try:
            import stoqlib
        except ImportError:
            self._missing(project="Stoqlib",
                          url='http://www.stoq.com.br',
                          version=version)

        stoqlib_version = tuple(stoqlib.version.split('.'))
        if stoqlib_version < version:
            self._too_old(project="Stoqlib",
                          url='http://www.stoq.com.br',
                          required=version,
                          found=stoqlib_version)

    def _check_gazpacho(self, version):
        try:
            import gazpacho
        except ImportError:
            self._missing(project="Gazpacho",
                          url='http://gazpacho.sicem.biz/',
                          version=version)

        if map(int, gazpacho.__version__.split('.')) < list(version):
            self._too_old(project="Gazpacho",
                          url='http://gazpacho.sicem.biz/',
                          required=version,
                          found=gazpacho.__version__)

    def _check_pil(self, version):
        try:
            import PIL
            import PIL.Image
        except ImportError:
            self._missing(project='Python Imaging Library (PIL)',
                          url='http://www.pythonware.com/products/pil/',
                          version=version)

        if map(int, PIL.Image.VERSION.split('.')) < list(version):
            self._too_old(project='Python Imaging Library (PIL)',
                          url='http://www.pythonware.com/products/pil/',
                          required=version,
                          found=PIL.Image.VERSION)

    def _check_reportlab(self, version, max_version):
        try:
            import reportlab
        except ImportError:
            self._missing(project="Reportlab",
                          url='http://www.reportlab.org/',
                          version=version)

        rl_version = map(int, reportlab.Version.split('.'))
        if rl_version < list(version):
            self._too_old(project="Reportlab",
                          url='http://www.reportlab.org/',
                          required=version,
                          found=reportlab.Version)

        if rl_version > list(max_version):
            self._incompatible(project="Reportlab",
                               url='http://www.reportlab.org/',
                               required=version,
                               found=reportlab.Version)

    def _check_dateutil(self, version):
        try:
            import dateutil
        except ImportError:
            self._missing(project="Dateutil",
                          url='http://labix.org/python-dateutil/',
                          version=version)

        if map(int, dateutil.__version__.split('.')) < list(version):
            self._too_old(project="Dateutil",
                          url='http://labix.org/python-dateutil/',
                          required=version,
                          found=dateutil.__version__)

    def _check_mako(self, version):
        try:
            import mako
        except ImportError:
            self._missing(project="Mako",
                          url='http://www.makotemplates.org/',
                          version=version)

        if map(int, mako.__version__.split('.')) < list(version):
            self._too_old(project="Mako",
                          url='http://www.makotemplates.org/',
                          required=version,
                          found=mako.__version__)

    def _check_trml2pdf(self, version):
        try:
            import trml2pdf
        except ImportError:
            self._missing(project="trml2pdf",
                          url='pypi.python.org/pypi/trml2pdf/',
                          version=version)

def check_dependencies(text_mode=False):
    dp = DependencyChecker()
    dp.text_mode = text_mode
    dp.check()

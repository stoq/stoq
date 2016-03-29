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

# FIXME: Display all missing dependencies as once in an ObjectList
# FIXME: Integrate with package installer

import os
import platform
import sys

from stoqlib.lib.translation import stoqlib_gettext as _

# When changing something here, remember to update
# the README and the debian control files
DATEUTIL_REQUIRED = (1, 4, 1)
GTK_REQUIRED = (2, 20, 0)
GUDEV_REQUIRED = (147, )
KIWI_REQUIRED = (1, 10)
MAKO_REQUIRED = (0, 2, 5)
PIL_REQUIRED = (1, 1, 5)
PYCAIRO_REQUIRED = (1, 8, 2)
PYPOPPLER_REQUIRED = (0, 12, 1)
PSQL_REQUIRED = (8, 4)
PSYCOPG_REQUIRED = (2, 0, 9)
PYGTK_REQUIRED = (2, 20, 0)
PYGTKWEBKIT_REQUIRED = (1, 1, 7)
PYOBJC_REQUIRED = (2, 3)
PYSERIAL_REQUIRED = (2, 1)
REPORTLAB_REQUIRED = (2, 4)
STORM_REQUIRED = (0, 19)
STOQDRIVERS_REQUIRED = (1, 1)
TWISTED_CORE_REQUIRED = (10, 0)
TWISTED_WEB_REQUIRED = (10, 0)
WEASYPRINT_REQUIRED = (0, 15)
XLWT_REQUIRED = (0, 7, 2)
ZOPE_INTERFACE_REQUIRED = (3, 0)


def _tuple2str(tpl):
    return '.'.join(map(str, tpl))


class DependencyChecker(object):
    def __init__(self):
        self.text_mode = False

    def check_kiwi(self, version):
        self._check_kiwi(version)

    def check(self):
        # First make it possible to open up a graphical interface,
        # so we can display error messages
        self._check_pygtk(PYGTK_REQUIRED, GTK_REQUIRED)
        self._check_kiwi(KIWI_REQUIRED)
        self._check_pycairo(PYCAIRO_REQUIRED)
        if platform.system() != 'Windows':
            self._check_pygtkwebkit(PYGTKWEBKIT_REQUIRED)
        if platform.system() == 'Darwin':
            self._check_pyobjc(PYOBJC_REQUIRED)
        self._check_zope_interface(ZOPE_INTERFACE_REQUIRED)
        self._check_dateutil(DATEUTIL_REQUIRED)
        self._check_twisted_core(TWISTED_CORE_REQUIRED)
        self._check_twisted_web(TWISTED_WEB_REQUIRED)
        self._check_xlwt(XLWT_REQUIRED)

        # Database
        self._check_psql(PSQL_REQUIRED)
        self._check_psycopg(PSYCOPG_REQUIRED)
        self._check_storm(STORM_REQUIRED)

        # Printing
        # FIXME: might be interesting to allow to run Stoq with printing
        #        disabled, would need a global somewhere and refactor
        #        printing imports.
        self._check_pil(PIL_REQUIRED)
        self._check_reportlab(REPORTLAB_REQUIRED)
        self._check_mako(MAKO_REQUIRED)
        if platform.system() not in ['Darwin', 'Windows']:
            self._check_pypoppler(PYPOPPLER_REQUIRED)

        # This needs to be imported *after* poppler. Don't ask me why
        self._check_weasyprint(WEASYPRINT_REQUIRED)

        # ECF
        # FIXME: makes sense to allow Stoq to run with all of these disabled.
        self._check_pyserial(PYSERIAL_REQUIRED)
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
        msg = _("<b>%s</b> could not be found on your system.\n"
                "%s %s or higher is required for Stoq to run.\n\n"
                "You can find a recent version of %s on it's homepage at\n%s") % (
            project, project, _tuple2str(version),
            project, url)

        self._error(_("Missing dependency"), msg)

    def _too_old(self, project, url=None, required=None, found=None):
        msg = _("<b>%s</b> was found on your system, but it is\n"
                "too old for Stoq to be able to run. %s %s was found, "
                "but %s is required.\n\n"
                "You can find a recent version of %s on it's homepage at\n%s") % (
            project, project, found, _tuple2str(required),
            project, url)

        self._error(_("Out-dated dependency"), msg)

    def _incompatible(self, project, url=None, required=None, found=None):
        msg = _("<b>%s</b> was found on your system, but its version,\n"
                "%s incompatible with Stoq, you need to downgrade to %s "
                "for Stoq to work.\n\n"
                "You can find an older version of %s on it's homepage at\n%s") % (
            project, found, _tuple2str(required),
            project, url)

        self._error(_("Incompatible dependency"), msg)

    def _check_pygtk(self, pygtk_version, gtk_version):
        try:
            import gtk
            gtk  # pylint: disable=W0104
        except ImportError:
            try:
                import pygtk
                # This modifies sys.path
                pygtk.require('2.0')
                # Try again now when pygtk is imported
                import gtk
            except ImportError as e:
                # Can't display a dialog here since gtk is not available
                raise SystemExit(
                    "ERROR: PyGTK not found, can't start Stoq: %r" % (e, ))

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
        try:
            import kiwi
        except ImportError:
            self._missing(project="Kiwi",
                          url='http://www.async.com.br/projects/kiwi/',
                          version=version)
            return

        kiwi_version = kiwi.__version__.version
        if kiwi_version < version:
            self._too_old(project="Kiwi",
                          url='http://www.async.com.br/projects/kiwi/',
                          found=_tuple2str(kiwi_version),
                          required=version)

    def _check_pycairo(self, version):
        try:
            import cairo
        except ImportError:
            self._missing(project="pycairo",
                          url='http://www.cairographics.org/pycairo/',
                          version=version)
            return

        if cairo.version_info < version:
            self._too_old(project="pycairo",
                          url='http://www.cairographics.org/pycairo/',
                          found=cairo.version,
                          required=version)

    def _check_pypoppler(self, version):
        try:
            import poppler
        except ImportError:
            self._missing(project="Pypoppler",
                          url='https://launchpad.net/poppler-python',
                          version=version)
            return

        pypoppler_version = poppler.pypoppler_version
        if pypoppler_version < version:
            self._too_old(project="Pypoppler",
                          url='https://launchpad.net/poppler-python',
                          found=_tuple2str(pypoppler_version),
                          required=version)

    def _check_pygtkwebkit(self, version):
        try:
            import webkit
            webkit  # pylint: disable=W0104
        except ImportError:
            self._missing(project='pywebkitgtk',
                          url='http://code.google.com/p/pywebkitgtk/',
                          version=version)

    def _check_zope_interface(self, version):
        try:
            import zope.interface
            zope  # pylint: disable=W0104
        except ImportError:
            self._missing(project='ZopeInterface',
                          url='http://www.zope.org/Products/ZopeInterface',
                          version=version)

    def _check_psql(self, version):
        executable = 'psql'
        paths = os.environ['PATH'].split(os.pathsep)
        if platform.system() == 'Windows':
            executable += '.exe'
            paths.insert(0, os.path.dirname(sys.argv[0]))
        for path in paths:
            full = os.path.join(path, executable)
            if os.path.exists(full):
                break
        else:
            self._missing(project="PostgreSQL",
                          url='http://www.postgresql.org/',
                          version=version)

    def _check_psycopg(self, version):
        try:
            import psycopg2
        except ImportError:
            self._missing(
                project="psycopg2 - PostgreSQL Database adapter for Python",
                url='http://www.initd.org/projects/psycopg2',
                version=version)

        psycopg2_version = psycopg2.__version__.split(' ', 1)[0]
        if tuple(map(int, psycopg2_version.split('.'))) < version:
            self._too_old(
                project="psycopg2 - PostgreSQL Database adapter for Python",
                url='http://www.initd.org/projects/psycopg2',
                found=psycopg2_version,
                required=version)

    def _check_storm(self, version):
        try:
            import storm
        except ImportError:
            self._missing(
                project="storm -  an object-relational mapper",
                url='https://storm.canonical.com',
                version=version)
            return

        if storm.version_info < version:
            self._too_old(
                project="storm -  an object-relational mapper",
                url='https://storm.canonical.com',
                found=storm.version,
                required=version)

    def _check_stoqdrivers(self, version):
        try:
            import stoqdrivers
        except ImportError:
            self._missing(project="Stoqdrivers",
                          url='http://www.stoq.com.br',
                          version=version)
            return

        stoqdrivers_version = stoqdrivers.__version__
        if stoqdrivers_version < version:
            self._too_old(project="Stoqdrivers",
                          url='http://www.stoq.com.br',
                          found=_tuple2str(stoqdrivers_version),
                          required=version)

    def _check_pil(self, version):
        try:
            import PIL
            import PIL.Image
        except ImportError:
            self._missing(project='Python Imaging Library (PIL)',
                          url='http://www.pythonware.com/products/pil/',
                          version=version)
            return

        if list(map(int, PIL.Image.VERSION.split('.'))) < list(version):
            self._too_old(project='Python Imaging Library (PIL)',
                          url='http://www.pythonware.com/products/pil/',
                          required=version,
                          found=PIL.Image.VERSION)

    def _check_reportlab(self, version):
        try:
            import reportlab
        except ImportError:
            self._missing(project="Reportlab",
                          url='http://www.reportlab.org/',
                          version=version)
            return

        rl_version = list(map(int, reportlab.Version.split('.')))
        if rl_version < list(version):
            self._too_old(project="Reportlab",
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
            return

        if (not hasattr(dateutil, "__version__") or
            list(map(int, dateutil.__version__.split('.'))) < list(version)):
            self._too_old(project="Dateutil",
                          url='http://labix.org/python-dateutil/',
                          required=version,
                          found=getattr(dateutil, '__version__', 'unknown'))

    def _check_mako(self, version):
        try:
            import mako
        except ImportError:
            self._missing(project="Mako",
                          url='http://www.makotemplates.org/',
                          version=version)
            return

        if list(map(int, mako.__version__.split('.'))) < list(version):
            self._too_old(project="Mako",
                          url='http://www.makotemplates.org/',
                          required=version,
                          found=mako.__version__)

    def _check_pyserial(self, version):
        try:
            import serial
            serial  # pylint: disable=W0104
        except ImportError:
            self._missing(project='pySerial',
                          url='http://pyserial.sourceforge.net/',
                          version=version)

    def _check_twisted_core(self, version):
        try:
            import twisted
            twisted  # pylint: disable=W0104
        except ImportError:
            self._missing(project='TwistedCore',
                          url='http://twistedmatrix.com/',
                          version=version)
            return

        if list(map(int, twisted.version.base().split('.'))) < list(version):
            self._too_old(project="TwistedCore",
                          url='http://www.twistedmatrix.com/',
                          required=version,
                          found=twisted.version.base())

    def _check_twisted_web(self, version):
        try:
            import twisted.web
        except ImportError:
            self._missing(project='TwistedWeb',
                          url='http://twistedmatrix.com/',
                          version=version)
            return

        if list(map(int, twisted.web.version.base().split('.'))) < list(version):
            self._too_old(project="TwistedWeb",
                          url='http://www.twistedmatrix.com/',
                          required=version,
                          found=twisted.web.version.base())

    def _check_weasyprint(self, version):
        try:
            import weasyprint
            weasyprint  # pylint: disable=W0104
        except ImportError:
            self._missing(project='weasyprint',
                          url='http://weasyprint.org/',
                          version=version)
            return

        if list(map(int, weasyprint.VERSION.split('.'))) < list(version):
            self._too_old(project="weasyprint",
                          url='http://weasyprint.org/',
                          required=version,
                          found=weasyprint.VERSION)

    def _check_xlwt(self, version):
        try:
            import xlwt
            xlwt  # pylint: disable=W0104
        except ImportError:
            self._missing(project='xlwt',
                          url='http://www.python-excel.org/',
                          version=version)
            return

        if list(map(int, xlwt.__VERSION__.split('.'))) < list(version):
            self._too_old(project="xlwt",
                          url='http://www.python-excel.org/',
                          required=version,
                          found=xlwt.__VERSION__)

    def _check_pyobjc(self, version):
        try:
            import objc
            objc  # pylint: disable=W0104
        except ImportError:
            self._missing(project='pyobjc',
                          url='http://pyobjc.sf.net/',
                          version=version)
            return

        if list(map(int, objc.__version__.split('.'))) < list(version):
            self._too_old(project="pyobjc",
                          url='http://pyobjc.sf.net/',
                          required=version,
                          found=objc.__version__)

        try:
            import AppKit
            AppKit  # pylint: disable=W0104
        except ImportError:
            self._missing(project='pyobjc with cocoa support',
                          url='http://pyobjc.sf.net/',
                          version=version)


def check_dependencies(text_mode=False):
    dp = DependencyChecker()
    dp.text_mode = text_mode
    dp.check()

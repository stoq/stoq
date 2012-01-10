# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""CSV Exporter Dialog"""


import csv
import errno

import gtk

from kiwi.python import Settable
from kiwi.ui.objectlist import ObjectList

from stoqlib.database.orm import ORMObject, SelectResults, export_csv, Viewable
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.csvexporter import objectlist2csv
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CSVExporterDialog(BaseEditor):
    gladefile = 'CSVExporterDialog'
    title = _(u'CSV Exporter Dialog')
    size = (400, 150)
    model_type = Settable

    def __init__(self, conn, klass, results=None):
        """A dialog to export data in CSV format.

        @param conn: a database connection
        @param klass:
        @param results:
        """
        if not results or isinstance(results, SelectResults):
            if not issubclass(klass, (ORMObject, Viewable)):
                raise TypeError("The klass argument should be a ORMObject or "
                                "Viewable class or subclass, got '%s' instead" %
                                klass.__class__.__name__)

        model = Settable(klass=klass, results=results)
        self.conn = conn
        BaseEditor.__init__(self, conn, model=model)
        self._setup_widgets()

    #
    # BaseEditor
    #

    def validate_confirm(self):
        filename = self._run_filechooser()
        if filename:
            self._save(filename)
            #self._show(filename)
            return True
        return False

    #
    # Private
    #

    def _setup_widgets(self):
        self.main_dialog.ok_button.set_label(gtk.STOCK_SAVE_AS)

        # (encoding name, python encoding codec)
        # see http://docs.python.org/lib/standard-encodings.html
        encodings = [('Unicode', 'utf8'),
                     ('ASCII', 'ascii'),
                     ('Latin-1', 'latin1')]
        self.encoding.prefill(encodings)

        # (Name, character)
        opts = [(_('Comma'), ','),
                (_('Semicolon'), ';'),
                (_('Tab'), '\t'),
                (_('Colon'), ':')]
        self.separator.prefill(opts)

    def _run_filechooser(self):
        chooser = gtk.FileChooserDialog(_(u"Export CSV..."), None,
                                        gtk.FILE_CHOOSER_ACTION_SAVE,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        chooser.set_do_overwrite_confirmation(True)

        csv_filter = gtk.FileFilter()
        csv_filter.set_name(_(u'CSV Files'))
        csv_filter.add_pattern('*.csv')
        chooser.add_filter(csv_filter)

        response = chooser.run()

        filename = None
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            if not filename.endswith('.csv'):
                filename += '.csv'

        chooser.destroy()
        return filename

    def _get_csv_content(self, encoding):
        if isinstance(self.model.results, ObjectList):
            return objectlist2csv(self.model.results, encoding)

        if self.model.klass and self.model.results is None:
            results = self.model.klass.select(connection=self.conn)
        else:
            results = self.model.results

        content = export_csv(self.model.klass, select=results,
                             connection=self.conn)
        content = content.encode(encoding, 'replace')
        return content.split('\n')

    def _save(self, filename):
        encoding = self.encoding.get_selected()
        sep = self.separator.get_selected()
        try:
            with open(filename, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=sep,
                                    doublequote=True,
                                    quoting=csv.QUOTE_ALL)
                writer.writerows(self._get_csv_content(encoding))
        except IOError as err:
            if err.errno == errno.EACCES:
                warning(_(u"You do not have enought permissions "
                          u"to save on that folder."))
            else:
                raise

    def _show(self, filename):
        import gio
        app_info = gio.app_info_get_default_for_type('text/csv', True)
        gfile = gio.File(path=filename)
        app_info.launch([gfile])

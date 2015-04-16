# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2012 Async Open Source <http://www.async.com.br>
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
"""Spreedsheet Exporter Dialog"""


import gio
import gtk

from stoqlib.api import api

from stoqlib.exporters.xlsexporter import XLSExporter
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SpreadSheetExporter:
    """A dialog to export data to a spreadsheet
    """
    title = _('Exporter to Spreadseet')

    def export(self, object_list, name, filename_prefix, data=None):
        xls = XLSExporter(name)
        xls.add_from_object_list(object_list, data)
        temporary = xls.save(filename_prefix)
        self.export_temporary(temporary)

    def export_temporary(self, temporary):
        mime_type = 'application/vnd.ms-excel'
        app_info = gio.app_info_get_default_for_type(mime_type, False)
        if app_info:
            action = api.user_settings.get('spreadsheet-action')
            if action is None:
                action = 'open'
        else:
            action = 'save'

        if action == 'ask':
            action = self._ask(app_info)

        if action == 'open':
            temporary.close()
            self._open_application(mime_type, temporary.name)
        elif action == 'save':
            self._save(temporary)

    def _ask(self, app_info):
        # FIXME: What if the user presses esc? Esc will return False
        # and open action will be executed. Esc should cancel the action
        if yesno(_("A spreadsheet has been created, "
                   "what do you want to do with it?"),
                 gtk.RESPONSE_NO,
                 _('Save it to disk'),
                 _("Open with %s") % (app_info.get_name())):
            return 'save'
        else:
            return 'open'

    def _open_application(self, mime_type, filename):
        app_info = gio.app_info_get_default_for_type(mime_type, False)
        gfile = gio.File(path=filename)
        app_info.launch([gfile])

    def _save(self, temp):
        chooser = gtk.FileChooserDialog(
            _("Export Spreadsheet..."), None,
            gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        chooser.set_do_overwrite_confirmation(True)

        xls_filter = gtk.FileFilter()
        xls_filter.set_name(_('Excel Files'))
        xls_filter.add_pattern('*.xls')
        chooser.add_filter(xls_filter)

        response = chooser.run()

        filename = None
        if response != gtk.RESPONSE_OK:
            chooser.destroy()
            return

        filename = chooser.get_filename()
        ext = '.xls'

        chooser.destroy()

        if not filename.endswith(ext):
            filename += ext

        # Open in binary format so windows dont replace '\n' with '\r\n'
        open(filename, 'wb').write(temp.read())
        temp.close()

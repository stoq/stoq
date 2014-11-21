# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.gui.dialogs.progressbardialog import ProgressbarDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ImporterDialog(ProgressbarDialog):
    title = _("Importer Dialog")

    log_category = 'stoqlib.importer.create'
    failure_msg = _("Something went wrong while trying to import")

    def __init__(self, format, filename):
        self.start_msg = _("Importing %s...") % (filename, )

        args = ['stoq', 'dbadmin', 'import',
                '-t', format,
                '--import-filename', filename,
                '-v']

        ProgressbarDialog.__init__(self, args=args)

    def process_line(self, line):
        if line.startswith('ITEMS:'):
            value = 0
            self.n_items = int(line.split(':', 1)[1])
            text = _("Importing ...")
        elif line.startswith('IMPORTED-ITEMS:'):
            value = 1
            self.imported_items = int(line.split(':', 1)[1])
            text = _("Imported %d items ...") % (self.imported_items, )
            self.success_msg = _("Done, %d items imported, %d skipped") % (
                self.imported_items,
                self.n_items - self.imported_items)
        elif line.startswith('ITEM:'):
            item = float(line.split(':', 1)[1])
            value = item / self.n_items
            text = _("Importing item %d ...") % (item + 1, )
        else:
            return None, None
        return value, text

# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
##

import csv
import os
import tempfile

from kiwi.python import strip_accents

from stoqlib.lib.parameters import sysparam
from stoqlib.lib.process import Process
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class LabelReport(object):
    title = _("Labels to print")

    def __init__(self, temp, models, skip=0, store=None):
        self.store = store
        self.models = models
        self.skip = skip
        self.temp = temp
        self.rows = []
        for model in models:
            for i in range(model.quantity):
                # XXX: glabels is not working with unicode caracters
                desc = strip_accents(model.description)
                self.rows.append([model.code, model.barcode, desc,
                                  model.price])

    def save(self):
        temp_csv = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        writer = csv.writer(temp_csv, delimiter=',',
                            doublequote=True,
                            quoting=csv.QUOTE_ALL)
        writer.writerows(self.rows)
        temp_csv.close()

        template_file = sysparam.get_string('LABEL_TEMPLATE_PATH')
        if not os.path.exists(template_file):
            raise ValueError(_('Template file for printing labels was not found.'))

        args = ['-f', str(self.skip + 1), '-o', self.filename, '-i',
                temp_csv.name, template_file]

        # FIXME: This is just a quick workaround. There must be a better way to
        # do this.
        # glables3 changed the script name. If the default (glables2) is not
        # available, try the one from glables3
        try:
            p = Process(['glabels-batch'] + args)
        except OSError:
            p = Process(['glabels-3-batch'] + args)
        # FIXME: We should use while so the print dialog can be canceled (see
        # threadutils)
        p.wait()

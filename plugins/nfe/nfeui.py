# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import logging
import os
import time

from stoqlib.domain.events import SaleStatusChangedEvent
from stoqlib.domain.sale import Sale
from stoqlib.lib.osutils import get_application_dir
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import stoqlib_gettext

from nfe.nfegenerator import NFeGenerator

_ = stoqlib_gettext
log = logging.getLogger(__name__)


class NFeUI(object):
    def __init__(self):
        SaleStatusChangedEvent.connect(self._on_SaleStatusChanged)

        pm = PermissionManager.get_permission_manager()
        pm.set('InvoiceLayout', pm.PERM_HIDDEN)
        pm.set('InvoicePrinter', pm.PERM_HIDDEN)

        # since the nfe plugin was enabled, the user must not be able to print
        # the regular fiscal invoice (replaced by the nfe).
        pm.set('app.sales.print_invoice', pm.PERM_HIDDEN)

    #
    # Private
    #

    def _get_save_location(self):
        stoq_dir = get_application_dir()

        # Until we finish the stoqnfe app, we will only export the nfe, so it
        # can be imported by an external application.
        # nfe_dir = os.path.join(stoq_dir, 'generated_nfe')
        nfe_dir = os.path.join(stoq_dir, 'exported_nfe',
                               time.strftime('%Y'), time.strftime('%m'),
                               time.strftime('%d'))

        if not os.path.isdir(nfe_dir):
            os.makedirs(nfe_dir)

        return nfe_dir

    def _can_create_nfe(self, sale):
        # FIXME: certainly, there is more conditions to check before we create
        #        the nfe. Maybe the user should have a chance to fix the
        #        missing information before we create the nfe.
        # return sale.client is not None

        # Since we are only exporting the nfe there is no problem if there is
        # some missing information...

        # ... except the client
        if not sale.client:
            return False

        return True

    def _create_nfe(self, sale, store):
        if self._can_create_nfe(sale):
            generator = NFeGenerator(sale, store)
            generator.generate()
            generator.export_txt(location=self._get_save_location())

    #
    # Events
    #

    def _on_SaleStatusChanged(self, sale, old_status):
        if sale.status == Sale.STATUS_CONFIRMED:
            self._create_nfe(sale, sale.store)

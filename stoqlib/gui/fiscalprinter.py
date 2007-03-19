# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin            <jdahlin@async.com.br>
##

import gtk

from stoqdrivers.exceptions import CouponOpenError, DriverError

from stoqlib.database.database import finish_transaction
from stoqlib.database.runtime import (new_transaction, get_current_station)
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.drivers.fiscalprinter import (
    CouponPrinter, get_fiscal_printer_settings_by_station)
from stoqlib.exceptions import TillError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.tilleditor import TillOpeningEditor
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class FiscalPrinterHelper(CouponPrinter):
    def __init__(self, conn, parent):
        """
        @param conn:
        @param parent: a gtk.Window subclass or None
        """
        self.conn = conn
        self.parent = parent
        station = get_current_station(conn)
        settings = get_fiscal_printer_settings_by_station(conn, station)
        CouponPrinter.__init__(self, settings.get_interface(), settings)

    def open_till(self):
        """
        Opens the till
        """
        if Till.get_current(self.conn) is not None:
            warning("You already have a till operation opened. "
                    "Close the current Till and open another one.")
            return False

        trans = new_transaction()
        try:
            model = run_dialog(TillOpeningEditor, self.parent, trans)
        except TillError, e:
            warning(e)
            model = None

        value = 0
        if model and model.value > 0:
            value = model.value

        retval = True
        while True:
            try:
                CouponPrinter.open_till(self, value)
            except CouponOpenError:
                self.cancel()
                retval = False
            except DriverError:
                response = warning(
                    _(u"It's not possible to emit a read X for the "
                          "configured printer.\nWould you like to ignore "
                          "this error and continue?"),
                    buttons=((_(u"Cancel"), gtk.RESPONSE_CANCEL),
                             (_(u"Ignore"), gtk.RESPONSE_YES),
                             (_(u"Try Again"), gtk.RESPONSE_NONE)))
                if response == gtk.RESPONSE_NONE:
                    continue
                elif response == gtk.RESPONSE_CANCEL:
                    retval = False

            break

        if retval:
            if not finish_transaction(trans, model):
                retval = False

        trans.close()

        return retval

    def close_till(self):
        """
        Closes the till
        @returns: True if the till was closed, otherwise False
        """

        till = Till.get_last_opened(self.conn)
        assert till

        from stoqlib.gui.editors.tilleditor import TillClosingEditor
        trans = new_transaction()
        model = run_dialog(TillClosingEditor, self.parent, trans)

        if not model:
            finish_transaction(trans, model)
            return

        opened_sales = Sale.selectBy(status=Sale.STATUS_OPENED,
                                     connection=trans)
        if opened_sales:
            # A new till object to "store" the sales that weren't
            # confirmed. Note that this new till operation isn't
            # opened yet, but it will be considered when opening a
            # new operation
            branch_station = opened_sales[0].till.station
            new_till = Till(connection=trans,
                            station=branch_station)
            for sale in opened_sales:
                sale.till = new_till

        value = 0
        if model and model.value > 0:
            value = model.value

        retval = True
        while True:
            try:
                CouponPrinter.close_till(self, value)
            except CouponOpenError:
                self.cancel()
                retval = False
            except DriverError:
                response = warning(
                    short=_(u"It's not possible to emit a reduce Z for the "
                            "configured printer.\nWould you like to ignore "
                            "this error and continue?"),
                    buttons=((_(u"Cancel"), gtk.RESPONSE_CANCEL),
                             (_(u"Ignore"), gtk.RESPONSE_YES),
                             (_(u"Try Again"), gtk.RESPONSE_NONE)))
                if response == gtk.RESPONSE_NONE:
                    continue
                elif response == gtk.RESPONSE_CANCEL:
                    retval = False

            break

        if retval:
            # TillClosingEditor closes the till
            if not finish_transaction(trans, model):
                retval = False

        trans.close()

        return retval

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

import sys
import traceback

import gobject
import gtk
from kiwi.argcheck import argcheck
from kiwi.log import Logger
from kiwi.utils import gsignal
from stoqdrivers.exceptions import (DriverError, CouponOpenError,
                                    OutofPaperError, PrinterOfflineError)
from zope.interface import implements

from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.giftcertificate import GiftCertificateItem
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.sellable import ASellableItem
from stoqlib.domain.till import Till
from stoqlib.exceptions import DeviceError, TillError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.tilleditor import TillOpeningEditor, TillClosingEditor
from stoqlib.gui.events import CouponCreatedEvent
from stoqlib.lib.message import warning, yesno
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


log = Logger('stoqlib.fiscalprinter')

class FiscalPrinterHelper:
    def __init__(self, conn, parent):
        """
        @param conn:
        @param parent: a gtk.Window subclass or None
        """
        self.conn = conn
        self._parent = parent

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
            model = run_dialog(TillOpeningEditor, self._parent, trans)
        except TillError, e:
            warning(e)
            model = None

        retval = finish_transaction(trans, model)

        trans.close()

        return retval

    def close_till(self, can_remove_cash):
        """
        Closes the till
        @param can_remove_cash: If True allow the user to remove cash.
        @returns: True if the till was closed, otherwise False
        """

        till = Till.get_last_opened(self.conn)
        assert till

        trans = new_transaction()
        model = run_dialog(TillClosingEditor, self._parent, trans,
                           can_remove_cash=can_remove_cash)

        if not model:
            finish_transaction(trans, model)
            return

        # TillClosingEditor closes the till
        retval = finish_transaction(trans, model)

        trans.close()

        return retval

    def needs_closing(self):
        """
        Checks if the last opened till was closed and asks the
        user if he wants to close it
        @returns: True if the till was open and the user wants to
          close it, otherwise False
        """
        till = Till.get_last_opened(self.conn)
        if till and till.needs_closing():
            if not yesno(_(u"You need to close the till opened %s before "
                           "creating a new order.\n\nClose the till?") %
                         till.opening_date.date(),
                         gtk.RESPONSE_NO, _(u"Not now"), _("Close Till")):
                return True

        return False

    def create_coupon(self, sale):
        """
        @param sale: a L{stoqlib.domain.sale.Sale}
        @returns: a new coupon
        """
        return FiscalCoupon(self._parent, sale)


class FiscalCoupon(gobject.GObject):
    """ This class is used just to allow us cancel an item with base in a
    ASellable object. Currently, services can't be added, and they
    are just ignored -- be aware, if a coupon with only services is
    emitted, it will not be opened in fact, but just ignored.
    """
    implements(IContainer)

    gsignal('open')
    gsignal('identify-customer', object)
    gsignal('add-item', object, retval=int)
    gsignal('remove-item', object)
    gsignal('add-payments', object)
    gsignal('totalize', object)
    gsignal('close', retval=int)
    gsignal('cancel')

    def __init__(self, parent, sale):
        gobject.GObject.__init__(self)

        log.info("Creating a new FiscalCoupon for sale %r" % (sale,))
        CouponCreatedEvent.emit(self)

        self._parent = parent
        self._sale = sale
        self._item_ids = {}

    def emit(self, signal, *args):
        sys.last_value = None
        retval = gobject.GObject.emit(self, signal, *args)
        if sys.last_value is not None:
            traceback.print_exception(sys.last_type, sys.last_value,
                                      sys.last_traceback)
            raise sys.last_value
        return retval

    #
    # IContainer implementation
    #

    @argcheck(ASellableItem)
    def add_item(self, item):
        """
        @param item: A L{ASellableItem} subclass
        @returns: id of the item.:
          0 >= if it was added successfully
          -1 if an error happend
          0 if added but not printed (gift certificates, free deliveries)
        """
        # GiftCertificates are not printed on the fiscal printer
        # See #2985 for more information.
        if isinstance(item, GiftCertificateItem):
            return 0

        if item.price <= 0:
            return 0

        log.info("adding item %r to coupon" % (item,))
        item_id = self.emit('add-item', item)

        ids = self._item_ids.setdefault(item, [])
        ids.append(item_id)
        return item_id

    def get_items(self):
        return self._item_ids.keys()

    @argcheck(ASellableItem)
    def remove_item(self, item):
        if isinstance(item, GiftCertificateItem):
            return
        if item.price <= 0:
            return

        for item_id in self._item_ids.pop(item):
            log.info("removing item %r from coupon" % (item,))
            try:
                self.emit('remove-item', item_id)
            except DriverError:
                return False
        return True

    #
    # Fiscal coupon related functions
    #

    def identify_customer(self, person):
        self.emit('identify-customer', person)

    def open(self):
        while True:
            log.info("opening coupon")
            try:
                self.emit('open')
                break
            except CouponOpenError:
                if not self.cancel():
                    return False
            except OutofPaperError:
                if not yesno(
                    _(u"The fiscal printer has run out of paper.\nAdd more paper "
                      "before continuing."),
                    gtk.RESPONSE_YES, _(u"Resume"), _(u"Confirm later")):
                    return False
                return self.open()
            except PrinterOfflineError:
                if not yesno(
                    (_(u"The fiscal printer is offline, turn it on and try "
                       "again")),
                    gtk.RESPONSE_YES, _(u"Resume"), _(u"Confirm later")):
                    return False
                return self.open()
            except DriverError, e:
                warning(_(u"It is not possible to emit the coupon"),
                        str(e))
                return False
        return True

    def totalize(self):
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True

        try:
            self.emit('totalize', self._sale)
        except DriverError, details:
            warning(_(u"It is not possible to totalize the coupon"),
                    str(details))
            return False
        return True

    def cancel(self):
        try:
            self.emit('cancel')
        except DriverError:
            return False
        return True

    # FIXME: Rename to add_payment_group(group)
    def setup_payments(self):
        """ Add the payments defined in the sale to the coupon. Note that this
        function must be called after all the payments has been created.
        """
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True

        try:
            self.emit('add-payments', self._sale)
        except DeviceError, e:
            warning(_(u"It is not possible to add payments to the coupon"),
                    str(e))
            return False

        return True

    def close(self):
        # XXX: Remove this when bug #2827 is fixed.
        if not self._item_ids:
            return True
        try:
            coupon_id = self.emit('close')
        except DriverError, details:
            warning(_("It's not possible to close the coupon"), str(details))
            return False
        self._sale.coupon_id = coupon_id
        return True

# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##


from stoqlib.api import api
from stoqlib.lib.formatters import get_formatted_price, get_price_as_cardinal
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.report import HTMLReport

_ = stoqlib_gettext


class BasePaymentReceipt(HTMLReport):
    """ Base account receipt
    """
    title = _("Payment receipt")
    template_filename = 'payment_receipt/payment_receipt.html'
    complete_header = True

    def __init__(self, filename, payment, order, date, *args, **kwargs):
        self.payment = payment
        self.order = order
        self.receipt_date = date
        HTMLReport.__init__(self, filename, *args, **kwargs)

    def get_subtitle(self):
        total_value = get_formatted_price(self.payment.value)
        return _('Receipt: %s - Value: %s - Date: %s') % (
            self.payment.identifier,
            get_formatted_price(total_value),
            self.receipt_date.strftime('%x'))

    def get_namespace(self):
        return {'get_price_as_cardinal': get_price_as_cardinal}

    def get_recipient(self):
        """This should be implemented in subclasses"""
        raise NotImplementedError

    def get_drawee(self):
        """This should be implemented in subclasses"""
        raise NotImplementedError


class InPaymentReceipt(BasePaymentReceipt):
    """ Accounts receivable receipt
    """

    def get_drawee(self):
        return self.payment.group.payer

    def get_recipient(self):
        if self.order:
            drawee = self.order.branch.person
        else:
            store = self.payment.store
            drawee = api.get_current_branch(store).person
        return drawee


class OutPaymentReceipt(BasePaymentReceipt):
    """ Accounts payable receipt
    """

    def get_drawee(self):
        if self.order:
            payer = self.order.branch.person
        else:
            store = self.payment.store
            payer = api.get_current_branch(store).person
        return payer

    def get_recipient(self):
        if self.order:
            drawee = self.order.supplier.person
        else:
            drawee = self.payment.group.recipient
        return drawee

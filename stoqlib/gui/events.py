# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2012 Async Open Source <http://www.async.com.br>
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

"""Events used in the domain code
"""

from stoqlib.lib.decorators import public
from stoqlib.lib.event import Event


#
# Application events
#

@public(since="1.5.0")
class StartApplicationEvent(Event):
    """Emitted when an application is activated

    :param appname: the name of the application
    :param app: the app itself
    """


@public(since="1.5.0")
class StopApplicationEvent(Event):
    """Emitted when an application is deactivated

    :param appname: the name of the application
    :param app: the app itself
    """


#
# Dialog events
#

class DialogCreateEvent(Event):
    """Emited when a dialog is instantialized

    :param dialog: an instance of :class:`stoqlib.gui.base.dialogs.BasicDialog`
    """


class EditorSlaveCreateEvent(Event):
    """Emited when a dialog is instantialized

    :param editor: a subclass of
        :class:`stoqlib.gui.editor.baseeditor.BaseEditorSlave`
    :param model: a subclass of :class:`stoqlib.domain.base.Domain`
    :param conn: the connection used in editor and model
    :param visual_mode: a bool defining if the editor was created
        on visual_mode.
    """


#
# CouponCreatedEvent
#

class CouponCreatedEvent(Event):
    pass


#
# Stock Update Events
#


@public(since="1.5.0")
class WizardSellableItemStepEvent(Event):
    """
    This event is emitted when the `items step <stoqlib.gui.wizard...>` of the
    receiving wizard is reached.

    :param wizard_step: The product receiving order dialog.
    """


#
# POS Events
#


@public(since="1.5.0")
class POSConfirmSaleEvent(Event):
    """
    This event is emitted in case a sale is confirmed in the pos app.

    :param sale_items: A list of objects representing the itens added in the
      Sale. This objects are instances of `<stoq.gui.pos.TemporarySaleItem>`
    """


#
# Wizard Events
#


@public(since="1.5.0")
class NewLoanWizardFinishEvent(Event):
    """
    This event is emitted in case a loan is confirmed in the New Loan Wizard.

    :param loan: The `loan <stoqlib.domain.loan.Loan>` object that represents
      the loan created.
    """


@public(since="1.5.0")
class LoanItemSelectionStepEvent(Event):
    """
    This event is emitted in item selection step of the close loan wizard

    :param step: The step itself
    """


@public(since="1.5.0")
class CloseLoanWizardFinishEvent(Event):
    """
    This event is emitted in case a loan is closed in the Close Loan Wizard.

    :param loan: The `loan <stoqlib.domain.loan.Loan>` object that represents
      the loan closed.
    :param created_sale: The `sale <stoqlib.domain.sale.Sale>` object that was
      created for the closed loan
    """


@public(since="1.5.0")
class ReceivingOrderWizardFinishEvent(Event):
    """
    This event is emitted in case an order is received in the Receiving Order
    Wizard.

    :param order: The `receiving order <stoqlib.domain.receiving.ReceivingOrder>`
      object that represents the order received.
    """


@public(since="1.5.0")
class SaleReturnWizardFinishEvent(Event):
    """
    This event is emitted in case a sale is returned in the Sale Return Wizard.

    :param returned_sale: The `returned sale
      <stoqlib.domain.returned_sale.ReturnedSale>` object that represents the
      sale returned.
    """


@public(since="1.5.0")
class SaleTradeWizardFinishEvent(Event):
    """
    This event is emitted in case a new trade is created in the Sale Trade
    Wizard. Note that the trade will only be confirmed after the new sale is
    confirmed in the POS app.

    :param returned_sale: The `returned sale
      <stoqlib.domain.returnedsale.ReturnedSale>` object that represents the
      sale returned.
    """


@public(since="1.5.0")
class StockDecreaseWizardFinishEvent(Event):
    """
    This event is emitted in case the stock is decreased in the Stock Decrease
    Wizard.

    :param stock_decreased: The `stock decrease
      <stoqlib.domain.stockdecrease.StockDecrease>` object that represents the
      stock decrement.
    """


@public(since="1.5.0")
class StockTransferWizardFinishEvent(Event):
    """
    This event is emitted in case a stock transfer is ordered in the Stock
    Transfer Wizard.

    :param transfer_order: The `transfer order
      <stoqlib.domain.transfer.TransferOrder>` object that represents the stock
      transfer.
    """

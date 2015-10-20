# -*- coding: utf-8 -*-

from stoqlib.database.properties import IdCol, IntCol, UnicodeCol, EnumCol
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.migration.domainv4 import Domain

_ = stoqlib_gettext


class Invoice(Domain):
    __storm_table__ = 'invoice'

    TYPE_IN = u'in'
    TYPE_OUT = u'out'

    invoice_number = IntCol()
    operation_nature = UnicodeCol()
    invoice_type = EnumCol(allow_none=False)
    branch_id = IdCol()


class ReturnedSale(Domain):
    __storm_table__ = 'returned_sale'

    status = EnumCol()
    invoice_id = IdCol()
    branch_id = IdCol()
    invoice_number = IntCol()
    operation_nature = _(u"Sale Return")


class Sale(Domain):
    __storm_table__ = 'sale'

    STATUS_INITIAL = u'initial'
    STATUS_QUOTE = u'quote'
    STATUS_ORDERED = u'ordered'

    status = EnumCol()
    invoice_id = IdCol()
    branch_id = IdCol()
    invoice_number = IntCol()
    operation_nature = UnicodeCol()


class StockDecrease(Domain):
    __storm_table__ = 'stock_decrease'

    STATUS_INITIAL = u'initial'

    status = EnumCol()
    invoice_id = IdCol()
    branch_id = IdCol()
    invoice_number = IntCol()
    operation_nature = _(u"Stock decrease")


class TransferOrder(Domain):
    __storm_table__ = 'transfer_order'

    STATUS_PENDING = u'pending'

    status = EnumCol()
    invoice_id = IdCol()
    source_branch_id = IdCol()
    invoice_number = IntCol()
    operation_nature = _(u"Transfer")


def apply_patch(store):
    existing_invoices = set((invoice.invoice_number, invoice.branch_id)
                            for invoice in store.find(Invoice))

    # Sale
    for sale in store.find(Sale, invoice_id=None):
        invoice = Invoice(
            store=store,
            invoice_type=Invoice.TYPE_OUT,
            operation_nature=sale.operation_nature,
        )
        sale.invoice_id = invoice.id

        inv_key = (sale.invoice_number, sale.branch_id)
        if (inv_key not in existing_invoices and
                sale.status not in [Sale.STATUS_INITIAL,
                                    Sale.STATUS_QUOTE,
                                    Sale.STATUS_ORDERED]):
            invoice.invoice_number = sale.invoice_number
            invoice.branch_id = sale.branch_id

            existing_invoices.add(inv_key)

    # ReturnedSale
    for returned_sale in store.find(ReturnedSale, invoice_id=None):
        invoice = Invoice(
            store=store,
            invoice_type=Invoice.TYPE_IN,
            operation_nature=returned_sale.operation_nature,
        )
        returned_sale.invoice_id = invoice.id

        inv_key = (returned_sale.invoice_number, returned_sale.branch_id)
        if inv_key not in existing_invoices:
            invoice.invoice_number = returned_sale.invoice_number
            invoice.branch_id = returned_sale.branch_id

            existing_invoices.add(inv_key)

    # StockDecrease
    for stock_decrease in store.find(StockDecrease, invoice_id=None):
        invoice = Invoice(
            store=store,
            invoice_type=Invoice.TYPE_OUT,
            operation_nature=stock_decrease.operation_nature,
        )
        stock_decrease.invoice_id = invoice.id

        inv_key = (stock_decrease.invoice_number, stock_decrease.branch_id)
        if (inv_key not in existing_invoices and
                stock_decrease.status != StockDecrease.STATUS_INITIAL):
            invoice.invoice_number = stock_decrease.invoice_number
            invoice.branch_id = stock_decrease.branch_id

            existing_invoices.add(inv_key)

    # TransferOrder
    for transfer in store.find(TransferOrder, invoice_id=None):
        invoice = Invoice(
            store=store,
            invoice_type=Invoice.TYPE_OUT,
            operation_nature=transfer.operation_nature,
        )
        transfer.invoice_id = invoice.id

        inv_key = (transfer.invoice_number, transfer.source_branch_id)
        if (inv_key not in existing_invoices and
                transfer.status != TransferOrder.STATUS_PENDING):
            invoice.invoice_number = transfer.invoice_number
            invoice.branch_id = transfer.source_branch_id

            existing_invoices.add(inv_key)

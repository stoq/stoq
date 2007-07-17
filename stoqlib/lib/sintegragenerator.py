# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):       Johan Dahlin            <jdahlin@async.com.br>
##                  Fabio Morbec            <fabio@async.com.br>
##

"""Generate a Sintegra archive from the Stoqlib domain classes"""

from kiwi.db.query import DateIntervalQueryState
from kiwi.db.sqlobj import SQLObjectQueryExecuter

from stoqlib.database.runtime import get_connection, get_current_branch

from stoqlib.domain.devices import FiscalDayHistory
from stoqlib.domain.interfaces import ICompany
from stoqlib.domain.person import (_PersonAdaptToCompany,
                                   PersonAdaptToIndividual)
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.lib.sintegra import SintegraFile


class StoqlibSintegraGenerator(object):
    """
    This class is responsible for generating a sintegra file
    from the Stoq domain classes.
    """
    def __init__(self, conn, start, end):
        self.conn = conn
        self.start = start
        self.end = end
        self.sintegra = SintegraFile()

        self._add_header()
        self.sintegra.close()

    def write(self, filename):
        self.sintegra.write(filename)

    def _date_query(self, search_table, column):
        sfilter = object()
        executer = SQLObjectQueryExecuter(self.conn)
        executer.set_filter_columns(sfilter, [column])
        executer.set_table(search_table)
        state = DateIntervalQueryState(filter=sfilter,
                                       start=self.start,
                                       end=self.end)
        return executer.search([state])

    def _add_header(self):
        branch = get_current_branch(self.conn)
        company = ICompany(branch.person)
        address = branch.person.get_main_address()

        state_registry = company.get_state_registry_number()
        state = address.get_state()

        self.sintegra.add_header(company.get_cnpj_number(),
                                 str(state_registry) or 'ISENTO',
                                 company.fancy_name,
                                 address.get_city(),
                                 state,
                                 branch.person.get_fax_number_number(),
                                 self.start,
                                 self.end)
        self.sintegra.add_complement_header(address.street, address.number,
                                            address.complement,
                                            address.district,
                                            address.get_postal_code_number(),
                                            company.fancy_name,
                                            branch.person.get_phone_number_number())

        self._add_fiscal_coupons()
        self._add_receiving_orders(state_registry, state)

    def _add_fiscal_coupons(self):
        for item in self._date_query(FiscalDayHistory, 'emission_date'):
            self.sintegra.add_fiscal_coupon(
                item.emission_date, item.serial, item.serial_id,
                item.coupon_start, item.coupon_end,
                item.cro, item.crz, item.period_total, item.total)
            for tax in item.taxes:
                self.sintegra.add_fiscal_tax(item.emission_date, item.serial,
                                             tax.code, tax.value)

    def _get_cnpj_or_cpf(self, receiving_order):
        person = receiving_order.supplier.person
        company = person.has_individual_or_company_facets()
        if isinstance(company, _PersonAdaptToCompany):
            cnpj = company.get_cnpj_number()
        elif isinstance(company, PersonAdaptToIndividual):
            cnpj = company.get_cpf_number()
        else:
            raise AssertionError
        return cnpj

    def _add_receiving_orders(self, state_registry, state):
        receiving_orders = self._date_query(ReceivingOrder, 'receival_date')

        # 1) Add orders (registry 50)
        for receiving_order in receiving_orders:
            self._add_receiving_order(state_registry, state, receiving_order)

        # 2) Add order items (registry 54) and collect sellables
        sellables = set()
        for receiving_order in receiving_orders:
            self._add_receiving_order_items(receiving_order, sellables)
            self._add_receiving_order_item_special(receiving_order, 991, receiving_order.freight_total)
            self._add_receiving_order_item_special(receiving_order, 992, receiving_order.secure_value)
            self._add_receiving_order_item_special(receiving_order, 999, receiving_order.expense_value)

        # 2) Add sellables (registry 75)
        for sellable in sellables:
            self._add_sellable(sellable)

    def _add_receiving_order(self, state_registry, state, receiving_order):
        cnpj = self._get_cnpj_or_cpf(receiving_order)

        # Sintegra register 50 requires us to separate the receiving orders per
        # class of sales tax (aliquota), so first we have to check all the 
        # items in our order and split them out per tax code
        sellable_per_constant = {}
        for item in receiving_order.get_items():
            # Tax is stored as a number between 0 and 100
            # We're going to use it as a percentage value, so
            # divide by 100, Perhaps this code should move to a method in
            # the SellableTaxConstant class
            tax_value = item.sellable.tax_constant.tax_value
            if tax_value:
                tax_value /= 100
            else:
                tax_value = 0
            tax_values = sellable_per_constant.setdefault(tax_value, [])
            tax_values.append(item)

        # There's no way to specify a global discount for the whole order,
        # instead we have to put the discount proportionally over all
        # tax constants in the order, calculate the percentage here
        items_total = receiving_order.get_products_total()
        discount_percental = 1 - (receiving_order.discount_value / items_total)
        extra_percental = 1 + ((receiving_order.freight_total +
                                receiving_order.secure_value +
                                receiving_order.expense_value) / items_total)

        for tax_value, items in sellable_per_constant.items():
            item_total = sum(item.get_total() for item in items)
            item_total *= extra_percental
            item_total *= discount_percental
            if tax_value:
                base_total = item_total
            else:
                # Lack of a tax_value means lack of a ICMS base to calculate
                # taxes from
                base_total = 0

            self.sintegra.add_receiving_order(
                cnpj,
                state_registry,
                receiving_order.receival_date,
                state,
                1,
                '1  ',
                receiving_order.invoice_number,
                receiving_order.get_cfop_code(),
                'T',
                item_total,
                base_total,
                item_total * tax_value,
                0,
                (receiving_order.expense_value +
                 receiving_order.secure_value),
                tax_value * 100,
                'N')

    def _add_receiving_order_items(self, receiving_order, sellables):
        cnpj = self._get_cnpj_or_cpf(receiving_order)
        items = receiving_order.get_items()
        no_items = items.count()
        items_total = receiving_order.get_products_total()
        discount_percental = 1 - (receiving_order.discount_value / items_total)
        extra_percental = 1 + ((receiving_order.freight_total +
                                receiving_order.secure_value +
                                receiving_order.expense_value) / items_total)

        for i, item in enumerate(items):
            tax_value = item.sellable.tax_constant.tax_value or 0
            item_total = item.get_total()
            if tax_value:
                base_total = item_total
                base_total *= extra_percental
                base_total *= discount_percental
            else:
                base_total = 0
            self.sintegra.add_receiving_order_item(
                cnpj, 1, '1  ',
                receiving_order.invoice_number,
                receiving_order.get_cfop_code(),
                '000',
                i+1,
                item.sellable.id,
                item.quantity,
                item_total,
                item_total - (item_total * discount_percental),
                base_total,
                0,
                receiving_order.ipi_total / no_items,
                tax_value)
            sellables.add(item.sellable)

    def _add_receiving_order_item_special(self, receiving_order, code, value):
        if not value:
            return
        cnpj = self._get_cnpj_or_cpf(receiving_order)
        self.sintegra.add_receiving_order_item(cnpj, 1, '1  ',
                                               receiving_order.invoice_number,
                                               receiving_order.get_cfop_code(),
                                               None, 
                                               code,
                                               None,
                                               0,
                                               0,
                                               value,
                                               0, 0, 0, 0)

    def _add_sellable(self, sellable):
        unit = 'un'
        if sellable.unit:
            unit = str(sellable.unit.description or 'un')
        self.sintegra.add_product(self.start,
                                  self.start, sellable.id,
                                  0, sellable.get_description(),
                                  unit,
                                  0, 0, 0, 0)


def generate(filename, start, end):
    """
    Generate a sintegra file for all changes in the system
    between start and end dates. Start and end are normally
    the first and last day of a month

    @param filename: filename to save the sintegra file
    @param start: start date
    @type start: datetime.date
    @param end: end date
    @type start: datetime.date
    """

    generator = StoqlibSintegraGenerator(get_connection(), start, end)
    fp = open(filename, 'w')
    for register in generator.sintegra.get_registers():
        fp.write(register.get_string().replace('2007', '2006'))
    fp.close()

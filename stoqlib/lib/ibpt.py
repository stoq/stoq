# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""
Identify and apply to a product, the defined taxes by
IBPT - Instituto Brasileiro de Planejamento Tributário (Brazilian Institute
of Tributary Planning)
According to Law 12,741 of 12/08/2012 - Taxes in Coupon.
"""
from collections import namedtuple

from kiwi.environ import environ

import csv
from decimal import Decimal

from stoqlib.database.runtime import get_current_branch, new_store

taxes_data = {}
TaxInfo = namedtuple('TaxInfo', 'nacionalfederal, importadosfederal, estadual,'
                     'fonte, chave')


def load_taxes_csv():
    """ Load the fields of IBPT table.

    - Fields:
        - ncm: Nomenclatura Comum do Sul.
        - ex: Exceção fiscal da NCM.
        - tipo: Código que pertence a uma NCM.
        - descricao: Nome do produto.
        - nacionalfederal: Carga tributária para os produtos nacionais.
        - importadosfederal: Carga tributária para os produtos importados.
        - estadual: Carga tributária estadual
        - municipal: Carga tributária municipal
        - vigenciainicio: Data de início da vigência desta alíquota.
        - vigenciafim: Data de fim da vigência desta alíquota.
        - chave: Chave que associa a Tabela IBPT baixada com a empresa.
        - versao: Versão das alíquotas usadas para cálculo.
        - Fonte: Fonte
    """

    # Avoid load taxes more than once.
    if taxes_data:
        return

    store = new_store()
    branch = get_current_branch(store)
    address = branch.person.get_main_address()
    state = address.city_location.state

    # Change the version according to the updates of IBPT tables.
    version = '16.1.A'
    filename = environ.get_resource_filename('stoq', 'csv', 'ibpt_tables',
                                             'TabelaIBPTax%s%s.csv'
                                             % (state, version))
    csv_file = (csv.reader(open(filename, "r"), delimiter=';'))

    for (ncm, ex, tipo, descricao, nacionalfederal, importadosfederal,
         estadual, municipal, vigenciainicio, vigenciafim, chave,
         versao, fonte) in csv_file:
        # Ignore service codes (NBS - Nomenclatura Brasileira de Serviços)
        if tipo == '1':
            continue
        tax_dict = taxes_data.setdefault(ncm, {})
        tax_dict[ex] = TaxInfo(nacionalfederal, importadosfederal, estadual,
                               fonte, chave)


class IBPTGenerator(object):
    def __init__(self, items):
        load_taxes_csv()
        self.items = items

    def _format_ex(self, ex_tipi):
        if not ex_tipi:
            return ''
        ex = int(ex_tipi)
        return str(ex).zfill(2)

    def _load_tax_values(self, item):
        assert item
        sellable = item.sellable
        product = sellable.product
        if not product:
            return None
        ncm = product.ncm or ''
        ex_tipi = self._format_ex(product.ex_tipi)

        options = taxes_data.get(ncm, {})
        n_options = len(options)
        if n_options == 0:
            tax_values = TaxInfo('0', '0', '0', '', '0')
        elif n_options == 1:
            tax_values = options['']
        else:
            tax_values = options.get(ex_tipi) or options['']
        return tax_values

    def _calculate_federal_tax(self, item, tax_values):
        """ Calculate the IBPT tax for a give item.

        :param item: a |saleitem|
        :returns: the IBPT tax or ``0`` if it does not exist
        :rtype: decimal
        """
        if tax_values is None:
            return Decimal("0")
        sellable = item.sellable
        product = sellable.product

        if product.icms_template:
            origin = product.icms_template.orig
        else:
            # If the product does not have any fiscal information, defaults to
            # national origin
            origin = 0

        # Values (0, 3, 4, 5, 8) represent the taxes codes of brazilian origin.
        if origin in [0, 3, 4, 5, 8]:
            federal_tax = Decimal(tax_values.nacionalfederal) / 100
        # Different codes, represent taxes of international origin.
        else:
            federal_tax = Decimal(tax_values.importadosfederal) / 100
        total_item = item.price * item.quantity
        return total_item * federal_tax

    def _calculate_state_tax(self, item, tax_values):
        if tax_values is None:
            return Decimal("0")
        total_item = item.price * item.quantity
        state_tax = Decimal(tax_values.estadual) / 100
        return total_item * state_tax

    def get_ibpt_message(self):
        federal_tax = state_tax = 0
        for item in self.items:
            tax_values = self._load_tax_values(item)
            federal_tax += self._calculate_federal_tax(item, tax_values)
            state_tax += self._calculate_state_tax(item, tax_values)
        if tax_values:
            source = tax_values.fonte
            key = tax_values.chave
        else:
            source = ""
            key = "0"

        federal_msg = "%0.2f Federal" % federal_tax
        state_msg = "%0.2f Estadual" % state_tax

        final_msg = ("Trib aprox R$: {federal} e {state}\n"
                     "Fonte: {source} {key} ")
        return final_msg.format(federal=federal_msg, state=state_msg,
                                source=source, key=key)


def generate_ibpt_message(items):
    generator = IBPTGenerator(items)
    return generator.get_ibpt_message()

# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
""" Slaves for books """

import datetime
from dateutil.relativedelta import relativedelta

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.domain.taxes import (SaleItemIcms, ProductIcmsTemplate,
                                  SaleItemIpi, ProductIpiTemplate)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditorSlave


_ = stoqlib_gettext


class BaseTaxSlave(BaseEditorSlave):
    combo_widgets = ()
    percentage_widgets = ()
    value_widgets = ()

    hide_widgets = ()

    tooltips = {}

    field_options = {}

    def __init__(self, *args, **kargs):
        self.proxy = None
        BaseEditorSlave.__init__(self, *args, **kargs)

    def _setup_widgets(self):
        for name, options in self.field_options.items():
            widget = getattr(self, name)
            widget.prefill(options)
            widget.set_size_request(220, -1)

        for name in self.percentage_widgets:
            widget = getattr(self, name)
            widget.set_digits(2)
            widget.set_adjustment(
                gtk.Adjustment(lower=0, upper=100, step_incr=1))

        for w in self.hide_widgets:
            getattr(self, w).hide()
            getattr(self, w + '_label').hide()

        for name, tooltip in self.tooltips.items():
            widget = getattr(self, name)
            if isinstance(widget, gtk.Entry):
                widget.set_property('primary-icon-stock', gtk.STOCK_INFO)
                widget.set_property('primary-icon-tooltip-text', tooltip)
                widget.set_property('primary-icon-sensitive', True)
                widget.set_property('primary-icon-activatable', False)

        self.setup_callbacks()

    def setup_callbacks(self):
        """Implement this in a child when necessary
        """
        pass

    def set_valid_widgets(self, valid_widgets):
        for widget in self.all_widgets:
            if widget in valid_widgets:
                getattr(self, widget).set_sensitive(True)
                lbl = getattr(self, widget + '_label', None)
                if lbl:
                    lbl.set_sensitive(True)
            else:
                getattr(self, widget).set_sensitive(False)
                lbl = getattr(self, widget + '_label', None)
                if lbl:
                    lbl.set_sensitive(True)


#
#   ICMS
#


class BaseICMSSlave(BaseTaxSlave):
    gladefile = 'TaxICMSSlave'

    combo_widgets = ['cst', 'orig', 'mod_bc', 'mod_bc_st', 'csosn']
    percentage_widgets = ['p_icms', 'p_mva_st', 'p_red_bc_st', 'p_icms_st',
                          'p_red_bc', 'p_cred_sn']
    value_widgets = ['v_bc', 'v_icms', 'v_bc_st', 'v_icms_st',
                     'v_cred_icms_sn', 'v_bc_st_ret', 'v_icms_st_ret']
    bool_widgets = ['bc_include_ipi', 'bc_st_include_ipi']
    date_widgets = ['p_cred_sn_valid_until']
    all_widgets = (combo_widgets + percentage_widgets + value_widgets +
                   bool_widgets + date_widgets)

    simples_widgets = ['orig', 'csosn', 'mod_bc_st', 'p_mva_st', 'p_red_bc_st',
              'p_icms_st', 'v_bc_st', 'v_icms_st', 'p_cred_sn',
              'p_cred_sn_valid_until' 'v_cred_icms_sn', 'v_bc_st_ret',
              'v_icms_st_ret'],

    normal_widgets = ['orig', 'cst', 'mod_bc_st', 'p_mva_st', 'p_red_bc_st',
             'p_icms_st', 'v_bc_st', 'v_icms_st', 'bc_st_include_ipi',
             'mod_bc', 'p_icms', 'v_bc', 'v_icms', 'bc_include_ipi',
             'bc_st_include_ipi']

    tooltips = {
        'p_icms': u'Aliquota do imposto',
        'p_mva_st': u'Percentual da margem de valor adicionado do ICMS ST',
        'p_red_bc_st': u'Percentual da Redução de Base de Cálculo do ICMS ST'
    }

    field_options = {
        'cst': (
            (None, None),
            (u'00 - Tributada Integralmente', 0),
            (u'10 - Tributada e com cobrança de ICMS por subst. trib.', 10),
            (u'20 - Com redução de BC', 20),
            (u'30 - Isenta ou não trib. e com cobrança de ICMS por subst. trib.', 30),
            (u'40 - Isenta', 40),
            (u'41 - Não tributada', 41),
            (u'50 - Suspensão', 50),
            (u'51 - Deferimento', 51),
            (u'60 - ICMS cobrado anteriormente por subst. trib.', 60),
            (u'70 - Com redução da BC cobrança do ICMS por subst. trib.', 70),
            (u'90 - Outros', 90),
        ),

        'csosn': (
            (None, None),
            (u'101 - Tributada com permissão de crédito', 101),
            (u'102 - Tributada sem permissão de crédito', 102),
            (u'103 - Isenção do ICMS para faixa de receita bruta', 103),
            (u'201 - Tributada com permissão de crédito e com cobrança do ICMS por ST', 201),
            (u'202 - Tributada sem permissão de crédito e com cobrança do ICMS por ST', 202),
            (u'203 - Isenção do ICMS para faixa de receita bruta e com cobrança do ICMS por ST', 203),
            (u'300 - Imune', 300),
            (u'400 - Não tributada', 400),
            (u'500 - ICMS cobrado anteriormente por ST ou por antecipação', 500),
        ),

        'orig': (
            (None, None),
            (u'0 - Nacional', 0),
            (u'1 - Estrangeira - importação direta', 1),
            (u'2 - Estrangeira - adquirida no mercado interno', 2),
        ),
        'mod_bc': (
            (None, None),
            (u'0 - Margem do valor agregado (%)', 0),
            (u'1 - Pauta (Valor)', 1),
            (u'2 - Preço tabelado máximo (valor)', 2),
            (u'3 - Valor da operação', 3),
        ),
        'mod_bc_st': (
            (None, None),
            (u'0 - Preço tabelado ou máximo sugerido', 0),
            (u'1 - Lista negativa (valor)', 1),
            (u'2 - Lista positiva (valor)', 2),
            (u'3 - Lista neutra (valor)', 3),
            (u'4 - Margem Valor Agregado (%)', 4),
            (u'5 - Pauta (valor)', 5),
        ),
    }

    MAP_VALID_WIDGETS = {
        0: ['orig', 'cst', 'mod_bc', 'p_icms', 'v_bc', 'v_icms',
            'bc_include_ipi'],
        10: ['orig', 'cst', 'mod_bc', 'p_icms', 'mod_bc_st', 'p_mva_st',
             'p_red_bc_st', 'p_icms_st', 'v_bc', 'v_icms', 'v_bc_st',
             'v_icms_st', 'bc_include_ipi', 'bc_st_include_ipi'],
        20: ['orig', 'cst', 'mod_bc', 'p_icms', 'p_red_bc', 'v_bc',
             'v_icms', 'bc_include_ipi'],
        30: ['orig', 'cst', 'mod_bc_st', 'p_mva_st', 'p_red_bc_st',
             'p_icms_st', 'v_bc_st', 'v_icms_st', 'bc_st_include_ipi'],
        40: ['orig', 'cst'], #
        41: ['orig', 'cst'], # Same tag
        50: ['orig', 'cst'], #
        51: ['orig', 'cst', 'mod_bc', 'p_red_bc', 'p_icms', 'v_bc',
             'v_icms', 'bc_st_include_ipi'],
        60: ['orig', 'cst', 'v_bc_st', 'v_icms_st'],
        70: normal_widgets,
        90: normal_widgets,
        # Simples Nacional
        101: ['orig', 'csosn', 'p_cred_sn', 'p_cred_sn_valid_until',
              'v_cred_icms_sn'],
        102: ['orig', 'csosn'],
        103: ['orig', 'csosn'],
        201: ['orig', 'csosn', 'mod_bc_st', 'p_mva_st', 'p_red_bc_st',
              'p_icms_st', 'v_bc_st', 'v_icms_st', 'p_cred_sn',
              'p_cred_sn_valid_until', 'v_cred_icms_sn'],
        202: ['orig', 'csosn', 'mod_bc_st', 'p_mva_st', 'p_red_bc_st',
              'p_icms_st', 'v_bc_st', 'v_icms_st'],
        203: ['orig', 'csosn', 'mod_bc_st', 'p_mva_st', 'p_red_bc_st',
              'p_icms_st', 'v_bc_st', 'v_icms_st'],
        300: ['orig', 'csosn'],
        400: ['orig', 'csosn'],
        500: ['orig', 'csosn', 'v_bc_st_ret', 'v_icms_st_ret'],
    }

    def setup_proxies(self):
        self._setup_widgets()
        self.branch = api.get_current_branch(self.model.get_connection())
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

        # Simple Nacional
        if self.branch.crt in [1, 2]:
            self._update_selected_csosn()
        else:
            self._update_selected_cst()

    def _update_widgets(self):
        has_p_cred_sn = (self.p_cred_sn.get_sensitive()
                         and bool(self.p_cred_sn.get_value()))
        self.p_cred_sn_valid_until.set_sensitive(has_p_cred_sn)

    def _update_p_cred_sn_valid_until(self):
        if (self.p_cred_sn.get_value()
            and not self.p_cred_sn_valid_until.get_date()):
                # Set the default expire date to the last day of current month.
            default_expire_date = (datetime.date.today() +
                                   relativedelta(day=1, months=+1, days=-1))
            self.p_cred_sn_valid_until.set_date(default_expire_date)

    def _update_selected_cst(self):
        cst = self.cst.get_selected_data()
        valid_widgets = self.MAP_VALID_WIDGETS.get(cst, ('cst', ))
        self.set_valid_widgets(valid_widgets)

    def _update_selected_csosn(self):
        csosn = self.csosn.get_selected_data()
        valid_widgets = self.MAP_VALID_WIDGETS.get(csosn, ('csosn', ))
        self.set_valid_widgets(valid_widgets)

    def on_cst__changed(self, widget):
        self._update_selected_cst()

    def on_csosn__changed(self, widget):
        self._update_selected_csosn()
        self._update_widgets()

    def after_p_cred_sn__changed(self, widget):
        self._update_p_cred_sn_valid_until()
        self.p_cred_sn_valid_until.validate(force=True)
        self._update_widgets()

    def on_p_cred_sn_valid_until__validate(self, widget, value):
        if not self.p_cred_sn.get_value():
            return
        if value <= datetime.date.today():
            return ValidationError(_(u"This date must be set in the future."))


class ICMSTemplateSlave(BaseICMSSlave):
    model_type = ProductIcmsTemplate
    proxy_widgets = (BaseICMSSlave.combo_widgets +
                     BaseICMSSlave.percentage_widgets +
                     BaseICMSSlave.date_widgets)
    hide_widgets = BaseICMSSlave.value_widgets


class SaleItemICMSSlave(BaseICMSSlave):
    model_type = SaleItemIcms
    proxy_widgets = (BaseICMSSlave.combo_widgets +
                     BaseICMSSlave.percentage_widgets +
                     BaseICMSSlave.bool_widgets +
                     BaseICMSSlave.value_widgets)
    hide_widgets = BaseICMSSlave.date_widgets

    def setup_callbacks(self):
        for name in self.percentage_widgets:
            widget = getattr(self, name)
            widget.connect_after('changed', self._after_field_changed)

        self.bc_include_ipi.connect_after('toggled', self._after_field_changed)
        self.bc_st_include_ipi.connect_after('toggled', self._after_field_changed)
        self.cst.connect_after('changed', self._after_field_changed)

    def update_values(self):
        self.model.update_values()
        for name in self.value_widgets:
            self.proxy.update(name)

    def _after_field_changed(self, widget):
        if not self.proxy:
            return

        self.update_values()


class BaseIPISlave(BaseTaxSlave):
    gladefile = 'TaxIPISlave'

    combo_widgets = ['cst', 'calculo']
    percentage_widgets = ['p_ipi']
    text_widgets = ['cl_enq', 'cnpj_prod', 'c_selo', 'c_enq']
    value_widgets = ['v_ipi', 'v_bc', 'v_unid', 'q_selo', 'q_unid']
    all_widgets = (combo_widgets + percentage_widgets + value_widgets +
                   text_widgets)

    tooltips = {
        'cl_enq': u'Preenchimento conforme Atos Normativos editados pela '
                  u'Receita Federal (Observação 4)',
        'cnpj_prod': u'Informar os zeros não significativos',
        'c_selo': u'Preenchimento conforme Atos Normativos editados pela '
                  u'Receita Federal (Observação 3)',
        'c_enq': u'Tabela a ser criada pela RFB, informar 999 enquanto a '
                 u'tabela não for criada',
    }

    field_options = {
        'cst': (
            (None, None),
            (u'00 - Entrada com recuperação de crédito', 0),
            (u'01 - Entrada tributada com alíquota zero', 1),
            (u'02 - Entrada isenta', 2),
            (u'03 - Entrada não-tributada', 3),
            (u'04 - Entrada imune', 4),
            (u'05 - Entrada com suspensão', 5),
            (u'49 - Outras entradas', 49),
            (u'50 - Saída tributada', 50),
            (u'51 - Saída tributada com alíquota zero', 51),
            (u'52 - Saída isenta', 52),
            (u'53 - Saída não-tributada', 53),
            (u'54 - Saída imune', 54),
            (u'55 - Saída com suspensão', 55),
            (u'99 - Outras saídas', 99),
        ),
        'calculo': (
            (u'Por alíquota', 0),
            (u'Valor por unidade', 1),
        )
    }

    # This widgets should be enabled when this option is selected.
    MAP_VALID_WIDGETS = {
        0: all_widgets,
        1: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        2: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        3: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        4: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        5: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        49: all_widgets,
        50: all_widgets,
        51: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        52: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        53: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        54: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        55: ['cst', 'cl_enq', 'cnpj_prod', 'c_selo', 'q_selo', 'c_enq'],
        99: all_widgets,
    }

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
        self._update_selected_cst()
        self._update_selected_calculo()

    def _update_selected_cst(self):
        cst = self.cst.get_selected_data()
        valid_widgets = self.MAP_VALID_WIDGETS.get(cst, ('cst', ))
        self.set_valid_widgets(valid_widgets)

    def _update_selected_calculo(self):
        # IPI is only calculated if cst is one of the following
        if not self.model.cst in (0, 49, 50, 99):
            return

        calculo = self.calculo.get_selected_data()

        if calculo == SaleItemIpi.CALC_ALIQUOTA:
            self.p_ipi.set_sensitive(True)
            self.v_bc.set_sensitive(True)
            self.v_unid.set_sensitive(False)
            self.q_unid.set_sensitive(False)
        elif calculo == SaleItemIpi.CALC_UNIDADE:
            self.p_ipi.set_sensitive(False)
            self.v_bc.set_sensitive(False)
            self.v_unid.set_sensitive(True)
            self.q_unid.set_sensitive(True)

    def on_cst__changed(self, widget):
        self._update_selected_cst()

    def on_calculo__changed(self, widget):
        self._update_selected_calculo()


class IPITemplateSlave(BaseIPISlave):
    model_type = ProductIpiTemplate
    proxy_widgets = (BaseIPISlave.combo_widgets +
                     BaseIPISlave.percentage_widgets +
                     BaseIPISlave.text_widgets)
    hide_widgets = BaseIPISlave.value_widgets


class SaleItemIPISlave(BaseIPISlave):
    model_type = SaleItemIpi
    proxy_widgets = BaseIPISlave.all_widgets

    def setup_callbacks(self):
        self.p_ipi.connect_after('changed', self._after_field_changed)
        self.q_unid.connect_after('changed', self._after_field_changed)
        self.v_unid.connect_after('changed', self._after_field_changed)
        self.cst.connect_after('changed', self._after_field_changed)

    def update_values(self):
        self.model.update_values()
        self.proxy.update('v_bc')
        self.proxy.update('v_ipi')

    def _after_field_changed(self, widget):
        if not self.proxy:
            return

        self.update_values()

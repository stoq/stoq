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
## Author(s):   Ronaldo Maia  <romaia@async.com.br>
##
""" Slaves for books """

import sys

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.slaves.sellableslave import SellableDetailsSlave
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product
from stoqlib.domain.taxes import SaleItemIcms, ProductIcmsTemplate
from stoqlib.lib.countries import get_countries
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class BaseTaxSlave(BaseEditorSlave):
    combo_widgets = ()
    percentage_widgets = ()
    value_widgets = ()

    hide_widgets = ()

    field_options = {}

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
            getattr(self, w+'_label').hide()

    def set_valid_widgets(self, valid_widgets):
        for widget in self.all_widgets:
            if widget in valid_widgets:
                getattr(self, widget).set_sensitive(True)
                getattr(self, widget+'_label').set_sensitive(True)
            else:
                getattr(self, widget).set_sensitive(False)
                getattr(self, widget+'_label').set_sensitive(False)




class BaseICMSSlave(BaseTaxSlave):
    gladefile = 'TaxICMSSlave'

    combo_widgets = ['cst', 'orig', 'mod_bc', 'mod_bc_st']
    percentage_widgets = ['p_icms', 'p_mva_st', 'p_red_bc_st', 'p_icms_st',
                          'p_red_bc']
    value_widgets = ['v_bc', 'v_icms', 'v_bc_st', 'v_icms_st']
    all_widgets = combo_widgets + percentage_widgets + value_widgets

    field_options = {
        'cst': (
            (None, None),
            ('00 - Tributada Integralmente', 0),
            ('10 - Tributada e com cobrança de ICMS por subst. trib.', 10),
            ('20 - Com redução de BC', 20),
            ('30 - Isenta ou não trib. e com cobrança de ICMS por subst. trib.', 30),
            ('40 - Isenta', 40),
            ('41 - Não tributada', 41),
            ('50 - Suspensão', 50),
            ('51 - Deferimento', 51),
            ('60 - ICMS cobrado anteriormente por subst. trib.', 60),
            ('70 - Com redução da BC cobrança do ICMS por subst. trib.', 70),
            ('90 - Outros', 90),
        ),
        'orig': (
            (None, None),
            ('0 - Nacional', 0),
            ('1 - Estrangeira - importação direta', 1),
            ('2 - Estrangeira - adquirida no mercado interno', 2),
        ),
        'mod_bc': (
            (None, None),
            ('0 - Margem do valor agregado (%)', 0),
            ('1 - Pauta (Valor)', 1),
            ('2 - Preço tabelado máximo (valor)', 2),
            ('3 - Valor da operação', 3),
        ),
        'mod_bc_st': (
            (None, None),
            ('0 - Preço tabelado ou máximo sugerido', 0),
            ('1 - Lista negativa (valor)', 1),
            ('2 - Lista positiva (valor)', 2),
            ('3 - Lista neutra (valor)', 3),
            ('4 - Margem Valor Agregado (%)', 4),
            ('5 - Pauta (valor)', 5),
        ),
    }



    # This widgets should be enabled when this option is selected.
    MAP_VALID_WIDGETS = {
        0: ['orig', 'cst', 'mod_bc', 'p_icms', 'v_bc', 'v_icms'],
        10: ['orig', 'cst', 'mod_bc', 'p_icms', 'mod_bc_st', 'p_mva_st',
             'p_red_bc_st', 'p_icms_st', 'v_bc', 'v_icms', 'v_bc_st',
             'v_icms_st'],
        20: ['orig', 'cst', 'mod_bc', 'p_icms', 'p_red_bc', 'v_bc', 'v_icms'],
        30: ['orig', 'cst', 'mod_bc_st', 'p_mva_st', 'p_red_bc_st',
             'p_icms_st', 'v_bc_st', 'v_icms_st' ],
        40: ['orig', 'cst'], #
        41: ['orig', 'cst'], # Same tag # FIXME
        50: ['orig', 'cst'], #
        51: ['orig', 'cst', 'mod_bc', 'p_red_bc', 'p_icms', 'v_bc', 'v_icms'],
        60: ['orig', 'cst', 'v_bc_st', 'v_icms_st' ], # FIXME
        70: all_widgets,
        90: all_widgets,
    }


    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
        self._update_selected_cst()

    def _update_selected_cst(self):
        cst = self.cst.get_selected_data()
        valid_widgets = self.MAP_VALID_WIDGETS.get(cst, ('cst', ))
        self.set_valid_widgets(valid_widgets)

    def on_cst__changed(self, widget):
        self._update_selected_cst()


class ICMSTemplateSlave(BaseICMSSlave):
    model_type = ProductIcmsTemplate
    proxy_widgets = (BaseICMSSlave.combo_widgets +
                     BaseICMSSlave.percentage_widgets)
    hide_widgets = BaseICMSSlave.value_widgets


class SaleItemICMSSlave(BaseICMSSlave):
    model_type = SaleItemIcms
    proxy_widgets = BaseICMSSlave.all_widgets



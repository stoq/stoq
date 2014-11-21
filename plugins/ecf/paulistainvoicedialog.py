# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
##

from kiwi.datatypes import ValidationError
from kiwi.python import Settable

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import validate_cpf, validate_cnpj

from ecf.ecfdomain import FiscalSaleHistory

_ = stoqlib_gettext


class PaulistaInvoiceDialog(BaseEditor):
    """A dialog to generate Paulista invoices"""
    title = _(u"Paulista Invoice")
    hide_footer = False
    size = (-1, 160)
    model_type = Settable
    translation_domain = 'stoq'
    domain = 'ecf'
    gladefile = "PaulistaInvoice"
    proxy_widgets = ("document", )
    cpf_mask = u"000.000.000-00"
    cnpj_mask = u"00.000.000/0000-00"

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def create_model(self, store):
        return Settable(document=u'',
                        document_type=FiscalSaleHistory.TYPE_CPF)

    def _setup_widgets(self):
        self._initial_document = self.model.document
        self._initial_document_type = self.model.document_type
        self.handler_block('document', 'validate')
        if self._initial_document_type == FiscalSaleHistory.TYPE_CPF:
            self._set_cpf()
        else:
            self.cnpj.set_active(True)
        self.handler_unblock('document', 'validate')

    def _set_cpf(self):
        self.doc_label.set_text(_(u"CPF:"))
        self.document.set_mask(self.cpf_mask)
        self.model.document_type = FiscalSaleHistory.TYPE_CPF
        if self._initial_document_type == FiscalSaleHistory.TYPE_CPF:
            self.document.set_text(self._initial_document)
        self.document.grab_focus()
        self.main_dialog.set_cancel_label(_(u"Without CPF"))

    def _set_cnpj(self):
        self.doc_label.set_text(_(u"CNPJ:"))
        self.document.set_mask(self.cnpj_mask)
        self.model.document_type = FiscalSaleHistory.TYPE_CNPJ
        if self._initial_document_type == FiscalSaleHistory.TYPE_CNPJ:
            self.document.set_text(self._initial_document)
        self.document.grab_focus()
        self.main_dialog.set_cancel_label(_(u"Without CNPJ"))

    #
    # BaseEditor
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def validate_confirm(self):
        if self.document.is_empty():
            if self._initial_document_type == FiscalSaleHistory.TYPE_CPF:
                doc = 'CPF'
            else:
                doc = 'CNPJ'
            info(_("The %s cannot be empty") % doc)
            return False

        return True

    #
    # Kiwi callbacks
    #

    def on_cpf__toggled(self, widget):
        if self.cpf.get_active():
            self._set_cpf()
        else:
            self._set_cnpj()

    def on_document__validate(self, widget, value):
        # this will allow the user to use an empty value to this field
        if self.document.is_empty():
            return
        if self.cpf.get_active() and not validate_cpf(value):
            return ValidationError(_(u"The CPF is not valid."))
        elif self.cnpj.get_active() and not validate_cnpj(value):
            return ValidationError(_(u"The CNPJ is not valid."))

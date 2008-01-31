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
## Author(s):   George Y. Kussumoto         <george@async.com.br>
##
##

from kiwi.python import Settable

from stoqlib.domain.fiscal import PaulistaInvoice
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class PaulistaInvoiceDialog(BaseEditor):
    """"""
    title = _(u"Paulista Invoice")
    hide_footer = False
    size = (260, 160)
    model_type = Settable
    gladefile = "PaulistaInvoice"
    cpf_mask = u"000.000.000-00"
    cnpj_mask = u"00.000.000/0000-00"

    def __init__(self, conn, sale):
        self.model = self._create_model(sale)
        BaseEditor.__init__(self, conn, self.model)
        self._setup_widgets()

    def _create_model(self, sale):
        return Settable(sale=sale, document=u'',
                        document_type=PaulistaInvoice.TYPE_CPF)

    def _setup_widgets(self):
        self._set_cpf()
        self.validate_confirm()

    def _set_cpf(self):
        self.doc_label.set_text(_(u"CPF:"))
        self.doc_entry.set_mask(self.cpf_mask)
        self.model.document_type = PaulistaInvoice.TYPE_CPF
        self.doc_entry.grab_focus()

    def _set_cnpj(self):
        self.doc_label.set_text(_(u"CNPJ:"))
        self.doc_entry.set_mask(self.cnpj_mask)
        self.model.document_type = PaulistaInvoice.TYPE_CNPJ
        self.doc_entry.grab_focus()

    #
    # BaseEditor
    #

    def on_confirm(self):
        return PaulistaInvoice(sale=self.model.sale,
                               document_type=self.model.document_type,
                               document=self.model.document,
                               connection=self.conn)

    #
    # Kiwi callbacks
    #

    def on_cpf__toggled(self, widget):
        if self.cpf.get_active():
            self._set_cpf()
        else:
            self._set_cnpj()

    def on_doc_entry__content_changed(self, widget):
        self.model.document = widget.get_text()

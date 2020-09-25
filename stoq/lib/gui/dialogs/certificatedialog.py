# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
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

from kiwi.enums import ListType
from stoqlib.lib.objutils import Settable
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.certificate import PasswordObfuscator, Certificate
from stoq.lib.gui.base.lists import ModelListDialog, ModelListSlave
from stoq.lib.gui.editors.baseeditor import BaseEditor
from stoq.lib.gui.editors.certificateeditor import CertificateEditor
from stoqlib.lib.translation import stoqlib_gettext as _


class CertificatePasswordDialog(BaseEditor):
    size = (-1, -1)
    model_type = PasswordObfuscator
    gladefile = 'CertificatePasswordDialog'
    model_name = _("Certificate Password")
    proxy_widgets = ['password']

    def __init__(self, cert_name, retry=False):
        super(CertificatePasswordDialog, self).__init__(None)

        text = _("Enter the password for <b>%s</b>:") % (api.escape(cert_name), )
        if retry:
            error_text = '<b><span color="red">%s</span></b>' % (
                api.escape(_("Wrong password provided...")), )
            text = "%s\n%s" % (error_text, text)
        self.info_lbl.set_markup(text)

    #
    #  BaseEditor
    #

    def create_model(self, store):
        return PasswordObfuscator(password=u'')

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)

    def cancel(self):
        if not super(CertificatePasswordDialog, self).cancel():
            return False

        self.model.password = None
        self.retval = self.model
        return True


class CertificateChooserDialog(BaseEditor):
    size = (-1, -1)
    model_type = Settable
    gladefile = 'CertificateChooserDialog'
    model_name = _("Certificate Chooser")
    proxy_widgets = ['cert']

    def __init__(self, certs, last_used):
        self._certs = certs
        self._last_used = last_used if last_used in certs else None

        super(CertificateChooserDialog, self).__init__(None)

    #
    #  BaseEditor
    #

    def create_model(self, store):
        return Settable(cert=self._last_used)

    def setup_proxies(self):
        self.cert.prefill([(cert, cert) for cert in self._certs])
        self.add_proxy(self.model, self.proxy_widgets)


class CertificateListSlave(ModelListSlave):
    editor_class = CertificateEditor
    model_type = Certificate
    columns = [
        Column('active', title=_("Active"), data_type=bool),
        Column('type_str', title=_("Type"), data_type=str),
        Column('name', title=_("Certificate"), data_type=str, expand=True),
    ]

    def __init__(self, *args, **kwargs):
        ModelListSlave.__init__(self, *args, **kwargs)
        self.set_list_type(ListType.UNREMOVABLE)


class CertificateListDialog(ModelListDialog):
    list_slave_class = CertificateListSlave
    title = _("Certificates")
    size = (500, 300)

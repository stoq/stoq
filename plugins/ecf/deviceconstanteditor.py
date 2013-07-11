# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
"""Interface for manipulating Device Constants"""

import re

import gtk
from kiwi.decorators import signal_block
from kiwi.python import Settable
from kiwi.ui.objectlist import Column, ObjectList

from stoqdrivers.enum import TaxType
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.defaults import UNKNOWN_CHARACTER
from stoqlib.lib.translation import stoqlib_gettext

from ecf.ecfdomain import ECFPrinter, DeviceConstant

_ = stoqlib_gettext

_HEX_REGEXP = re.compile("[0-9a-fA-F]{1,2}")


def dec2hex(dec):
    return "".join([data.encode("hex") for data in dec])


def hex2dec(hex):
    # pylint: disable=W0402
    import string
    dec = ""
    for data in _HEX_REGEXP.findall(hex):
        data = data.zfill(2).decode("hex")
        if not data in string.printable:
            data = UNKNOWN_CHARACTER
        dec += data
    # pylint: enable=W0402
    return dec


class _DeviceConstantEditor(BaseEditor):
    gladefile = 'DeviceConstantEditor'
    model_type = DeviceConstant
    model_name = _('Device constant')
    proxy_widgets = ('constant_name',
                     'constant_value',
                     'constant_type_description',
                     'device_value',
                     'device_value_hex',
                     )

    def __init__(self, store, model=None, printer=None, constant_type=None):
        if not isinstance(printer, ECFPrinter):
            raise TypeError("printer should be a ECFPrinter, not %s" % printer)
        self.printer = printer
        self.constant_type = constant_type

        BaseEditor.__init__(self, store, model)

        # Hide value label/entry for non tax types
        if constant_type != DeviceConstant.TYPE_TAX:
            self.label_value.hide()
            self.constant_value.hide()

    @signal_block('device_value.content_changed')
    def _update_dec(self, value):
        self.device_value.set_text(value)

    @signal_block('device_value_hex.content_changed')
    def _update_hex(self, value):
        self.device_value_hex.set_text(value)

    def create_model(self, store):
        return DeviceConstant(store=store,
                              printer=self.printer,
                              constant_type=self.constant_type,
                              constant_value=None,
                              constant_name=u"Unnamed",
                              constant_enum=int(TaxType.CUSTOM),
                              device_value=None)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    _DeviceConstantEditor.proxy_widgets)
        self.proxy.update('device_value')

    #
    # Callbacks
    #

    def on_device_value_hex__content_changed(self, entry):
        self._update_dec(hex2dec(entry.get_text()))

    def on_device_value__content_changed(self, entry):
        self._update_hex(dec2hex(entry.get_text()))


class _DeviceConstantsList(AdditionListSlave):
    def __init__(self, store, printer):
        self._printer = printer
        self._constant_type = None
        AdditionListSlave.__init__(self, store,
                                   self._get_columns())
        self.connect('on-add-item', self._on_list_slave__add_item)
        self.connect('before-delete-items',
                     self._on_list_slave__before_delete_items)

    def _get_columns(self):
        return [Column('constant_name', _('Name'), expand=True),
                Column('device_value', _('Value'), data_type=str,
                       width=120, format_func=lambda x: repr(x)[1:-1])]

    def _before_delete_items(self, list_slave, items):
        self.store.commit()
        self._refresh()

    def _refresh(self):
        self.klist.clear()
        self.klist.extend(self._printer.get_constants_by_type(
            self._constant_type))

    #
    # AdditionListSlave
    #

    def run_editor(self, model):
        return run_dialog(_DeviceConstantEditor, store=self.store,
                          model=model,
                          printer=self._printer,
                          constant_type=self._constant_type)

    #
    # Public API
    #

    def switch(self, constant_type):
        self._constant_type = constant_type
        self._refresh()

    #
    # Callbacks
    #

    def _on_list_slave__add_item(self, slave, item):
        self._refresh()

    def _on_list_slave__before_delete_items(self, slave, items):
        for item in items:
            DeviceConstant.delete(item.id, store=self.store)


class DeviceConstantsDialog(BasicDialog):
    size = (500, 300)

    def __init__(self, store, printer):
        self._constant_slave = None
        self.store = store
        self.printer = printer

        BasicDialog.__init__(self, hide_footer=False, title='edit',
                             size=self.size)
        self.main.set_border_width(6)

        self._create_ui()

    def _create_ui(self):
        hbox = gtk.HBox()
        self.klist = ObjectList([Column('name')])
        self.klist.set_size_request(150, -1)
        self.klist.get_treeview().set_headers_visible(False)
        self.klist.connect('selection-changed',
                           self._on_klist__selection_changed)
        hbox.pack_start(self.klist)
        hbox.show()

        for name, ctype in [(_(u'Units'), DeviceConstant.TYPE_UNIT),
                            (_(u'Tax'), DeviceConstant.TYPE_TAX),
                            (_(u'Payments'), DeviceConstant.TYPE_PAYMENT)]:
            self.klist.append(Settable(name=name, type=ctype))
        self.klist.show()

        self._constant_slave = _DeviceConstantsList(self.store, self.printer)
        self._constant_slave.switch(DeviceConstant.TYPE_UNIT)

        hbox.pack_start(self._constant_slave.get_toplevel())

        # FIXME: redesign BasicDialog
        self.main.remove(self.main_label)
        self.main.add(hbox)

        hbox.show_all()

    def _on_klist__selection_changed(self, klist, selected):
        self._constant_slave.switch(selected.type)

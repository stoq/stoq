# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
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
""" Grid configuration editor implementation."""

import collections

import gtk
from kiwi.ui.objectlist import Column
from kiwi.ui.forms import TextField, BoolField

from stoqlib.api import api
from stoqlib.gui.base.lists import ModelListSlave
from stoqlib.domain.product import GridGroup, GridAttribute, GridOption
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.fields import GridGroupField
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class GridGroupEditor(BaseEditor):
    model_name = _('Grid Group')
    model_type = GridGroup
    gladefile = 'GridGroupEditor'
    proxy_widgets = ['description', 'active_check_box']
    confirm_widgets = ['description']

    def __init__(self, store, model=None, visual_mode=False):
        BaseEditor.__init__(self, store, model, visual_mode)
        if model:
            self.set_description(model.description)

        self.active_check_box.set_property('sensitive', bool(model))

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return GridGroup(store=self.store, description=u'')

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, GridGroupEditor.proxy_widgets)


class GridAttributeEditor(BaseEditor):
    model_name = _('Grid Attribute')
    model_type = GridAttribute
    gladefile = 'GridAttributeEditor'
    size = (400, 350)

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            group=GridGroupField(_('Attribute group'), proxy=True, mandatory=True),
            description=TextField(_('Attribute name'), proxy=True, mandatory=True),
            is_active=BoolField(_('Is active'), proxy=True),
        )

    def __init__(self, store, model=None, visual_mode=False, group=None):
        self._group = group

        BaseEditor.__init__(self, store, model, visual_mode)
        # Only let the user edit if its a new attribute
        if model:
            self.set_description(model.description)

        self.fields['group'].set_sensitive(not self._group)
        self.fields['is_active'].set_sensitive(bool(model))

    #
    # BaseEditor Hooks
    #

    def setup_slaves(self):
        slave = _GridOptionsSlave(self.store, self.model)
        self.attach_slave('options_holder', slave)

    def create_model(self, store):
        group = self._group or GridGroup.get_active_groups(store).any()
        return GridAttribute(store=self.store, description=u'', group=group)

    def setup_proxies(self):
        groups = list(GridGroup.get_active_groups(self.store))
        # If the current group is no longer active, we must add it to the list
        # of groups:
        if not self.model.group.is_active:
            groups.append(self.model.group)

        self.fields['group'].prefill(
            api.for_combo(groups, attr='description'), self.model.group)
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def validate_confirm(self):
        if self.store.find(GridOption, attribute=self.model).is_empty():
            warning(_("You need to add at least one option"))
            return False

        return True


class GridOptionEditor(BaseEditor):
    model_name = _('Grid Attribute Option')
    model_type = GridOption
    gladefile = 'GridOptionEditor'
    proxy_widgets = ['description', 'option_order_spin', 'active_check_box']
    confirm_widgets = ['description']

    def __init__(self, store, model=None, visual_mode=False, attribute=None):
        self._attribute = attribute
        BaseEditor.__init__(self, store, model, visual_mode)
        if model:
            self.set_description(model.description)

        self.active_check_box.set_property('sensitive', bool(model))

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return GridOption(store=self.store, description=u'',
                          attribute=self._attribute)

    def setup_proxies(self):
        self.option_order_spin.set_adjustment(gtk.Adjustment(lower=0,
                                                             upper=100,
                                                             step_incr=1,
                                                             page_incr=5))
        self.proxy = self.add_proxy(self.model, GridOptionEditor.proxy_widgets)


class _GridOptionsSlave(ModelListSlave):
    model_type = GridOption
    editor_class = GridOptionEditor
    columns = [
        Column('description', _('Description'), data_type=str, expand=True),
        Column('is_active', _('Active'), data_type=bool),
        Column('option_order', _('Option order'), data_type=int)
    ]

    def __init__(self, store, attribute):
        self._attribute = attribute
        ModelListSlave.__init__(self, store=store, reuse_store=True)

    def populate(self):
        return self.store.find(self.model_type, attribute=self._attribute)

    def selection_changed(self, selected):
        if not selected:
            return

        can_remove = selected.can_remove()
        self.listcontainer.remove_button.set_sensitive(can_remove)

    def run_editor(self, store, model):
        return self.run_dialog(self.editor_class, store=store, model=model,
                               attribute=self._attribute)


def test_grid_editor():  # pragma nocover
    from stoqlib.gui.base.dialogs import run_dialog
    ec = api.prepare_test()
    group = ec.store.find(GridGroup).any()
    attribute = ec.create_grid_attribute(attribute_group=group)
    attribute.group = None
    run_dialog(GridAttributeEditor,
               parent=None, store=ec.store, model=attribute)
    print attribute.group

if __name__ == '__main__':  # pragma nocover
    test_grid_editor()

# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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
""" Dialog for detecting duplicate person registers and merging them

Duplicate detection is currenctly really simple and works like this:

1) All data is fetched from the database.
2) We iter through each item, reducing it to a key, that will be used to detect
the duplicates
2.1) The key will be calculated using the persons name, phone and/or address
street (configurable)
2.2) We insert the key in a dictionary, where the value is a list of objects
that match the same key

After this, all items in the dictionary that have more than one person are
considered duplicate by the given criteria

Room for improvement:
    - Add some way the user can choose which register will be kept
    - Add some way the user can choose field values from other registers that
      will be used to update the main register.
    - Use a soundex algorithm to reduce even further the name
    - phone number and mobile number may be swaped across duplicate registers.
    - Add an entry so the user can restrict the search (for when he already
      knows there is someone duplicate)
"""

import gtk
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.person import PersonAddressView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.progressdialog import ProgressDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import yesno
from stoqlib.lib.formatters import format_phone_number
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _DupModel(object):
    """A temporary model for the duplicated tree.

    When no person is provided, this means it represents a root node in the tree
    (ie, it has a list of duplicate data).
    """

    def __init__(self, person=None, name=None, parent=None):
        self.duplicates = []
        self.parent = parent
        self.merge = False
        if name:
            assert not person
            self.name = name
        else:
            assert not name
            assert parent
            self.person = person
            self.name = person.name
            self.email = person.email
            self.phone_number = person.phone_number
            self.cpf = person.cpf
            self.cnpj = person.cnpj
            self.mobile_number = person.mobile_number
            self.fax_number = person.fax_number
            self.address = (person.main_address and
                            person.main_address.get_address_string())

    def add_dup(self, model):
        self.duplicates.append(model)

    def get_to_merge(self):
        return [i for i in self.duplicates if i.merge]


class _MethodModel(object):
    (SAME_NAME,
     FIRST_NAME,
     FIRST_LAST_NAME) = range(3)

    def __init__(self):
        self.method = self.SAME_NAME
        self.same_phone = True
        self.same_street = True
        self._street_prefixes = api.get_l10n_field('common_street_prefixes')

    def _get_street_name(self, person):
        street = person.clean_street.strip()
        for prefix in self._street_prefixes:
            if street.startswith(prefix):
                street = street[len(prefix):]
                break
        return street.strip()

    def _get_name(self, person):
        if self.method == self.SAME_NAME:
            return person.clean_name
        elif self.method == self.FIRST_NAME:
            first_name = person.clean_name.split(' ')[0]
            return first_name
        elif self.method == self.FIRST_LAST_NAME:
            parts = person.clean_name.split(' ')
            if len(parts) == 1:
                return parts[0]
            else:
                return parts[0] + parts[-1]

    def get_key(self, person):
        key = [self._get_name(person)]
        if self.same_phone:
            phone_number = str(person.phone_number)[-8:]
            if not phone_number or len(phone_number) < 6:
                return None
            key.append(phone_number)

        if self.same_street:
            street = self._get_street_name(person)
            # We cant trust when the street name is to short
            if len(street) <= 3:
                return None
            key.append(street)

        return tuple(key)


class NameColumn(Column):
    def attach(self, objectlist):
        column = Column.attach(self, objectlist)

        # Add another renderer for checking if the person will be merged
        self._bool_renderer = gtk.CellRendererToggle()
        self._bool_renderer.connect('toggled', self._on_merge_toggled)
        column.pack_start(self._bool_renderer, False)
        column.reorder(self._bool_renderer, 0)
        return column

    def cell_data_func(self, tree_column, text_renderer,
                       model, treeiter, (column, renderer_prop)):
        obj = model[treeiter][0]
        if obj.parent:
            text_renderer.set_property(renderer_prop, obj.name)
        else:
            to_merge = obj.get_to_merge()
            text = obj.name + _(' (%s duplicates)') % len(to_merge)
            text_renderer.set_property(renderer_prop, text)

        # The checkbox will only be visible then the row is not a parent node.
        self._bool_renderer.set_property('active', obj.merge)
        self._bool_renderer.set_property('visible', obj.parent)

        # Display the row in bold when the user has checked if for merging, to
        # make it easyer distinguishing them
        weight = 400
        if obj.merge:
            weight = 800
        text_renderer.set_property('weight', weight)

    def _on_merge_toggled(self, renderer, path):
        model = self._objectlist.get_model()
        obj = model[path][0]
        # Invert the model attribute. Note that when this is emitted, the
        # renderer wont change the state automatically. It will the next time
        # cell_data_func is called (and we change the active property)
        obj.merge = not obj.merge


class PersonMergeDialog(BaseEditor):
    gladefile = "PersonMergeDialog"
    size = (800, 550)
    title = _(u'Duplicate Person Search')
    model_type = _MethodModel
    hide_footer = True
    proxy_widgets = ['method_combo', 'same_phone', 'same_street']

    methods = [
        (_('Identical name'), _MethodModel.SAME_NAME),
        (_('First and last name'), _MethodModel.FIRST_LAST_NAME),
        (_('First name'), _MethodModel.FIRST_NAME),
    ]

    def setup_proxies(self):
        self.dup_tree.set_columns(self._get_columns())
        self.merge_button.set_sensitive(False)
        self.method_combo.prefill(self.methods)

        self.add_proxy(self.model, self.proxy_widgets)

    def create_model(self, store):
        return _MethodModel()

    #
    #   Public API
    #

    def merge(self, store, to_merge):
        self._create_progress(_('Merging duplicate'))

        first = store.fetch(to_merge[0].person.person)
        rest = to_merge[1:]
        total = len(rest)
        for i, other in enumerate(rest):
            first.merge_with(store.fetch(other.person.person),
                             copy_empty_values=True)
            self._update_progress(i, total)

        self._close_progress()

    #
    # Private API
    #

    def _create_progress(self, title):
        self._progress_dialog = ProgressDialog(title, pulse=False)
        self._progress_dialog.set_transient_for(self.main_dialog)
        self._progress_dialog.start(wait=0)
        self._progress_dialog.cancel.hide()

    def _update_progress(self, current, total):
        self._progress_dialog.progressbar.set_text('%s/%s' % (current, total))
        self._progress_dialog.progressbar.set_fraction((current + 1) / float(total))
        while gtk.events_pending():
            gtk.main_iteration(False)

    def _close_progress(self):
        self._progress_dialog.stop()

    def _search_duplicates(self):
        self._create_progress(_('Searching duplicates'))
        data = self.store.find(PersonAddressView).order_by(PersonAddressView.name)
        total = data.count()
        self.dup_tree.clear()
        dups_total = 0

        # A dictionaty mapping a reduced version of the person to a list of
        # persons that match this reduced version.
        person_dict = {}

        # A cache of duplicate registers already found.
        dups = []

        for i, person in enumerate(data):
            key = self.model.get_key(person)
            if not key:
                continue

            entry = person_dict.setdefault(key, [])
            if len(entry) == 1:
                # The entry already has one person in it. So we can consider
                # this a duplicate.
                dups.append(entry)
            entry.append(person)

            if len(entry) >= 2:
                dups_total += 1

            if i % 100 == 0:
                self._update_progress(i, total)

        self.message.set_text(_('Found %s persons in a total of %s duplicate registers')
                              % (len(dups), dups_total + len(dups)))
        self._close_progress()
        self._build_duplicate_tree(dups)

    def _build_duplicate_tree(self, dups):
        for d in dups:
            root = _DupModel(name=d[0].name)
            self.dup_tree.append(None, root)
            for obj in d:
                model = _DupModel(person=obj, parent=root)
                root.add_dup(model)
                self.dup_tree.append(root, model)
            self.dup_tree.expand(root)

    def _get_columns(self):
        return [NameColumn(title=_('Name'), data_type=str, width=350),
                Column('cpf', title=_('CPF'), data_type=str),
                Column('cnpj', title=_('CNPJ'), data_type=str),
                Column('phone_number', title=_('Phone'), data_type=str,
                       format_func=format_phone_number),
                Column('mobile_number', title=_('Mobile'), data_type=str,
                       format_func=format_phone_number),
                Column('address', title=_('Address'), data_type=str, width=250),
                Column('fax_number', title=_('Fax'), data_type=str,
                       format_func=format_phone_number),
                Column('email', title=_('Email'), data_type=str)]

    #
    # Callbacks
    #

    def on_search_button__clicked(self, widget):
        self._search_duplicates()

    def on_merge_button__clicked(self, widget):
        model = self.dup_tree.get_selected()
        to_merge = model.get_to_merge()
        msg = (_("This will merge %s persons into 1. Are you sure?") %
               len(to_merge))
        if not yesno(msg, gtk.RESPONSE_NO, _("Merge"), _("Don't merge")):
            return

        with api.new_store() as store:
            self.merge(store, to_merge)

        if store.committed:
            self.dup_tree.remove(model)

    def on_dup_tree__selection_changed(self, olist, item):
        can_merge = item and len(item.get_to_merge()) > 1
        self.merge_button.set_sensitive(bool(can_merge))


if __name__ == '__main__':  # pragma nocover
    ec = api.prepare_test()
    run_dialog(PersonMergeDialog, None, ec.store)

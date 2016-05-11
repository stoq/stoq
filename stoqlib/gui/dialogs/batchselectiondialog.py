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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import collections
import datetime
import decimal

import gtk
from kiwi import ValueUnset
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column
from kiwi.ui.entry import ENTRY_MODE_DATA
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.spinbutton import ProxySpinButton

from stoqlib.api import api
from stoqlib.domain.product import Storable, StorableBatch, StorableBatchView
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.defaults import QUANTITY_PRECISION, MAX_INT
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.message import warning
from stoqlib.lib.stringutils import next_value_for, max_value_for
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BatchSelectionDialog(BaseEditor):
    """A dialog for selecting batch quantities

    This editor will help to generate quantities for batches given a
    |storable|. By default, it will add an entry and a spin button to
    select the batch and it's quantity. That spin button will be
    pre-filled with *quantity* passed in from the dialog constructor
    so you can just fill the batch and confirm the dialog.

    But as soon as you fill a valid batch, a new entry and spin button
    will be appended below the last ones, so you can add more quantities
    to/from another batch.

    When confirming, a dict will be returned mapping the batch to it's
    quantity. Note that *batch' there can be a text (containing the
    batch number) or an object (containing the |batch| in question).
    That will depend on the editor (see :class:`.BatchIncreaseSelectionDialog`
    and :class:`.BatchDecreaseSelectionDialog` for more information).

    """

    #: if we should validate the quantity and treat is as a maximum
    #: quantity. If ``True``, the sum of all quantities on spin buttons
    #: cannot be greater than the *quantity* passed in from the dialog
    #: constructor for the dialog to be confirmed. If ``False``, it will
    #: have no limit.
    validate_max_quantity = False

    #: If we should show a list displaying the existing batches. It's used
    #: to make easier to check for batch's stock, creation date, etc
    show_existing_batches_list = True

    #: If ``True``, activating an entry (e.g. pressing Enter) will confirm
    #: the dialog. If ``False``, the default behaviour will happen that is
    #: to set focus on the spinbutton (and that spinbutton is always
    #: set to confirm the dialog on activation)
    confirm_dialog_on_entry_activate = False

    #: If we should allow to indicate a batch with a quantity of 0. The
    #: default is ``False`` which will always set a quantity of 0 as invalid
    allow_no_quantity = False

    size = (600, 400)
    title = _("Batch selection")
    gladefile = 'BatchSelectionDialog'
    model_type = Storable
    proxy_widgets = [
        'description',
    ]

    def __init__(self, store, model, quantity, original_batches=None):
        """
        :param store: the store for this editor
        :param model: the |storable| used to generate the batch quantities
        :param quantity: the quantity used to fill the first appended spin.
            Note that if :attr:`.validate_max_quantity` is set to ``True``
            and this is different than 0, it will be used to validate the
            dialog as a maximum quantity (see the attr doc for more
            information). Passing 0 here means forcing no validation
            (so the user can type whatever he wants)
        :param original_batches: a dict mapping the batch to it's
            original quantity to be populated on entries. Very useful when
            calling this editor to edit the same model
        :param visual_mode: if we are working on visual mode
        """
        if quantity < 0:
            raise ValueError("The quantity cannot be negative")

        # quantity = 0 means forcing no validation
        if quantity == 0:
            self._validate_max_quantity = False
        else:
            self._validate_max_quantity = self.validate_max_quantity

        self._quantity = quantity
        # A simple lock, used to avoid some problems (infinity recursion,
        # spin being updated wrong, etc) when appending a new dumb row
        self._append_dumb_row_lock = 0
        # The last entry appended
        self._last_entry = None
        # This dicts store what is the spin given an entry,
        # or the entry given the spin
        self._spins = collections.OrderedDict()
        self._entries = collections.OrderedDict()

        BaseEditor.__init__(self, store, model=model, visual_mode=False)

        self._append_initial_rows(original_batches)

    #
    #  Public API
    #

    def get_entry_by_spin(self, spin):
        """Gets an entry given a *spin*

        This will return the entry that makes a pair with the
        spin on the dialog

        :returns: a :class:`kiwi.ui.widgets.ProxyEntry`
        """
        return self._entries[spin]

    def get_spin_by_entry(self, entry):
        """Gets a spin given an *entry*

        This will return the spin that makes a pair with the
        entry on the dialog

        :returns: a :class:`kiwi.ui.widgets.ProxyEntry`
        """
        return self._spins[entry]

    def get_batch_item(self, batch):
        """A hook called to get the batch item for the given batch

        By default, it will return the batch itself. Subclasses can
        override this if they are working with other type of items
        on the entries (e.g. the batch number as a string)

        :param batch: the |batch|
        :returns: the batch item that will be used to update
            the entry's value
        """
        return batch

    def setup_entry(self, entry):
        """A hook called every time a new entry is appended on the dialog

        Subclasses can override this if they want to do some extra
        setup on the entry (for example, setting a completion).

        :param entry: the :class:`kiwi.ui.widgets.ProxyEntry`
        """

    def setup_spin(self, entry):
        """A hook called every time a new spin button is appended on the dialog

        Subclasses can override this if they want to do some extra
        setup on the spin button.

        :param entry: the :class:`kiwi.ui.widgets.ProxySpinButton`
        """

    def validate_entry(self, entry):
        """A hook called to validate *entry*

        This should return :class:`kiwi.datatypes.ValidationError` if
        the *entry* is not valid.

        Subclasses can override this.

        :param entry: the :class:`kiwi.ui.widgets.ProxyEntry`
        """

    def validate_spin(self, spin):
        """A hook called to validate *spin*

        This should return :class:`kiwi.datatypes.ValidationError` if
        the *spin* is not valid.

        Subclasses can override this.

        :param spin: the :class:`kiwi.ui.widgets.ProxySpinButton`
        """

    #
    #  BaseEditor
    #

    def validate_confirm(self):
        if self._get_diff_quantity() < 0:
            warning(_("There's some outstanding quantity. Adjust them "
                      "before you can confirm"))
            return False

        return True

    def setup_proxies(self):
        # If there's no max quantity, there's no reason to
        # have a missing/outstanding quantity
        if not self._validate_max_quantity:
            for widget in [self.diff_quantity, self.diff_quantity_lbl]:
                widget.hide()

        if self.show_existing_batches_list:
            self.existing_batches.set_columns([
                Column('batch_number', _(u"Number"), data_type=str, expand=True),
                Column('create_date', _(u"Creation date"),
                       data_type=datetime.date, sorted=True),
                Column('stock', _(u"Available"), data_type=decimal.Decimal,
                       format_func=format_quantity)])
            self.existing_batches.add_list(self._get_existing_batches())
        else:
            self.existing_batches_expander.hide()

        self.add_proxy(self.model, self.proxy_widgets)

    def on_confirm(self):
        self.retval = collections.OrderedDict()

        for entry, spin in self._spins.items():
            batch = entry.read()
            if not batch or batch == ValueUnset:
                continue

            self.retval[batch] = spin.read()

    #
    #  Private
    #

    def _get_existing_batches(self):
        branch = api.get_current_branch(self.store)
        return StorableBatchView.find_available_by_storable(
            self.store, self.model, branch=branch)

    def _get_total_sum(self):
        return sum(spin.read() for entry, spin in self._spins.items() if
                   entry.read() and entry.read() != ValueUnset)

    def _get_diff_quantity(self):
        if not self._validate_max_quantity:
            return 0

        return self._quantity - self._get_total_sum()

    def _append_initial_rows(self, batches=None):
        self._append_dumb_row_lock += 1

        batches = batches or {}
        if not batches:
            self._append_or_update_row(self._quantity, mandatory=True)

        for batch, quantity in batches.items():
            self._append_or_update_row(quantity, batch=batch)

        self._update_view()
        self._append_dumb_row_lock -= 1

    def _create_entry(self, mandatory=False):
        entry = ProxyEntry()

        entry.data_type = unicode
        # Set as empty or kiwi will return ValueUnset on entry.read()
        # and we would have to take that in consideration everywhere here
        entry.update(u'')
        entry.mandatory = mandatory
        self.setup_entry(entry)

        entry.connect_after('content-changed',
                            self._after_entry__content_changed)
        entry.connect_after('changed', self._after_entry__changed)
        entry.connect('validate', self._on_entry__validate)
        entry.connect('activate', self._on_entry__activate)

        return entry

    def _create_spin(self):
        spin = ProxySpinButton()

        spin.data_type = decimal.Decimal
        unit = self.model.product.sellable.unit
        upper = self._quantity if self._validate_max_quantity else MAX_INT
        spin.set_adjustment(gtk.Adjustment(lower=0, upper=upper,
                                           step_incr=1, page_incr=10))
        if unit and unit.allow_fraction:
            spin.set_digits(QUANTITY_PRECISION)
        self.setup_spin(spin)

        spin.connect_after('content-changed',
                           self._after_spinbutton__content_changed)
        spin.connect('validate', self._on_spinbutton__validate)

        return spin

    def _append_or_update_row(self, quantity=None, batch=None,
                              mandatory=False, grab_focus=False):
        last_entry = self._last_entry
        last_spin = self._last_entry and self._spins[self._last_entry]

        # If the last entry is not valid (no batch set), use it
        # instead of appending a lot of invalids
        if (last_entry is not None and
            (not last_entry.read() or not last_spin.read())):
            if quantity is not None:
                last_spin.update(quantity)
            # The batch is already None. Only update it if not None
            # to avoid update_view being called again here (no problem
            # for the spin because it should be insensitive)
            if batch is not None:
                self._last_entry.update(self.get_batch_item(batch))
                if grab_focus:
                    last_spin.grab_focus()
            return

        self._append_dumb_row_lock += 1

        entry = self._create_entry(mandatory)
        spin = self._create_spin()
        if quantity is not None:
            spin.set_value(quantity)
        self._spins[entry] = spin
        self._entries[spin] = entry
        self._last_entry = entry

        n_rows = self.main_table.get_property('n-rows')
        for i, widget in enumerate([entry, spin]):
            self.main_table.attach(widget, i, i + 1, n_rows, n_rows + 1,
                                   gtk.FILL, 0, 0, 0)
            widget.show()

        focus_chain = self.main_table.get_focus_chain() or []
        self.main_table.set_focus_chain(focus_chain + [entry, spin])

        # FIXME: Kiwi will only set mandatory and call validate events (and
        # other stuff) on widgets on a proxy. Remove this when fixing kiwi
        entry_name = '_entry_%d' % len(self._entries)
        spin_name = '_spin_%d' % len(self._spins)
        for widget, name in [(entry, entry_name), (spin, spin_name)]:
            setattr(self, name, widget)
            setattr(self.model, name, widget.read())
        self.add_proxy(self.model, [entry_name, spin_name])

        # Allow to confirm the editor by pressing enter on any spin
        self.set_confirm_widget(spin)
        if self.confirm_dialog_on_entry_activate:
            self.set_confirm_widget(entry)
        # Do this after adding the widget to the proxy so the validate
        # signal gets emitted
        entry.update(self.get_batch_item(batch))
        # Don't grab focus on the spin if we have to fill the batch
        if batch and grab_focus:
            spin.grab_focus()

        self._append_dumb_row_lock -= 1

    def _append_or_update_dumb_row(self):
        if self._append_dumb_row_lock > 0:
            return

        diff = self._get_diff_quantity()

        # If we have a max quantity and there's no diff, don't append a new row
        if self._validate_max_quantity and diff <= 0:
            return
        # No entry appended yet
        if self._last_entry is None:
            return
        # If the last entry is the first entry (the only mandatory)
        # wait until it's valid to add another one
        if self._last_entry.mandatory and not self._last_entry.read():
            return

        self._append_or_update_row(abs(diff))

    def _update_view(self):
        diff = self._get_diff_quantity()

        self.quantity.update(format_quantity(self._get_total_sum()))
        self.diff_quantity.update(format_quantity(abs(diff)))
        self.diff_quantity_lbl.set_text(
            _("Missing quantity:") if diff >= 0 else
            _("Outstanding quantity:"))

        self._append_or_update_dumb_row()

    def _validate_entry(self, entry, value):
        self._spins[entry].validate(force=True)

        for other_entry in self._entries.values():
            if other_entry is entry:
                continue
            entry_value = other_entry.read()
            if entry_value and entry_value == value:
                return ValidationError(_("This batch is already selected"))

        return self.validate_entry(entry=entry)

    #
    #  Callbacks
    #

    def on_existing_batches__row_activated(self, existing_batches, item):
        # If the item doesn't have stock, don't append it
        if not item.stock:
            return

        # FIXME: When grabbing focus here (both cases below), if the row
        # was activated by pressing 'Enter', the focus is grabbed right (and
        # thus, we can type the quantity for that batch directly). But if it
        # was activated by 'Double-click', it appears to be focussed, but the
        # focus is still on the objectlist
        batch = item.batch
        for spin, entry in self._entries.items():
            if entry.read() == batch:
                spin.grab_focus()
                return

        diff = self._get_diff_quantity()
        # The diff could be 0 or less if all the suggested quantity is filled.
        # If that happens, pass None for the spin to use it's created value
        if diff <= 0:
            diff = None
        self._append_or_update_row(diff, batch=batch, grab_focus=True)

    def _after_entry__changed(self, entry):
        # FIXME: This is a *very* ugly workaround, but if the entry is on
        # data mode, it will only emit validate and content-changed when
        # the widget goes from not-matched-object to a matched-object
        # (and vice-versa). Remove this when fixed on kiwi
        valid = self._validate_entry(entry, entry.get_text())
        if isinstance(valid, ValidationError):
            entry.set_invalid(str(valid))

    def _on_entry__activate(self, entry):
        # On activation, grab focus on entry's spin (but only if it's valid)
        if entry.read():
            self._spins[entry].grab_focus()

    def _on_entry__validate(self, entry, value):
        return self._validate_entry(entry, value)

    def _after_entry__content_changed(self, entry):
        self._spins[entry].set_sensitive(
            entry.read() not in [None, u'', ValueUnset])
        self._update_view()

    def _on_spinbutton__validate(self, spin, value):
        batch = self._entries[spin].read()
        if batch is not None and not self.allow_no_quantity and value == 0:
            return ValidationError(_("The quantity cannot be 0"))

        sellable = self.model.product.sellable
        if not self.model.product.sellable.is_valid_quantity(value):
            return ValidationError(_("This product unit (%s) does not "
                                     "support fractions.") %
                                   sellable.unit_description)

        return self.validate_spin(spin=spin)

    def _after_spinbutton__content_changed(self, spin):
        self._update_view()


class BatchDecreaseSelectionDialog(BatchSelectionDialog):
    """Batch selection for storable decreases

    This is the same as :class:`BatchSelectionDialog`,
    but since the quantity selected here is going to be decreased,
    it will be validated for each batch (so no batch is allowed
    to have more quantity than the available in stock)

    Also, the *batch* key on the returned dict will be a |batch|.

    """

    def __init__(self, store, model, quantity,
                 original_batches=None, decreased_batches=None):
        """
        :param decreased_batches: a dict mapping the batch to it's
            already decreased. Useful when you have some quantity
            already decreased on a store for example and you want it to be
            taken in consideration when checking for stock availability
        """
        self._decreased_batches = decreased_batches or {}
        BatchSelectionDialog.__init__(self, store, model, quantity,
                                      original_batches=original_batches)

    #
    #  BatchSelectionDialog
    #

    def setup_proxies(self):
        BatchSelectionDialog.setup_proxies(self)
        # For decreases, it's very useful for this to be expanded
        self.existing_batches_expander.set_expanded(True)

    def setup_entry(self, entry):
        entry.set_mode(ENTRY_MODE_DATA)
        entry.set_exact_completion()
        completion = entry.get_completion()
        completion.set_minimum_key_length = 1
        items = self.model.get_available_batches(
            api.get_current_branch(self.store))
        entry.prefill(api.for_combo(items))

    def validate_entry(self, entry):
        text = entry.get_text()
        if text == '':
            return

        if entry.read() is None:
            return ValidationError(_("'%s' is not a valid batch") % text)

    def validate_spin(self, spin):
        quantity = spin.read()
        batch = self.get_entry_by_spin(spin).read()
        if batch is None:
            return

        branch = api.get_current_branch(self.store)
        available_qty = batch.get_balance_for_branch(branch)
        for decreased_batch, decreased_quantity in self._decreased_batches.items():
            if decreased_batch == batch:
                available_qty -= decreased_quantity

        if quantity > available_qty:
            return ValidationError(_("There's only %s available in stock for "
                                     "the given batch") % available_qty)


# Editors/wizards using BatchIncreaseSelectionDialog will create the
# StorableBatch after confirming it, so we need this dict to known which ones
# are being used at the moment. That makes possible for us to validate already
# used batch numbers (they should be unique among all batches) and also to get
# the next value of the sequence based on the maximum here
_used_batches_mapper = {}


class BatchIncreaseSelectionDialog(BatchSelectionDialog):
    """Batch selection for storable increases

    This is the same as :class:`BatchSelectionDialog`,
    but since the quantity selected here is going to be increased
    there's no limit for quantities in each batch (unless specified
    by the *max_quantity* param)

    Also, the *batch* key on the returned dict will
    be a string object, containing the batch number.

    """

    validate_max_quantity = True

    #
    #  _BatchSelectionDialog
    #

    def on_confirm(self):
        super(BatchIncreaseSelectionDialog, self).on_confirm()

        used = set(batch for batch in self.retval)
        # Replace the existing one instead of replacing since some batches
        # may have been removed and thus are allowed for other storables
        _used_batches_mapper[(self.store, self.model.id)] = used

    def get_batch_item(self, batch):
        if isinstance(batch, basestring):
            return batch
        if batch is not None:
            return batch.batch_number
        if not api.sysparam.get_bool('SUGGEST_BATCH_NUMBER'):
            return None

        return self._get_next_batch_number()

    def validate_entry(self, entry):
        batch_number = unicode(entry.get_text())
        if not batch_number:
            return

        available = StorableBatch.is_batch_number_available(
            self.store, batch_number, exclude_storable=self.model)
        if (not available or
            batch_number in self._get_used_batches(exclude=batch_number)):
            return ValidationError(_("'%s' is already in use") % batch_number)

    #
    #  Private
    #

    def _get_next_batch_number(self):
        max_db = StorableBatch.get_max_batch_number(self.store)
        max_used = max_value_for(self._get_used_batches() | set([max_db]))
        if not api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            return next_value_for(max_used)

        # On synchronized mode we need to append the branch acronym
        # to avoid conflicts
        max_used_list = max_used.split('-')
        if len(max_used_list) == 1:
            # '123'
            max_used = max_used_list[0]
        elif len(max_used_list) == 2:
            # '123-AB'
            max_used = max_used_list[0]
        else:
            # TODO: Maybe we should allow only one dash in the batch number
            # '123-456-AB'
            max_used = ''.join(max_used_list[:-1])

        branch = api.get_current_branch(self.store)
        if not branch.acronym:
            raise ValueError("branch '%s' needs an acronym since we are on "
                             "synchronized mode" % (branch.get_description(),))
        return '-'.join([next_value_for(max_used), branch.acronym])

    def _get_used_batches(self, exclude=None):
        in_use = set()

        for k in _used_batches_mapper:
            # Excluding our batches from the used to avoid 'already in use'
            # problems when editing the same batches a second time
            if k == (self.store, self.model.id):
                continue
            in_use.update(_used_batches_mapper[k])

        for entry in self._entries.values():
            batch_number = entry.read()
            if batch_number == exclude:
                continue
            in_use.add(entry.read())

        return in_use

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
import decimal
import sys

import gtk
from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.spinbutton import ProxySpinButton

from stoqlib.api import api
from stoqlib.domain.product import Storable
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.defaults import QUANTITY_PRECISION
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#: a simple :py:`collections.namedtuple` used by this modules' editors
#: to generate batch information. The *batch* element will represent a
#: |batch| or it's batch number (which one is documented on the
#: editor) and the *quantity* element represents the quantity of that batch
BatchItem = collections.namedtuple('BatchItem', ['batch', 'quantity'])


class _StorableBatchSelectionDialog(BaseEditor):
    """A dialog for selecting batch quantities

    This editor will help to generate quantities for batches given a
    |storable|. By default, it will add an entry and a spin button to
    select the batch and it's quantity. That spin button will be
    pre-filled with *quantity* passed in from the dialog constructor
    so you can just fill the batch and confirm the dialog.

    But as soon as you fill a valid batch, a new entry and spin button
    will be appended below the last ones, so you can add more quantities
    to/from another batch.

    When confirming, a list of :class:`batch items <.BatchItem>` will be
    returned. Note that *batch' there can be a text (containing the
    batch number) or an object (containing the |batch| in question).
    That will depend on the editor (see :class:`.BatchIncreaseSelectionDialog`
    and :class:`.BatchDecreaseSelectionDialog` for more information).

    """

    #: if we should validate the quantity and treat is as a maximum
    #: quantity. If ``True``, the sum of all quantities on spin buttons
    #: cannot be greater than the *quantity* passed in from the dialog
    #: constructor for the dialog to be confirmed. If ``False``, it will
    #: have no limit.
    VALIDATE_MAX_QUANTITY = None

    size = (400, -1)
    title = _("Batch selection")
    gladefile = 'StorableBatchSelectionEditor'
    model_type = Storable
    proxy_widgets = [
        'description',
    ]

    def __init__(self, store, model, quantity, original_batches=None):
        """
        :param store: the store for this editor
        :param model: the |storable| used to generate the batch quantities
        :param quantity: the quantity used to fill the first appended spin.
            Note that if :attr:`.VALIDATE_MAX_QUANTITY` is set to ``True``
            and this is different than 0, it will be used to validate the
            dialog as a maximum quantity (see the attr doc for more
            information). Passing 0 here means forcing no validation
            (so the user can type whatever he wants)
        :param original_batches: a sequence of :class:`batch item <.BatchItem>`
            with original items to be populated on entries. Very useful when
            calling this editor to edit the same model
        :param visual_mode: if we are working on visual mode
        """
        if self.VALIDATE_MAX_QUANTITY is None:
            raise ValueError(
                "The class %s must define a VALIDATE_MAX_QUANTITY" % (
                    self.__class__.__name__))

        if quantity < 0:
            raise ValueError("The quantity cannot be negative")

        # quantity = 0 means forcing no validation
        if quantity == 0:
            self._validate_max_quantity = False
        else:
            self._validate_max_quantity = self.VALIDATE_MAX_QUANTITY

        self._quantity = quantity
        # A simple lock, used to avoid some problems (infinity recursion,
        # spin being updated wrong, etc) when appending a new dumb row
        self._append_dumb_row_lock = 0
        # The last entry appended
        self._last_entry = None
        # This dicts store what is the spin given an entry,
        # or the entry given the spin
        self._spins = {}
        self._entries = {}

        BaseEditor.__init__(self, store, model=model, visual_mode=False)

        self._append_initial_rows(original_batches)
        self._update_view()

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

        self.add_proxy(self.model, self.proxy_widgets)

    def on_confirm(self):
        self.retval = []

        for entry, spin in self._spins.items():
            batch = entry.read()
            if not batch:
                continue
            self.retval.append(BatchItem(batch=batch, quantity=spin.read()))

    #
    #  Private
    #

    def _get_total_sum(self):
        return sum(spin.read() for spin in
                   self._spins.values() if spin.get_sensitive())

    def _get_diff_quantity(self):
        if not self._validate_max_quantity:
            return 0

        return self._quantity - self._get_total_sum()

    def _append_initial_rows(self, batches=None):
        self._append_dumb_row_lock += 1

        # No problem if we have _default_batches because they will update this
        self._append_or_update_row(self._quantity, mandatory=True)

        for item in batches or []:
            batch, quantity = item.batch, item.quantity
            self._append_or_update_row(quantity, batch=batch)

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
        upper = self._quantity if self._validate_max_quantity else sys.maxint
        spin.set_adjustment(gtk.Adjustment(lower=0, upper=upper,
                                           step_incr=1, page_incr=10))
        if unit and unit.allow_fraction:
            spin.set_digits(QUANTITY_PRECISION)
        self.setup_spin(spin)

        spin.connect_after('content-changed',
                           self._after_spinbutton__content_changed)
        spin.connect('validate', self._on_spinbutton__validate)

        return spin

    def _append_or_update_row(self, quantity, batch=None, mandatory=False):
        # If the last entry is not valid (no batch set), use it
        # instead of appending a lot of invalids
        if self._last_entry is not None and not self._last_entry.read():
            self._spins[self._last_entry].update(quantity)
            # The batch is already None. Only update it if not None
            # to avoid update_view being called again here (no problem
            # for the spin because it should be insensitive)
            if batch is not None:
                self._last_entry.update(batch)
            return

        self._append_dumb_row_lock += 1

        entry = self._create_entry(mandatory)
        spin = self._create_spin()
        spin.set_value(quantity)
        self._spins[entry] = spin
        self._entries[spin] = entry
        self._last_entry = entry

        n_rows = self.main_table.get_property('n-rows')
        for i, widget in enumerate([entry, spin]):
            self.main_table.attach(widget, i, i + 1, n_rows, n_rows + 1,
                                   gtk.FILL, 0, 0, 0)
            widget.show()

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
        # Do this after adding the widget to the proxy so the validate
        # signal gets emitted
        entry.update(batch)

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
        self._spins[entry].set_sensitive(bool(entry.read()))
        self._update_view()

    def _on_spinbutton__validate(self, spin, value):
        batch = self._entries[spin].read()
        if batch is not None and not value:
            return ValidationError(_("The quantity cannot be 0"))

        sellable = self.model.product.sellable
        if not self.model.product.sellable.is_valid_quantity(value):
            return ValidationError(_("This product unit (%s) does not "
                                     "support fractions.") %
                                   sellable.get_unit_description())

        return self.validate_spin(spin=spin)

    def _after_spinbutton__content_changed(self, spin):
        self._update_view()


class BatchDecreaseSelectionDialog(_StorableBatchSelectionDialog):
    """Batch selection for storable decreases

    This is the same as :class:`_StorableBatchSelectionDialog`,
    but since the quantity selected here is going to be decreased,
    it will be validated for each batch (so no batch is allowed
    to have more quantity than the available in stock)

    Also, the *batch* on the returned :class:`.BatchItem` will be a |batch|.

    """

    VALIDATE_MAX_QUANTITY = False

    def __init__(self, store, model, quantity,
                 original_batches=None, decreased_batches=None):
        """
        :param decreased_batches: a sequence of :class:`batch item <.BatchItem>`
            of quantities already decreased. Useful when you have some quantity
            already decreased on a store for example and you want it to be
            taken in consideration when checking for stock availability
        """
        self._decreased_batches = decreased_batches or []
        _StorableBatchSelectionDialog.__init__(self, store, model, quantity,
                                               original_batches=original_batches)

    #
    #  _StorableBatchSelectionDialog
    #

    def setup_entry(self, entry):
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
        for batch_item in self._decreased_batches:
            if batch_item.batch == batch:
                available_qty -= batch_item.quantity

        if quantity > available_qty:
            return ValidationError(_("There's only %s available in stock for "
                                     "the given batch") % available_qty)


class BatchIncreaseSelectionDialog(_StorableBatchSelectionDialog):
    """Batch selection for storable increases

    This is the same as :class:`_StorableBatchSelectionDialog`,
    but since the quantity selected here is going to be increased
    there's no limit for quantities in each batch (unless specified
    by the *max_quantity* param)

    Also, the *batch* on the returned :class:`.BatchItem` will
    be a string object, containing the batch number.

    """

    VALIDATE_MAX_QUANTITY = True

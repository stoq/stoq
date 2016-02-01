# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2014 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Search filters, graphical widgets to interactively create advanced queries"""

import datetime
from decimal import Decimal

import gobject
import gtk
from kiwi import ValueUnset
from kiwi.environ import environ
from kiwi.python import enum
from kiwi.ui.pixbufutils import pixbuf_from_string
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.ui.widgets.entry import ProxyDateEntry
from kiwi.ui.widgets.multicombo import ProxyMultiCombo
from kiwi.utils import gsignal
from zope.interface import implementer

from stoqlib.database.interfaces import ISearchFilter
from stoqlib.database.queryexecuter import (NumberQueryState, StringQueryState,
                                            DateQueryState, DateIntervalQueryState,
                                            NumberIntervalQueryState,
                                            BoolQueryState, MultiQueryState)
from stoqlib.gui.search.searchoptions import (Any,
                                              Between,
                                              IdenticalTo,
                                              ContainsExactly,
                                              ContainsAll,
                                              DoesNotContain,
                                              ComboEquals,
                                              ComboDifferent,
                                              EqualsTo,
                                              FixedDateSearchOption,
                                              FixedIntervalSearchOption,
                                              GreaterThan,
                                              LastMonth,
                                              LastWeek,
                                              LowerThan,
                                              Today,
                                              Yesterday)
from stoqlib.gui.widgets.hintedentry import HintedEntry
from stoqlib.gui.widgets.searchfilterbutton import SearchFilterButton
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# Search Filters
#

@implementer(ISearchFilter)
class SearchFilter(gtk.HBox):
    """
    A base class used by common search filters
    """

    #: the label of this filter
    label = gobject.property(type=str, flags=(gobject.PARAM_READWRITE))

    gsignal('changed')
    gsignal('removed')
    __gtype_name__ = 'SearchFilter'

    def __init__(self, label=''):
        gtk.HBox.__init__(self)
        self.props.label = label
        self._label = label
        self._remove_button = None

    def _add_remove_button(self):
        self._remove_button = SearchFilterButton(stock=gtk.STOCK_REMOVE)
        self._remove_button.set_relief(gtk.RELIEF_NONE)
        self._remove_button.set_label_visible(False)
        self._remove_button.connect('clicked', self._on_remove_clicked)
        self._remove_button.show()
        self.pack_start(self._remove_button, False, False)

    def _on_remove_clicked(self, button):
        self.emit('removed')

    def do_set_property(self, pspec, value):
        if pspec.name == 'label':
            self._label = value
        else:
            raise AssertionError(pspec.name)

    def do_get_property(self, child, property_id, pspec):
        if pspec.name == 'label':
            return self._label
        else:
            raise AssertionError(pspec.name)

    def set_label(self, label):
        self._label = label

    def get_state(self):
        """
        Implement this in a subclass
        """
        raise NotImplementedError

    def get_title_label(self):
        raise NotImplementedError

    def get_mode_combo(self):
        raise NotImplementedError

    def get_description(self):
        """Returns a description of the search filter.
        :returns: a string describing the search filter.
        """
        raise NotImplementedError

    def set_removable(self):
        if self._remove_button is None:
            self._add_remove_button()


class DateSearchFilter(SearchFilter):
    """
    A filter which helps you to search by a date interval.
    Can be customized through add_option.
    """
    __gtype_name__ = 'DateSearchFilter'

    class Type(enum):
        (USER_DAY,
         USER_INTERVAL) = range(100, 102)

    def __init__(self, label=''):
        """
        Create a new DateSearchFilter object.
        :param label: name of the search filter
        """
        self._options = {}
        SearchFilter.__init__(self, label=label)
        self.title_label = gtk.Label(label)
        self.pack_start(self.title_label, False, False)
        self.title_label.show()

        self.mode = ProxyComboBox()
        self.mode.connect(
            'content-changed',
            self._on_mode__content_changed)
        self.pack_start(self.mode, False, False, 6)
        self.mode.show()

        self.from_label = gtk.Label(_("From:"))
        self.pack_start(self.from_label, False, False)
        self.from_label.show()

        self.start_date = ProxyDateEntry()
        self._start_changed_id = self.start_date.connect(
            'content-changed', self._on_start_date__changed)
        self.pack_start(self.start_date, False, False, 6)
        self.start_date.show()

        self.to_label = gtk.Label(_("To:"))
        self.pack_start(self.to_label, False, False)
        self.to_label.show()

        self.end_date = ProxyDateEntry()
        self._end_changed_id = self.end_date.connect(
            'content-changed', self._on_end_date__changed)
        self.pack_start(self.end_date, False, False, 6)
        self.end_date.show()

        self.add_custom_options()

        for option in (Any, Today, Yesterday, LastWeek, LastMonth):
            self.add_option(option)

        self.mode.select_item_by_position(0)

    #
    # SearchFilter
    #

    def get_state(self):
        start = self.start_date.get_date()
        end = self.end_date.get_date()
        if start == end:
            return DateQueryState(filter=self, date=start)
        return DateIntervalQueryState(filter=self, start=start, end=end)

    def set_state(self, start, end=None):
        self.start_date.set_date(start)
        if end is not None:
            self.end_date.set_date(end)

    def get_title_label(self):
        return self.title_label

    def get_mode_combo(self):
        return self.mode

    def get_description(self):
        desc = ''
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        if start_date:
            if end_date and start_date != end_date:
                desc += ' %s %s %s %s' % (_(u'from'), start_date.strftime('%x'),
                                          _(u'to'), end_date.strftime('%x'),)

            else:
                desc += start_date.strftime('%x')
        if desc:
            return '%s %s' % (self.get_title_label().get_text(), desc,)

    #
    # Public API
    #

    def clear_options(self):
        """
        Removes all previously added options
        """
        self._options = {}
        self.mode.clear()

    def add_option(self, option_type, position=-2):
        """
        Adds a date option
        :param option_type: option to add
        :type option_type: a :class:`DateSearchOption` subclass
        """
        option = option_type()
        num = len(self.mode) + position
        self.mode.insert_item(num, option.name, option_type)
        self._options[option_type] = option

    def add_option_fixed(self, name, date, position=-2):
        """
        Adds a fixed option, eg one for which date is not
        possible to modify.
        :param name: name of the option
        :param date: fixed data
        :param position: position to add the option at
        """
        option_type = type('', (FixedDateSearchOption,),
                           dict(name=name, date=date))
        self.add_option(option_type, position=position)

    def add_option_fixed_interval(self, name, start, end, position=-2):
        """
        Adds a fixed option interval, eg one for which the dates are not
        possible to modify.
        :param name: name of the option
        :param start: start of the fixed interval
        :param end: end of the fixed interval
        :param position: position to add the option at
        """
        option_type = type('', (FixedIntervalSearchOption,),
                           dict(name=name, start=start, end=end))
        self.add_option(option_type, position=position)

    def add_custom_options(self):
        """Adds the custom options 'Custom day' and 'Custom interval' which
        let the user define its own interval dates.
        """
        pos = len(self.mode) + 1
        for name, option_type in [
            (_('Custom day'), DateSearchFilter.Type.USER_DAY),
            (_('Custom interval'), DateSearchFilter.Type.USER_INTERVAL)]:

            self.mode.insert_item(pos, name, option_type)
            pos += 1

    def get_start_date(self):
        """
        Get the start date.
        :returns: start date
        :rtype: datetime.date or None
        """
        return self.start_date.get_date()

    def get_end_date(self):
        """
        Get the end date.
        :returns: end date
        :rtype: datetime.date or None
        """
        return self.end_date.get_date()

    def set_use_date_entries(self, use_date_entries):
        """
        Toggles the visibility of the user selectable date entries
        :param use_date_entries:
        """
        self.from_label.props.visible = use_date_entries
        self.to_label.props.visible = use_date_entries
        self.start_date.props.visible = use_date_entries
        self.end_date.props.visible = use_date_entries

    def select(self, data=None, position=None):
        """
        selects an item in the combo
        Data or position can be sent in. If nothing
        is sent in the first item will be selected, if any

        :param data: data to select
        :param position: position of data to select
        """
        if data is not None and position is not None:
            raise TypeError("You can't send in both data and position")

        if data is None and position is None:
            position = 0

        if position is not None:
            if len(self.mode):
                self.mode.select_item_by_position(position)
        elif data:
            self.mode.select(data)

    #
    # Private
    #

    def _update_dates(self):
        # This is called when we change mode
        date_type = self.mode.get_selected_data()
        if date_type is None:
            return

        # If we switch to a user selectable day, make sure that
        # both dates are set to today
        if date_type == DateSearchFilter.Type.USER_DAY:
            today = datetime.date.today()
            self.start_date.set_date(today)
            self.end_date.set_date(today)
        # And for user interval, set start to today and to tomorrow
        elif date_type == DateSearchFilter.Type.USER_INTERVAL:
            today = datetime.date.today()
            self.start_date.set_date(today)
            self.end_date.set_date(today + datetime.timedelta(days=1))
        # Finally for pre-defined ones let the DateSearchOption decide what the
        # values are going to be, these dates are not user editable so
        # we don't need to do any checking.
        else:
            option = self._options.get(date_type)
            assert option, (date_type, self._options)
            start_date, end_date = option.get_interval()
            self.start_date.set_date(start_date)
            self.end_date.set_date(end_date)

    def _update_sensitivity(self):
        date_type = self.mode.get_selected_data()
        enabled = date_type == DateSearchFilter.Type.USER_INTERVAL
        self.to_label.set_sensitive(enabled)
        self.end_date.set_sensitive(enabled)

        enabled = (date_type == DateSearchFilter.Type.USER_INTERVAL or
                   date_type == DateSearchFilter.Type.USER_DAY)
        self.from_label.set_sensitive(enabled)
        self.start_date.set_sensitive(enabled)

    def _internal_set_start_date(self, date):
        self.start_date.handler_block(self._start_changed_id)
        self.start_date.set_date(date)
        self.start_date.handler_unblock(self._start_changed_id)

    def _internal_set_end_date(self, date):
        self.end_date.handler_block(self._end_changed_id)
        self.end_date.set_date(date)
        self.end_date.handler_unblock(self._end_changed_id)

    def _restore_date_validation(self):
        self.start_date.set_valid()
        self.end_date.set_valid()

    #
    # Callbacks
    #

    def _on_mode__content_changed(self, mode):
        self._update_dates()
        self._update_sensitivity()
        self._restore_date_validation()
        self.emit('changed')

    def _on_start_date__changed(self, start_date):
        date_type = self.mode.get_selected_data()
        start = start_date.get_date()
        # For user days, just make sure that the date entries
        # always are in sync
        if date_type == DateSearchFilter.Type.USER_DAY:
            if start is None:
                self.start_date.set_invalid(_(u'Invalid date'))
            else:
                self.start_date.set_valid()
                self._internal_set_end_date(start)
        # Make sure that we cannot select a start date after
        # the end date, be nice and increase the end date if
        # the start date happen to be the same
        elif date_type == DateSearchFilter.Type.USER_INTERVAL:
            end = self.end_date.get_date()
            if start is None:
                self.start_date.set_invalid(_(u'Invalid date'))
                return
            if end and start >= end:
                self._internal_set_end_date(start + datetime.timedelta(days=1))

            self.start_date.set_valid()

    def _on_end_date__changed(self, end_date):
        date_type = self.mode.get_selected_data()
        # We don't need to do anything for user day, since
        # this the end date widget is disabled
        if date_type == DateSearchFilter.Type.USER_DAY:
            pass
        # Make sure that we cannot select an end date before
        # the start date, be nice and decrease the start date if
        # the end date happen to be the same
        elif date_type == DateSearchFilter.Type.USER_INTERVAL:
            start = self.start_date.get_date()
            end = end_date.get_date()
            if end is None:
                self.end_date.set_invalid(_(u'Invalid date'))
            else:
                self.end_date.set_valid()

            if start and end and end <= start:
                self._internal_set_start_date(end - datetime.timedelta(days=1))


class ComboSearchFilter(SearchFilter):
    """
    - a label
    - a combo with a set of predefined item to select from
    """
    __gtype_name__ = 'ComboSearchFilter'

    def __init__(self, label='', values=None):
        """
        Create a new ComboSearchFilter object.
        :param label: label of the search filter
        :param values: items to put in the combo, see
            :class:`kiwi.ui.widgets.combo.ProxyComboBox.prefill`
        """
        self._block_updates = False
        SearchFilter.__init__(self, label=label)
        label = gtk.Label(label)
        self.pack_start(label, False, False)
        label.show()
        self.title_label = label

        # We create the mode, but it will only be added to this box when
        # enable_advanced is called
        self.mode = ProxyComboBox()
        self.mode.connect('content-changed', self._on_mode__content_changed)
        for option in (ComboEquals, ComboDifferent):
            self.add_option(option)
        self.mode.select_item_by_position(0)

        self.combo = ProxyComboBox()
        if values:
            self.update_values(values)
        self.combo.connect('content-changed', self._on_combo__content_changed)
        self.pack_start(self.combo, False, False, 6)
        self.combo.show()

    #
    # SearchFilter
    #

    def get_state(self):
        value = self.combo.get_selected_data()
        mode = self.mode.get_selected_data()
        state = NumberQueryState(filter=self, value=value, mode=mode.mode)
        if hasattr(value, 'id'):
            state.value_id = value.id
        return state

    def set_state(self, value, value_id=None, mode=None):
        if mode is None:
            mode = NumberQueryState.EQUALS
        if value_id is not None:
            for item in self.combo.get_model_items().values():
                if item is None:
                    continue
                if item.id == value_id:
                    value = item
                    break
        self.select(value)

    def update_values(self, values):
        self._block_updates = True
        self.combo.prefill(values)
        self._block_updates = False

    def get_title_label(self):
        return self.title_label

    def get_mode_combo(self):
        return self.combo

    def get_description(self):
        desc = ''
        data = self.combo.get_selected_data()
        if data is not None:
            desc += self.combo.get_selected_label()
            return '%s %s' % (self.title_label.get_text(), desc,)

    #
    # Public API
    #

    def add_option(self, option_type, position=0):
        """
        Adds an option
        :param option_type: option to add
        :type option_type: a :class:`ComboSearchOption` subclass
        """
        option = option_type()
        num = len(self.mode) + position
        self.mode.insert_item(num, option.name, option_type)

    def select(self, data):
        """
        selects an item in the combo
        :param data: what to select
        """
        self.combo.select(data)

    def enable_advanced(self):
        self.pack_start(self.mode, False, False, 6)
        self.reorder_child(self.mode, 1)
        self.mode.show()

    #
    # Callbacks
    #

    def _on_mode__content_changed(self, combo):
        if not self._block_updates:
            self.emit('changed')

    def _on_combo__content_changed(self, mode):
        if not self._block_updates:
            self.emit('changed')


class BoolSearchFilter(SearchFilter):
    """
    - a checkbutton
    - a label
    """
    __gtype_name__ = 'BoolSearchFilter'

    def __init__(self, label=''):
        """
        Create a new BoolSearchFilter object.
        :param label: label of the search filter
        """
        self._block_updates = False
        SearchFilter.__init__(self, label=label)

        self.button = ProxyCheckButton(label=label)
        self.button.connect('content-changed', self._on_button__content_changed)
        self.pack_start(self.button, False, False, 6)
        self.button.show()

        self.combo = False

    #
    # SearchFilter
    #

    def get_state(self):
        return BoolQueryState(filter=self,
                              value=self.button.read())

    def set_state(self, value):
        if isinstance(value, bool):
            self.button.set_active(value)
        elif value is None or value is ValueUnset:
            self.button.set_active(False)
        else:
            self.button.set_active(True)

    def get_title_label(self):
        return self.button.get_label()

    def get_description(self):
        return '%s: %s' % (self.get_label(), str(self.get_state()))

    def get_mode_combo(self):
        return None

    #
    # Public API
    #

    def check(self, data):
        self.button.set_active(True)

    def uncheck(self, data):
        self.button.set_active(False)

    #
    # Callbacks
    #

    def _on_button__content_changed(self, mode):
        if not self._block_updates:
            self.emit('changed')


class StringSearchFilter(SearchFilter):
    """
    Contains:

      - a label
      - an entry

    :ivar entry: the entry
    :ivar label: the label
    """
    def __init__(self, label, chars=0, container=None):
        """
        Create a new StringSearchFilter object.
        :param label: label of the search filter
        :param chars: maximum number of chars used by the search entry
        """
        self._container = container
        SearchFilter.__init__(self, label=label)
        self.title_label = gtk.Label(label)
        self.pack_start(self.title_label, False, False)
        self.title_label.show()

        self._options = {}
        self.mode = ProxyComboBox()
        self.mode.connect('content-changed', self._on_mode__content_changed)
        self.pack_start(self.mode, False, False, 6)

        self.entry = HintedEntry()
        self.entry.set_hint(_("Search"))
        self.entry.show_hint()
        self.entry.props.secondary_icon_sensitive = False
        data = environ.get_resource_string('stoq', 'pixmaps',
                                           'stoq-funnel-16x16.png')
        image = pixbuf_from_string(data)
        self.entry.set_icon_from_pixbuf(gtk.ENTRY_ICON_PRIMARY,
                                        image)
        self.entry.set_icon_tooltip_text(gtk.ENTRY_ICON_PRIMARY,
                                         _("Add a filter"))
        self.entry.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY,
                                       gtk.STOCK_CLEAR)
        self.entry.set_icon_tooltip_text(gtk.ENTRY_ICON_SECONDARY,
                                         _("Clear the search"))
        self.entry.connect("icon-release", self._on_entry__icon_release)
        self.entry.connect('activate', self._on_entry__activate)
        self.entry.connect('changed', self._on_entry__changed)
        if chars:
            self.entry.set_width_chars(chars)
        self.pack_start(self.entry, False, False, 6)
        self.entry.show()

        for option in (ContainsAll, ContainsExactly, DoesNotContain, IdenticalTo):
            self._add_option(option)
        self.mode.select_item_by_position(0)

    def _add_option(self, option_type, position=-2):
        option = option_type()
        num = abs(position)
        self.mode.insert_item(num, option.name, option_type)
        self._options[option_type] = option

    #
    # Callbacks
    #

    def _on_mode__content_changed(self, combo):
        self.emit('changed')

    def _on_entry__activate(self, entry):
        self.emit('changed')

    def _on_entry__changed(self, entry):
        entry.props.secondary_icon_sensitive = bool(entry.get_text())

    def _position_filter_menu(self, data):
        window = self.entry.get_icon_window(gtk.ENTRY_ICON_PRIMARY)
        x, y = window.get_origin()
        y += window.get_size()[1]
        border = self.entry.style_get_property('progress-border')
        if border is not None:
            y += border.bottom
        return (x, y, True)

    def _on_entry__icon_release(self, entry, icon_pos, event):
        if icon_pos == gtk.ENTRY_ICON_SECONDARY:
            entry.set_text("")
            entry.grab_focus()
            self.emit('changed')
        elif icon_pos == gtk.ENTRY_ICON_PRIMARY:
            # We don't need create popup filters if haven't search columns.
            if (not self._container or not hasattr(self._container, 'menu') or
                not self._container.menu):
                return
            self._container.menu.popup(None, None,
                                       self._position_filter_menu, 0, event.time)

    #
    # SearchFilter
    #

    def get_state(self):
        option = self.mode.get_selected_data()
        return StringQueryState(filter=self,
                                text=unicode(self.entry.get_text()),
                                mode=option and option.mode)

    def set_state(self, text, mode=None):
        self.entry.set_text(text)
        if mode is not None:
            self.mode.select_item_by_position(mode)

    def get_title_label(self):
        return self.title_label

    def get_mode_combo(self):
        return self.mode

    def get_description(self):
        desc = self.entry.get_text()
        if desc:
            mode = self.mode.get_selected_label()
            return '%s %s "%s"' % (self.title_label.get_text(), mode, desc,)

    #
    # Public API
    #

    def enable_advanced(self):
        # Do not show the funnel icon if its an advanced filter
        self.entry.set_icon_from_pixbuf(gtk.ENTRY_ICON_PRIMARY, None)
        self.mode.show()

    def set_label(self, label):
        self.title_label.set_text(label)


class NumberSearchFilter(SearchFilter):
    """
    A filter which helps you to search by a number interval.
    """
    __gtype_name__ = 'NumberSearchFilter'

    def __init__(self, label=''):
        """
        Create a new NumberSearchFilter object.
        :param label: name of the search filter
        """

        self._options = {}

        SearchFilter.__init__(self, label=label)
        self.title_label = gtk.Label(label)
        self.title_label.set_alignment(1.0, 0.5)
        self.pack_start(self.title_label, False, False)
        self.title_label.show()

        self.mode = ProxyComboBox()
        self.mode.connect('content-changed', self._on_mode__content_changed)
        self.pack_start(self.mode, False, False, 6)
        self.mode.show()

        self.start = gtk.SpinButton(climb_rate=1.0)
        self.start.get_adjustment().step_increment = 1.0
        self.start.set_range(-MAX_INT - 1, MAX_INT)
        self.pack_start(self.start, False, False, 6)
        self.start.show()
        self.start.connect_after('activate', self._on_entry__activate)

        self.and_label = gtk.Label(_("And"))
        self.pack_start(self.and_label, False, False)
        self.and_label.show()

        self.end = gtk.SpinButton(climb_rate=1.0)
        self.end.get_adjustment().step_increment = 1.0
        self.end.set_range(-MAX_INT - 1, MAX_INT)
        self.pack_start(self.end, False, False, 6)
        self.end.show()
        self.end.connect_after('activate', self._on_entry__activate)

        for option in (LowerThan, EqualsTo, GreaterThan, Between):
            self.add_option(option)

        self.mode.select_item_by_position(0)

    def set_digits(self, digits):
        """
        Number of decimal place to be displayed
        :param digits: number of decimal places
        """
        self.start.set_digits(digits)
        self.end.set_digits(digits)

    #
    #   Private
    #

    def _update_visibility(self):
        option = self.mode.get_selected_data()
        numbers = option.numbers
        if numbers == 0:
            self.start.hide()
            self.and_label.hide()
            self.end.hide()
        elif numbers == 1:
            self.start.show()
            self.and_label.hide()
            self.end.hide()
        elif numbers == 2:
            self.start.show()
            self.and_label.show()
            self.end.show()

    #
    #   Callbacks
    #

    def _on_entry__activate(self, entry):
        self.emit('changed')

    def _on_mode__content_changed(self, combo):
        self._update_visibility()
        self.emit('changed')

    #
    #   SearchFilter
    #

    def get_state(self):
        # Using Decimals for better precision.
        start_value = Decimal("%.2f" % self.start.get_value())
        end_value = Decimal("%.2f" % self.end.get_value())
        option = self.mode.get_selected_data()

        start, end = option().get_interval(start_value, end_value)
        return NumberIntervalQueryState(filter=self, start=start, end=end)

    def set_state(self, start, end):
        self.start.set_value(start)
        self.end.set_value(end)

    def get_title_label(self):
        return self.title_label

    def get_mode_combo(self):
        return self.mode

    def get_description(self):
        desc = ''
        option = self.mode.get_selected_data()
        if option is not None:
            desc += option.name
            if option.numbers > 0:
                start = self.start.get_value_as_int()
                if option.numbers == 1:
                    desc += ' %d' % start
                elif option.numbers == 2:
                    end = self.end.get_value_as_int()
                    desc += ' %d %s %d' % (start, self.and_label.get_text(), end,)
        if desc:
            return '%s %s' % (self.get_title_label().get_text(), desc)

    #
    #   Public API
    #

    def add_option(self, option_type, position=-2):
        """
        Adds a date option
        :param option_type: option to add
        :type option_type: a :class:`NumberSearchOption` subclass
        """
        option = option_type()
        num = len(self.mode) + position
        self.mode.insert_item(num, option.name, option_type)
        self._options[option_type] = option


class MultiSearchFilter(SearchFilter):
    """A multi object search filter, containing:

      - a label
      - a multicombo widget
    """

    def __init__(self, label, items):
        super(MultiSearchFilter, self).__init__(label=label)

        self._title_label = gtk.Label(label)
        self.pack_start(self._title_label, False, False)

        self._combo = ProxyMultiCombo(width=400)
        self._combo.prefill(items)
        self._combo.connect('content-changed', self._on_combo__content_changed)
        self.pack_start(self._combo, False, False, 6)

        self.show_all()

    #
    # SearchFilter
    #

    def set_label(self, label):
        super(MultiSearchFilter, self).set_label(label)
        self._title_label.set_text(label)

    def get_title_label(self):
        return self._title_label

    def get_state(self):
        return MultiQueryState(filter=self,
                               values=self._combo.get_selection_data())

    def set_state(self, values):
        self._combo.clear()
        self._combo.add_selection_by_data(values)

    def get_mode_combo(self):
        return None

    def get_description(self):
        return '%s: [%s]' % (', '.join(self._combo.get_selection_label()), )

    #
    #  Callbacks
    #

    def _on_combo__content_changed(self, combo):
        self.emit('changed')

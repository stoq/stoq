# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Base classes for application's GUI """

import logging

import gtk
from kiwi.ui.delegates import GladeDelegate
from stoqlib.api import api
from stoqlib.domain.inventory import Inventory
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.spreadsheetexporterdialog import SpreadSheetExporter
from stoqlib.gui.events import ApplicationSetupSearchEvent
from stoqlib.gui.search.searchslave import SearchSlave
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.widgets.lazyobjectlist import LazyObjectModel
from stoqlib.lib.decorators import cached_function
from stoqlib.lib.translation import stoqlib_gettext as _

log = logging.getLogger(__name__)


class ShellApp(GladeDelegate):
    """Base class for shell applications.

    The main use is to interact with a shell window and reduce
    duplication between other applications.
    """

    domain = 'stoq'

    #: This attribute is used when generating titles for applications.
    #: It's also useful if we get a list of available applications with
    #: the application names translated. This list is going to be used when
    #: creating new user profiles.
    app_title = None

    #: name of the application, 'pos', 'payable', etc
    app_name = None

    #: If this application has a search like interface
    search = None

    #: This dictionary holds information about required permissions to access
    #: certain actions. Keys should be the name of the action (for instance
    #: SearchEmployess), and the value should be a tuple with the permission key
    #: (domain object or action identifier) and the required permission. In this
    #: case: ('Employee', perm.PERM_SEARCH). See <stoqlib.lib.permissions>
    action_permissions = {}

    #: The spec for store.find() to perform the search on
    search_spec = None

    #: Label left of the search entry
    search_label = _('Search:')

    #: the report class for printing the object list embedded on app.
    report_table = None

    def __init__(self, window, store=None):
        if store is None:
            store = api.get_default_store()
        self.store = store
        self.window = window

        self._sensitive_group = dict()
        self.help_ui = None
        self.uimanager = self.window.uimanager

        # FIXME: These two should probably post-__init__, but
        #        that breaks date_label in the calender app
        self._create_search()
        self.create_actions()
        GladeDelegate.__init__(self,
                               gladefile=self.gladefile,
                               toplevel_name=self.toplevel_name)
        self._attach_search()
        self.create_ui()

    def _create_search(self):
        if self.search_spec is None:
            return
        self.columns = self.get_columns()
        ApplicationSetupSearchEvent.emit(self)
        self.search = SearchSlave(self.columns,
                                  store=self.store,
                                  restore_name=self.__class__.__name__,
                                  search_spec=self.search_spec)

    def _attach_search(self):
        if self.search_spec is None:
            return
        self.search.enable_advanced_search()
        self.attach_slave('search_holder', self.search)
        search_filter = self.search.get_primary_filter()
        search_filter.set_label(self.search_label)
        self.create_filters()
        self.search.restore_filter_settings('app-ui', self.app_name)
        self.search.focus_search_entry()

        # FIXME: Remove and use search directly instead of the result view
        self.results = self.search.result_view

    def _display_open_inventory_message(self):
        msg = _(u'There is an inventory process open at the moment.\n'
                'While that inventory is open, you will be unable to do '
                'operations that modify your stock.')
        self.inventory_bar = self.window.add_info_bar(gtk.MESSAGE_WARNING, msg)

    #
    # Overridables
    #

    def create_actions(self):
        """This is called before the BaseWindow constructor, so we
        can create actions that can be autoconnected.
        The widgets and actions loaded from builder files are not set
        yet"""

    def create_ui(self):
        """This is called when the UI such as GtkWidgets should be
        created. Glade widgets are now created and can be accessed
        in the instance.
        """

    def activate(self, refresh=True):
        """This is when you switch to an application.

        You should setup widget sensitivity here and refresh lists etc

        :param refresh: if we should refresh the search
        """

    def setup_focus(self):
        """Define this method on child when it's needed.
        This is for calling grab_focus(), it's called after the window
        is shown. focus chains should be created in create_ui()"""

    def get_title(self):
        # This method must be redefined in child when it's needed
        branch = api.get_current_branch(self.store)
        return _('[%s] - %s') % (branch.get_description(), self.app_title)

    def can_change_application(self):
        """Define if we can change the current application or not.

        :returns: True if we can change the application, False otherwise.
        """
        return True

    def can_close_application(self):
        """Define if we can close the current application or not.

        :returns: True if we can close the application, False otherwise.
        """
        return True

    def set_open_inventory(self):
        """ Subclasses should overide this if they call
        :obj:`.check_open_inventory`.

        This method will be called it there is an open inventory, so the
        application can disable some funcionalities
        """
        raise NotImplementedError

    def new_activate(self):
        """Called when the New toolbar item is activated"""
        raise NotImplementedError

    def search_activate(self):
        """Called when the Search toolbar item is activated"""
        raise NotImplementedError

    def print_activate(self):
        """Called when the Print toolbar item is activated"""
        if self.search_spec is None:
            raise NotImplementedError

        if self.results.get_selection_mode() == gtk.SELECTION_MULTIPLE:
            results = self.results.get_selected_rows() or list(self.search.get_last_results())
        else:
            # There are not multiple selection.
            # We should print the entire list.
            results = list(self.search.get_last_results())
        self.print_report(self.report_table, self.results, results)

    def export_spreadsheet_activate(self):
        """Called when the Export menu item is activated"""
        if self.search_spec is None:
            raise NotImplementedError

        model = self.results.get_model()
        if isinstance(model, LazyObjectModel):
            model.load_items_from_results(0, model._count)

        sse = SpreadSheetExporter()
        sse.export(object_list=self.results,
                   name=self.app_name,
                   filename_prefix=self.app_name)

    def create_filters(self):
        """Implement this to provide filters for the search container"""

    def search_completed(self, results, states):
        """Implement this if you want to know when a search has
        been completed.

        :param results: the search results
        :param states: search states used to construct the search query search
        """

    #
    # Public API
    #

    def add_ui_actions(self, ui_string, actions, name='Actions',
                       action_type='normal', filename=None):
        return self.window.add_ui_actions(ui_string=ui_string,
                                          actions=actions,
                                          name=name,
                                          action_type=action_type,
                                          filename=filename,
                                          instance=self)

    def add_tool_menu_actions(self, actions):
        return self.window.add_tool_menu_actions(actions=actions)

    def add_columns(self, columns):
        """Add some columns to the default ones.

        Note that this method must be called during the setup of this search,
        which right now is only possible for those who capture the
        `<stoqlib.gui.events.ApplicationSetupSearchEvent>`
        """
        self.columns.extend(columns)

    def set_help_section(self, label, section):
        self.window.set_help_section(label=label,
                                     section=section)

    def get_statusbar_message_area(self):
        return self.window.statusbar.message_area

    def print_report(self, report_class, *args, **kwargs):
        filters = self.search.get_search_filters()
        if filters:
            kwargs['filters'] = filters

        print_report(report_class, *args, **kwargs)

    def set_sensitive(self, widgets, value):
        """Set the *widgets* sensitivity based on *value*

        If a sensitive group was registered for any widget,
        it's validation function will be tested and, if ``False``
        is returned, it will be set insensitive, ignoring *value*

        :param widgets: a list of widgets
        :param value: either `True` or `False`
        """
        # FIXME: Maybe this should ne done on kiwi?
        for widget in widgets:
            sensitive = value

            for validator in self._sensitive_group.get(widget, []):
                if not validator[0](*validator[1]):
                    sensitive = False
                    break

            widget.set_sensitive(sensitive)

    def register_sensitive_group(self, widgets, validation_func, *args):
        """Register widgets on a sensitive group.

        Everytime :obj:`.set_sensitive()` is called, if there is any
        validation function for a given widget on sensitive group,
        then that will be used to decide if it gets sensitive or
        insensitive.

        :param widgets: a list of widgets
        :param validation_func: a function for validation. It should
            return either ``True`` or ``False``.
        :param args: args that will be passed to *validation_func*
        """
        assert callable(validation_func)

        for widget in widgets:
            validators = self._sensitive_group.setdefault(widget, set())
            validators.add((validation_func, args))

    def run_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for running dialogs. """
        return run_dialog(dialog_class, self, *args, **kwargs)

    @cached_function()
    def has_open_inventory(self):
        return Inventory.has_open(self.store,
                                  api.get_current_branch(self.store))

    def check_open_inventory(self):
        """Checks if there is an open inventory.

        In the case there is one, will call set_open_inventory (subclasses
        should implement it).

        Returns True if there is an open inventory. False otherwise
        """
        inventory_bar = getattr(self, 'inventory_bar', None)

        if self.has_open_inventory():
            if inventory_bar:
                inventory_bar.show()
            else:
                self._display_open_inventory_message()
            self.set_open_inventory()
            return True
        elif inventory_bar:
            inventory_bar.hide()
            return False

    # FIXME: Most of these should be removed and access the search API
    #        directly, eg, self.search.clear() etc

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM,
                   columns=None, callback=None):
        """
        See :class:`SearchSlave.add_filter`
        """
        self.search.add_filter(search_filter, position, columns, callback)

    def set_text_field_columns(self, columns):
        """
        See :class:`SearchSlave.set_text_field_columns`
        """
        self.search.set_text_field_columns(columns)

    def create_branch_filter(self, label=None, column=None):
        branch_filter = self.search.create_branch_filter(label, column)
        # If there is only one item in the combo, lets hide it.
        if len(branch_filter.combo) == 1:
            branch_filter.hide()
        return branch_filter

    def refresh(self, rollback=True):
        """
        See :class:`stoqlib.gui.search.searchslave.SearchSlave.refresh`
        """
        # Since the store here is actually a transaction and the items
        # on it can be changed from another station, do a rollback so
        # the items get reloaded, avoiding cache problems
        # Note that this gets mocked on tests to not do the rollback
        if rollback:
            self.store.rollback(close=False)
        self.search.refresh()

    def clear(self):
        """
        See :class:`stoqlib.gui.search.searchslave.SearchSlave.clear`
        """
        self.search.clear()

    def select_result(self, result):
        """Select the object in the result list

        If the object is not in the list (filtered out, for instance), no error
        is thrown and nothing is selected
        """
        try:
            self.results.select(result)
        except ValueError:
            pass

    #
    # Callbacks
    #

    def on_search__search_completed(self, search, results, states):
        self.search_completed(results, states)

        has_results = len(results)
        for widget in [self.window.Print,
                       self.window.ExportSpreadSheet]:
            widget.set_sensitive(has_results)
        self.search.save_filter_settings('app-ui', self.app_name)

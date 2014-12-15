# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2012 Async Open Source
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
##

"""Stoqlib API

Singleton object which makes it easier to common stoqlib APIs without
having to import their symbols.
"""
import operator
import sys

import glib
from kiwi.component import get_utility
from twisted.internet.defer import inlineCallbacks, returnValue

from stoqlib.database.runtime import (new_store,
                                      get_default_store)
from stoqlib.database.runtime import (get_current_branch,
                                      get_current_station, get_current_user)
from stoqlib.database.settings import db_settings
from stoqlib.domain.person import Branch
from stoqlib.gui.events import CanSeeAllBranches
from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.interfaces import IStoqConfig
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.settings import get_settings
from stoqlib.lib.translation import locale_sorted, stoqlib_gettext as _
from stoqlib.l10n.l10n import get_l10n_field


class StoqAPI(object):
    def get_default_store(self):
        return get_default_store()

    def new_store(self):
        return new_store()

    def get_current_branch(self, store):
        return get_current_branch(store)

    def get_current_station(self, store):
        return get_current_station(store)

    def get_current_user(self, store):
        return get_current_user(store)

    @property
    def config(self):
        return get_utility(IStoqConfig)

    @property
    def db_settings(self):
        return db_settings

    @property
    def user_settings(self):
        return get_settings()

    def is_developer_mode(self):
        return is_developer_mode()

    @property
    def async(self):
        """Async API for dialog, it's built on-top of
        twisted.It is meant to be used in the following way::

          @api.async
          def _run_a_dialog(self):
              model = yield run_dialog(SomeDialog, parent, store)

        If the function returns a value, you need to use
        :py:func:`~stoqlib.api.StoqAPI.asyncReturn`, eg::

          api.asyncReturn(model)

        :returns: a generator
        """

        return inlineCallbacks

    def asyncReturn(self, value=None):
        """An async API that also returns a value,
        see :py:func:`~stoqlib.api.StoqAPI.async` for more information.

        :param value: the return value, defaults to None
        :returns: a twisted deferred
        """
        return returnValue(value)

    def get_l10n_field(self, field_name, country=None):
        return get_l10n_field(field_name, country=country)

    def for_combo(self, resultset, attr=None, empty=None, sorted=True):
        """
        Prepares the result of a table for inserting into a combo.
        Formats the item and sorts them according to the current locale

        :param resultset: a resultset
        :param attr: attribute to use instead of :py:class:`~stoqlib.domain.interfaces.IDescribable`
        :param empty: if set, add an initial None item with this parameter as
          a label

        Example::

          categories = self.store.find(SellableCategory)
          self.category_combo.prefill(api.for_combo(categories,
                                      attr='full_description'))
        """
        if attr is not None:
            items = [(getattr(obj, attr), obj) for obj in resultset]
        else:
            # If attr is not specified, the objects in the resultset must
            # implement IDescribable
            items = [(obj.get_description(), obj) for obj in resultset]

        if sorted:
            items = locale_sorted(items, key=operator.itemgetter(0))

        if empty is not None:
            items.insert(0, (empty, None))
        return items

    def for_person_combo(self, resultset):
        """
        This is similar to :py:func:`~stoqlib.api.StoqAPI.for_combo` but
        takes a class that references a :py:class:`~stoqlib.domain.person.Person`,
        such as a :py:class:`~stoqlib.domain.person.Client`,
        :py:class:`~stoqlib.domain.person.Company`,
        :py:class:`~stoqlib.domain.person.Supplier` etc.

        :param resultset: a resultset

        Example::

          suppliers = Supplier.get_active_suppliers(self.store)
          self.supplier.prefill(api.for_person_combo(suppliers))
        """
        from stoqlib.domain.person import Person
        from storm import Undef
        from storm.expr import Eq
        store = resultset._store
        facet = resultset._find_spec.default_cls
        where = resultset._where

        # This is fetching all persons to cache the objects and avoid extra
        # queries when constructing the combo strings.
        resultset = store.find((Person, facet), Person.id == facet.person_id,
                               Eq(Person.merged_with_id, None))
        if where is not Undef:
            resultset = resultset.find(where)

        items = [(obj[1].get_description(), obj[1]) for obj in resultset]
        # FIXME: A combo only changes to data mode (the one that it
        # returns an object insted of the label) when prefilled with
        # objects. Prefilling with this fake data will prevent the problem
        # from happening. We should fix this on kiwi later
        if not items:
            return [('', None)]

        return locale_sorted(items, key=operator.itemgetter(0))

    def can_see_all_branches(self):
        can_see = CanSeeAllBranches.emit()
        if can_see is not None:
            return can_see
        return not api.sysparam.get_bool('SYNCHRONIZED_MODE')

    def get_branches_for_filter(self, store, use_id=False):
        """Returns a list of branches to be used in a combo.

        :param use_id: If True, we will return the options using the object id
          instead of the real object.
        """
        if not api.can_see_all_branches():
            current = self.get_current_branch(store)
            if use_id:
                value = current.id
            else:
                value = current
            items = [(current.get_description(), value)]
        else:
            branches = Branch.get_active_branches(store)
            if use_id:
                items = [(b.get_description(), b.id) for b in branches]
            else:
                items = [(b.get_description(), b) for b in branches]
            items.insert(0, (_("Any"), None))
        return items

    def escape(self, string):
        """Escapes the text and makes it suitable for use with a
        PangoMarkup, usually via Label.set_markup()"""
        if string is None:
            string = ''
        return unicode(glib.markup_escape_text(string))

    def prepare_test(self):
        """Prepares to run a standalone test.
        This initializes Stoq and creates a store and returns
        an example creator.

        :returns: an :py:class:`~stoqlib.domain.exampledata.ExampleCreator`
        """
        # FIXME: We need to move this into stoqlib
        from stoq.gui.shell.bootstrap import boot_shell
        from stoq.lib.options import get_option_parser
        parser = get_option_parser()
        options = parser.parse_args(sys.argv[1:])[0]
        options.wizard = False
        options.splashscreen = False
        options.autoreload = False
        options.login_username = u'admin'
        options.non_fatal_warnings = False
        shell = boot_shell(options, initial=False)
        shell._dbconn.connect()
        shell._do_login()

        from stoqlib.domain.exampledata import ExampleCreator
        ec = ExampleCreator()
        store = self.new_store()
        ec.set_store(store)
        return ec

api = StoqAPI()
api.sysparam = sysparam

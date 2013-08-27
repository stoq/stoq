# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2013 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Tests for :mod:`stoqlib.gui.base.lists`"""

import gtk
from kiwi.python import Settable
from kiwi.ui.objectlist import Column
import mock
from zope.interface import implementer

from stoqlib.database.properties import UnicodeCol
from stoqlib.database.runtime import StoqlibStore
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable
from stoqlib.gui.base.lists import ModelListSlave, SimpleListDialog
from stoqlib.gui.test.uitestutils import GUITest


@implementer(IDescribable)
class _TestModel(Domain):
    __storm_table__ = '_test_model'

    unicode_var = UnicodeCol()

    def get_description(self):
        return self.unicode_var


class _ModelListSlave(ModelListSlave):
    model_type = _TestModel
    columns = [Column('unicode_var', title='Unicode var', data_type=str,
                      expand=True, sorted=True)]


class TestModelListSlave(GUITest):
    """Tests for :class:`stoqlib.gui.base.lists.ModelListSlave`"""

    def setUp(self):
        super(TestModelListSlave, self).setUp()

        self.store.execute("""
            DROP TABLE IF EXISTS _test_model;
            CREATE TABLE _test_model (
                id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
                te_id bigint UNIQUE REFERENCES transaction_entry(id) default new_te(),

                unicode_var text
            );
            CREATE RULE update_te AS ON UPDATE TO _test_model DO ALSO SELECT update_te(old.te_id);
        """)

        self.models = set([
            _TestModel(store=self.store, unicode_var=u'XXX'),
            _TestModel(store=self.store, unicode_var=u'YYY'),
        ])
        self.store.commit(close=False)

    def test_populate(self):
        list_slave = _ModelListSlave(store=self.store)
        # Make sure the list was populated right
        self.assertEqual(set(list_slave.listcontainer.list), self.models)

        # Make sure populate method is returning all models
        self.assertEqual(set(list_slave.populate()), self.models)
        self.assertEqual(StoqlibStore.of(list_slave.populate()[0]), self.store)

    @mock.patch('kiwi.ui.listdialog.yesno')
    def test_remove_item(self, yesno):
        yesno.return_value = gtk.RESPONSE_OK

        list_slave = _ModelListSlave(store=self.store)
        item_to_remove = self.store.find(_TestModel, unicode_var=u'XXX').one()

        self.assertNotSensitive(list_slave.listcontainer, ['remove_button'])
        list_slave.listcontainer.list.select(item_to_remove)
        self.assertSensitive(list_slave.listcontainer, ['remove_button'])

        original_dm = list_slave.delete_model
        with mock.patch.object(list_slave, 'delete_model') as dm:
            dm.side_effect = original_dm
            self.click(list_slave.listcontainer.remove_button)
            args, kwargs = dm.call_args
            model, store = args

            self.assertTrue(isinstance(model, _TestModel))
            self.assertEqual(self.store.fetch(model), item_to_remove)
            self.assertTrue(isinstance(store, StoqlibStore))
            self.assertNotEqual(store, self.store)

        models = self.models - set([item_to_remove])
        self.assertEqual(set(list_slave.listcontainer.list), models)
        self.assertEqual(set(list_slave.populate()), models)
        self.assertEqual(StoqlibStore.of(list_slave.populate()[0]), self.store)

    @mock.patch('kiwi.ui.listdialog.yesno')
    def test_remove_item_reuse_store(self, yesno):
        yesno.return_value = gtk.RESPONSE_OK

        list_slave = _ModelListSlave(store=self.store, reuse_store=True)
        item_to_remove = self.store.find(_TestModel, unicode_var=u'XXX').one()

        self.assertNotSensitive(list_slave.listcontainer, ['remove_button'])
        list_slave.listcontainer.list.select(item_to_remove)
        self.assertSensitive(list_slave.listcontainer, ['remove_button'])

        original_dm = list_slave.delete_model
        with mock.patch.object(list_slave, 'delete_model') as dm:
            dm.side_effect = original_dm
            self.click(list_slave.listcontainer.remove_button)
            args, kwargs = dm.call_args
            model, store = args

            self.assertEqual(model, item_to_remove)
            self.assertIs(store, self.store)

        models = self.models - set([item_to_remove])
        self.assertEqual(set(list_slave.listcontainer.list), models)
        self.assertEqual(set(list_slave.populate()), models)
        self.assertEqual(StoqlibStore.of(list_slave.populate()[0]), self.store)


class TestSimpleListDialog(GUITest):
    """Tests for :class:`stoqlib.gui.base.lists.SimpleListDialog`"""

    def _create_dialog(self):
        objs = []
        for i in range(10):
            objs.append(Settable(
                id=i,
                desc="Object %d" % i,
            ))

        columns = [
            Column('id', title='#', data_type=int),
            Column('desc', title='Description', data_type=str, expand=True),
        ]

        return SimpleListDialog(columns=columns, objects=objs)

    def test_dialog(self):
        dialog = self._create_dialog()
        self.check_dialog(dialog, 'dialog-simple-list')

    def test_confirm(self):
        dialog = self._create_dialog()
        with mock.patch.object(dialog, 'close') as close:
            self.click(dialog.ok_button)
            close.assert_called_once_with()

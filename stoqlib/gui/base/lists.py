# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" List management for common dialogs.  """

import gtk
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.listdialog import ListSlave
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.domain.interfaces import IDescribable
from stoqlib.exceptions import SelectionError, StoqlibError
from stoqlib.gui.base.dialogs import run_dialog, get_dialog, BasicDialog
from stoqlib.gui.base.search import StoqlibSearchSlaveDelegate
from stoqlib.gui.base.wizards import BaseWizard
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext, stoqlib_ngettext
from stoqlib.lib.message import yesno

_ = stoqlib_gettext


class ModelListSlave(ListSlave):

    def __init__(self, columns=None, conn=None,
                 orientation=gtk.ORIENTATION_VERTICAL):
        """
        Create a new ModelListDialog object.
        @param conn: A database connection
        """
        if not conn:
            conn = api.get_connection()
        self.conn = conn

        self._model_type = None
        self._reuse_transaction = False
        self._editor_class = None
        columns = columns or self.get_columns()
        ListSlave.__init__(self, columns, orientation)

    def _delete_with_transaction(self, model, trans):
        self.delete_model(model, trans)

    def _delete_model(self, model):
        if self._reuse_transaction:
            self._delete_with_transaction(model, self._reuse_transaction)
        else:
            trans = api.new_transaction()
            self._delete_with_transaction(model, trans)
            trans.commit(close=True)

    def _prepare_run_editor(self, item):
        if self._reuse_transaction:
            self._reuse_transaction.savepoint('before_run_editor')
            retval = self.run_editor(self._reuse_transaction, item)
            if not retval:
                self._reuse_transaction.rollback_to_savepoint('before_run_editor')
        else:
            # 1) Create a new transaction
            # 2) Fetch the model from that transactions POW
            # 3) Sent it to the editor and run the editor
            # 4) If the return value is not None fetch it in the
            #    original connection (eg, self.conn)
            # 5) Return the value, so it can be populated by the list
            trans = api.new_transaction()
            if item is not None:
                model = trans.get(item)
            else:
                model = None
            retval = self.run_editor(trans, model)
            api.finish_transaction(trans, retval)
            if retval:
                retval = self._model_type.get(retval.id, connection=self.conn)
            trans.close()
        return retval

    #
    # ListSlave
    #

    def populate(self):
        if self._reuse_transaction:
            conn = self._reuse_transaction
        else:
            conn = self.conn
        return self.model_type.select(connection=conn)

    def add_item(self):
        return self._prepare_run_editor(None)

    def remove_item(self, item):
        retval = self.listcontainer.default_remove(
            IDescribable(item).get_description())
        if retval:
            # Remove the list before deleting it because it'll be late
            # afterwards, the object is invalid and SQLObject will complain
            self.remove_list_item(item)
            self._delete_model(item)
        return False

    def edit_item(self, item):
        return bool(self._prepare_run_editor(item))

    #
    # Public API
    #

    def set_model_type(self, model_type):
        """Set the type of the model this slave is containing
        @param model_type: the model type
        """
        self._model_type = model_type

    def set_editor_class(self, editor_class):
        """Set the editor class which will be used to modify
        the mode of this slave
        @param editor_class: the editor class
        """
        self._editor_class = editor_class

    def set_reuse_transaction(self, trans):
        """
        Reuse the transaction.
        @param reuse_transaction: a transaction
        """
        self._reuse_transaction = trans

    def run_dialog(self, dialog_class, *args, **kwargs):
        """A special variant of run_dialog which deletes objects
        when a transaction is reused, it's safe to use when it's disabled,
        so always use this in your run_editor hook
        """
        dialog = get_dialog(self, dialog_class, *args, **kwargs)

        retval = run_dialog(dialog, parent=self)
        if not retval:
            # We must return None because of ListDialog's add-item signal
            # expects that
            retval = None

        return retval

    #
    # Hooks
    #

    def run_editor(self, trans, model):
        """This can be override by a subclass who wants to send in
        custom arguments to the editor.
        """
        if self._editor_class is None:
            raise ValueError("editor_class cannot be None in %s" % (
                type(self).__name__))

        return self.run_dialog(
            self._editor_class,
            conn=trans, model=model)

    def delete_model(self, model, trans):
        """
        Deletes the model in a transaction.
        This can be overriden by a subclass which is useful when
        you have foreign keys which depends on this class.
        @param model: model to delete
        @param trans: the transaction to delete the model within
        """
        self._model_type.delete(model.id, connection=trans)


class ModelListDialog(gtk.Dialog, ModelListSlave):
    """A dialog which displays all items in a table and allows you to
    add and remove items from it

    @cvar model_type: an ORMObject for the table we want to modify, must
      implement the IDescribable interface.
    @cvar columns: a list of L{kiwi.ui.objectlist.Columns}
    @cvar editor_class: class used to edit the model, must take the
      constructor arguments (conn, model)
    @cvar size: a two sized tuple;  (width, height) or None
    @cvar title: window title
    """
    model_type = None
    editor_class = None
    columns = None
    size = None
    title = None

    def __init__(self, conn=None):
        if self.model_type is None:
            raise TypeError("%s must define a model_type class attribute" %
                            type(self).__name__)
        if not IDescribable.implementedBy(self.model_type):
            raise TypeError("%s must provide the IDescribable interface" %
                            self.model_type.__name__)

        gtk.Dialog.__init__(self)
        if self.size:
            self.set_size_request(*self.size)
        if self.title:
            self.set_title(self.title)
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        ModelListSlave.__init__(self, self.columns)
        self.set_model_type(self.model_type)
        self.set_editor_class(self.editor_class)
        self.vbox.pack_start(self.listcontainer)


class AdditionListSlave(StoqlibSearchSlaveDelegate):
    """A slave that offers a simple list and its management.

    This slave also has the option to display a small message right next to the
    buttons
    """

    toplevel_name = gladefile = 'AdditionListSlave'
    widgets = ('add_button',
               'delete_button',
               'klist',
               'list_vbox',
               'edit_button')
    gsignal('on-edit-item', object)
    gsignal('on-add-item', object)
    gsignal('before-delete-items', object)
    gsignal('after-delete-items')

    def __init__(self, conn, columns=None, editor_class=None,
                 klist_objects=None, visual_mode=False, restore_name=None):
        """ Creates a new AdditionListSlave object

        @param conn:          a connection
        @param columns:       column definitions
        @type columns:        sequence of L{kiwi.ui.widgets.list.Columns}
        @param editor_class:  the window that is going to be open when user
                              clicks on add_button or edit_button.
        @type: editor_class:  a L{stoqlib.gui.editors.BaseEditor} subclass
        @param klist_objects: initial objects to insert into the list
        @param visual_mode:   if we are working on visual mode, that means,
                              not possible to edit the model on this object
        type visual_mode:     bool
        @param restore_name:  the name used to save and restore the columns
                              on a cache system (e.g. pickle)
        @type restore_name:   basestring
        """
        columns = columns or self.get_columns()
        StoqlibSearchSlaveDelegate.__init__(self, columns=columns,
                                            restore_name=restore_name)
        if not self._columns:
            raise StoqlibError("columns must be specified")
        self.visual_mode = visual_mode
        self.conn = conn
        self.set_editor(editor_class)
        self._editor_kwargs = dict()
        self._can_edit = True
        self._callback_id = None
        if self.visual_mode:
            self.hide_add_button()
            self.hide_edit_button()
            self.hide_del_button()
        items = klist_objects or self.get_items()
        self._setup_klist(items)
        self._update_sensitivity()

    def _setup_klist(self, klist_objects):
        self.klist.set_columns(self._columns)
        self.klist.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self.klist.add_list(klist_objects)

    def _update_sensitivity(self, *args):
        if self.visual_mode:
            return
        can_delete = _can_edit = True
        objs = self.get_selection()
        if not objs:
            _can_edit = can_delete = False
        elif len(objs) > 1:
            _can_edit = False

        self.add_button.set_sensitive(True)
        self.edit_button.set_sensitive(_can_edit)
        self.delete_button.set_sensitive(can_delete)

    def _edit_model(self, model=None):
        edit_mode = model
        result = self.run_editor(model)

        if not result:
            return

        if edit_mode:
            self.emit('on-edit-item', result)
            self.klist.update(result)
        else:
            self.klist.append(result)
            # Emit the signal after we added the item to the list to be able to
            # check the length of the list in our validation callbacks.
            self.emit('on-add-item', result)

        # As we have a selection extended mode for kiwi list, we
        # need to unselect everything before select the new instance.
        self.klist.unselect_all()
        self.klist.select(result)
        self._update_sensitivity()

    def _edit(self):
        if not self._can_edit:
            return
        objs = self.get_selection()
        qty = len(objs)
        if qty != 1:
            raise SelectionError(
                ("Please select only one item before choosing Edit."
                   "\nThere are currently %d items selected") % qty)
        self._edit_model(objs[0])

    def _clear(self):
        objs = self.get_selection()
        qty = len(objs)
        if qty < 1:
            raise SelectionError('There are no objects selected')

        msg = stoqlib_ngettext(
            _('Delete this item?'),
            _('Delete these %d items?') % qty,
            qty)
        delete_label = stoqlib_ngettext(
            _("Delete item"),
            _("Delete items"),
            qty)

        keep_label = stoqlib_ngettext(
            _("Keep it"),
            _("Keep them"),
            qty)
        if yesno(msg, gtk.RESPONSE_NO, keep_label, delete_label):
            return
        self.emit('before-delete-items', objs)
        if qty == len(self.klist):
            self.klist.clear()
        else:
            for obj in objs:
                self.klist.remove(obj)
        self.klist.unselect_all()
        self._update_sensitivity()
        self.emit('after-delete-items')

    #
    # Hooks
    #

    def get_items(self):
        return []

    def get_columns(self):
        raise NotImplementedError("get_columns must be implemented in "
                                  "subclasses")

    def run_editor(self, model):
        """This can be overriden to provide a custom run_dialog line,
        or a conversion function for the model
        """
        if self._editor_class is None:
            raise TypeError(
                "%s cannot create or edit items without the editor_class "
                "argument set" % (self.__class__.__name__))

        self.conn.savepoint('before_run_editor')
        retval = run_dialog(self._editor_class, None, conn=self.conn,
                          model=model, **self._editor_kwargs)
        if not retval:
            self.conn.rollback_to_savepoint('before_run_editor')
        return retval

    def delete_model(self, model):
        """Deletes a model, can be overridden in subclass
        @param model: model to delete
        """
        model.__class__.delete(model.id, connection=self.conn)

    #
    # Public API
    #

    def register_editor_kwargs(self, **kwargs):
        self._editor_kwargs = kwargs

    def set_message(self, message, details_callback=None):
        """Display a simple message on a label, next to the add, edit, delete buttons
        """
        self.message_hbox.set_visible(True)
        self.message_details_button.set_visible(bool(details_callback))
        if details_callback:
            if self._callback_id:
                self.message_details_button.disconnect(self._callback_id)
            self._callback_id = self.message_details_button.connect(
                                                'clicked', details_callback)
        self.message_label.set_markup(message)

    def clear_message(self):
        self.message_hbox.set_visible(False)

    def get_selection(self):
        # XXX: add get_selected_rows and raise exceptions if not in the
        #      right mode
        if self.klist.get_selection_mode() == gtk.SELECTION_MULTIPLE:
            return self.klist.get_selected_rows()
        selection = self.klist.get_selected()
        if not selection:
            return []
        return [selection]

    def hide_add_button(self):
        self.add_button.hide()

    def hide_edit_button(self):
        self._can_edit = False
        self.edit_button.hide()

    def hide_del_button(self):
        self.delete_button.hide()

    def set_editor(self, editor_class):
        if editor_class and not issubclass(editor_class,
                                           (BaseEditor, BaseWizard)):
            raise TypeError("editor_class must be a BaseEditor subclass")
        self._editor_class = editor_class

    #
    # Signal handlers
    #

    def on_klist__row_activated(self, *args):
        self._edit()

    def on_klist__selection_changed(self, *args):
        self._update_sensitivity()

    def on_add_button__clicked(self, button):
        self._edit_model()

    def on_edit_button__clicked(self, button):
        self._edit()

    def on_delete_button__clicked(self, button):
        self._clear()


class SimpleListDialog(BasicDialog):
    size = (500, 400)

    def __init__(self, columns, objects, hide_cancel_btn=True,
                 title='', multiple=True):
        """
        Create a new SimpleListDialog.
        @param columns:
        @param objects:
        @param hide_cancel_btn:
        @param title:
        @param multiple: if we're allowed to select multiple items
        @type multiple: boolean
        """

        BasicDialog.__init__(self)
        BasicDialog._initialize(self, size=self.size, title=title)
        if hide_cancel_btn:
            self.cancel_button.hide()

        if multiple:
            selection_mode = gtk.SELECTION_MULTIPLE
        else:
            selection_mode = gtk.SELECTION_BROWSE
        self.setup_slave(columns, objects, selection_mode)

    def setup_slave(self, columns, objects, selection_mode):
        self.main.remove(self.main_label)
        self._klist = ObjectList(columns, objects, selection_mode)
        self.main.add(self._klist)
        self._klist.show()

    def get_selection(self):
        mode = self._klist.get_selection_mode()
        if mode == gtk.SELECTION_MULTIPLE:
            return self._klist.get_selected_rows()
        selection = self._klist.get_selected()
        if not selection:
            return []
        return [selection]

    # BasicDialog 'confirm' method override
    def confirm(self):
        self.retval = self.get_selection()
        self.close()

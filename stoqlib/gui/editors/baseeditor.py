# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source
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
""" Base classes for editors """

import logging

import gtk
from gtk import gdk
from kiwi.enums import ListType
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.listdialog import ListContainer
from kiwi.ui.widgets.label import ProxyLabel

from stoqlib.database.runtime import StoqlibStore
from stoqlib.gui.base.dialogs import RunnableView, BasicDialog, run_dialog
from stoqlib.gui.events import (EditorSlaveCreateEvent, EditorSlaveConfirmEvent,
                                EditorCreateEvent)
from stoqlib.lib.decorators import public
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext

log = logging.getLogger(__name__)

_ = stoqlib_gettext


def _get_slaves_recursively(editor_slave):
    slaves = []

    for slave in editor_slave.slaves.values():
        if isinstance(slave, BaseEditorSlave):
            slaves.append(slave)
        slaves.extend(_get_slaves_recursively(slave))

    return slaves


class BaseEditorSlave(GladeSlaveDelegate):
    """ Base class for editor slaves inheritance. It offers methods for
    setting up focus sequence, required attributes and validated attrs.

    :cvar gladefile:
    :cvar model_type:
    """
    domain = 'stoq'
    gladefile = None
    model_type = None
    fields = None
    proxy_widgets = ()

    def __init__(self, store, model=None, visual_mode=False, edit_mode=None):
        """ A base class for editor slaves inheritance

        :param store: a store
        :param model: the object model tied with the proxy widgets
        :param visual_mode: does this slave must be opened in visual mode?
                            if so, all the proxy widgets will be disable
        :param edit_mode: indicate if the slave are being edited or its a new one
                          The editor that creates the slave should pass his
                          property edit_mode to the slaves.
                          If None self.edit_mode will be defined accordingly to
                          the model
        """
        self.store = store
        # FIXME: Need to check if we need to add edit_mode parameter for all classes
        # that inherit from BaseEditor
        if edit_mode is not None:
            self.edit_mode = edit_mode
        else:
            self.edit_mode = model is not None
        self.visual_mode = visual_mode

        if model:
            created = ""
        else:
            created = "created "
            model = self.create_model(self.store)

            if model is None:
                fmt = "%s.create_model() must return a valid model, not %r"
                raise ValueError(fmt % (self.__class__.__name__, model))

        log.info("%s editor using a %smodel %s" % (
            self.__class__.__name__, created, type(model).__name__))

        if self.model_type:
            if not isinstance(model, self.model_type):
                fmt = '%s editor requires a model of type %s, got a %r'
                raise TypeError(
                    fmt % (self.__class__.__name__,
                           self.model_type.__name__,
                           model))
        else:
            fmt = "Editor %s must define a model_type attribute"
            raise ValueError(fmt % (self.__class__.__name__, ))
        self.model = model

        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        if self.visual_mode:
            self._setup_visual_mode()
        self.setup_proxies()
        self.setup_slaves()

        EditorSlaveCreateEvent.emit(self, model, store, visual_mode)

    #
    # Private
    #

    def _setup_visual_mode(self):
        widgets = self.__class__.proxy_widgets
        for widget_name in widgets:
            widget = getattr(self, widget_name)
            if isinstance(widget, ProxyLabel):
                pass
            elif isinstance(widget, gtk.Entry):
                # First, we need to be able to select text from entries
                widget.set_editable(False)
                # Second, make sure they don't look like they're editable,
                # copy over the insentive style
                style = widget.get_style()
                widget.modify_text(
                    gtk.STATE_NORMAL, style.text[gtk.STATE_INSENSITIVE])
                widget.modify_base(
                    gtk.STATE_NORMAL, style.base[gtk.STATE_INSENSITIVE])
            else:
                widget.set_sensitive(False)

        if self.fields:
            for field in self.fields.values():
                field.set_sensitive(False)
                field.can_edit = False

        self.update_visual_mode()

    #
    # Public API
    #

    def confirm(self):
        """Confirms the editor

        Before actually confirming, we will verify that
        :meth:`.validate_confirm` (and all slaves validate_confirm)
        returns ``True``.
        Only if none of those calls return ``False``, we will call
        :meth:`.on_confirm` on the editor and all the slaves.

        :class:`BaseEditor` will call this when someone clicks it's
        *confirm* button.
        """
        slaves = _get_slaves_recursively(self)
        slaves.append(self)

        # Do this before trying to confirm any of the slaves for safety
        if not all([slave.is_valid and slave.validate_confirm() for
                    slave in slaves]):
            return False

        for slave in slaves:
            slave.on_confirm()

        EditorSlaveConfirmEvent.emit(self, self.model, self.store, self.visual_mode)

        return True

    def cancel(self):
        """Cancels the editor

        By calling this, the editor will get cancelled. All of the
        editor's slaves :meth:`.on_cancel`, including the editor's
        itself will get called.

        :class:`BaseEditor` will call this when someone clicks it's
        *cancel* button.
        """
        slaves = _get_slaves_recursively(self)
        slaves.append(self)

        for slave in slaves:
            slave.on_cancel()

    def create_model(self, store):
        """Creates a new model for the editor.

        After this method is called, the model can be accessed as self.model.
        The default behavior is to raise a TypeError, which can
        be overridden in a subclass.

        :param store: a store
        """
        raise TypeError(
            "%r needs a model, got None. Perhaps you want to "
            "implement create_model?" % (self.__class__.__name__))

    def setup_proxies(self):
        """A subclass can override this to setup proxies

        This is called at the end of the object initialization and before
        :meth:`.setup_slaves`. If you need to add a proxy, it should
        be done here, eg:

            self.proxy = self.add_proxy(self.model, self.proxy_widgets)

        """

    def setup_slaves(self):
        """A subclass can override this to setup slaves

        This is called at the end of the object initialization and after
        :meth:`.setup_proxies`. If you need to add slaves, it should
        be done here, eg:

            self.attach_slave('slave_holder', SlaveClass())

        """

    def on_cancel(self):
        """Called when the dialog is about to get cancelled

        When someone calls :meth:`.cancel` (normally a :class:`BaseEditor`:
        when clicking on it's *cancel* button), this will be called. If you
        need to do some kind of cleanup when cancelling, like removing an
        object that was already commited, this is the right place to do it.

        Some places (like :func:`stoqlib.gui.base.dialogs.run_dialog`) will
        consider the editor's retval as :obj:`.retval`. Depending on the
        case, if you want to confirm the editor even when it was cancelled
        (e.g. Asking the user "Do you want to save those changes?")
        you can do:

            self.retval = True

        Or simply do what you want in another store and commit it.
        """

    def on_confirm(self):
        """Called when the dialog is about to get confirmed

        When someone calls :meth:`.confirm` (normally a :class:`BaseEditor`:
        when clicking on it's *confirm* button), this will be called. If you
        need to do some kind of late modification before the object gets
        commited, this is the place to do it.

        Some places (like :func:`stoqlib.gui.base.dialogs.run_dialog`) will
        consider the editor's retval as :obj:`.retval`. Depending on the
        case, if you want to cancel the editor even when it was confirmed
        you can do:

            self.retval = False

        Or simply do a rollback on the actual store.
        """

    def update_visual_mode(self):
        """Called when the editor enters on visual mode

        When the editor is readonly (aka visual mode), every proxy widgets
        and fields will be set insensitive. You should override this if
        you have any kind of extra work to do when entering visual mode.
        """

    def validate_confirm(self):
        """Called to see if the editor can be confirmed

        The editor won't get confirmed if this returns ``False``. It's
        recommended to show a message for the user, as a feedback, to
        explain why this didn't confirm. By default, this returns ``True``.
        """
        return True


@public(since="1.5.0")
class BaseEditor(BaseEditorSlave, RunnableView):
    """ Base class for editor dialogs. It offers methods of
    BaseEditorSlave, a windows title and OK/Cancel buttons.
    """

    #: the model type name of the model we are editing.
    #: This value will be showed in the title of the editor and can not
    #: be merely the attribute __name__ of the object for usability reasons.
    #: Call sites will decide what could be the best name applicable in each
    #: situation.
    model_name = None
    header = ''
    size = ()
    title = None
    hide_footer = False

    #: if we need to ask the user if he really wants to cancel the dialog if
    #: there are any changes done that would be lost otherwise
    need_cancel_confirmation = False

    #: a list of widget names that when activated will confirm the dialog
    confirm_widgets = ()
    help_section = None
    form_holder_name = 'toplevel'

    def __init__(self, store, model=None, visual_mode=False):
        self._confirm_disabled = False

        # FIXME:
        # BasicEditor should inheirt from BasicDialog and instantiate
        # the slave inside here, but it requires some major surgery
        BaseEditorSlave.__init__(self, store, model,
                                 visual_mode=visual_mode)

        self.main_dialog = BasicDialog(title=self.get_title(self.model),
                                       header_text=self.header,
                                       help_section=self.help_section,
                                       size=self.size)
        # Do not close the dialog if re return False on self.confirm
        self.main_dialog.enable_confirm_validation = True
        self.main_dialog.attach_slave("main", self)
        self.main_dialog.connect('confirm', self._on_main_dialog__confirm)
        self.main_dialog.connect('cancel', self._on_main_dialog__cancel)

        dialog_toplevel = self.main_dialog.get_toplevel()
        dialog_toplevel.connect('response', self._on_toplevel__response)
        dialog_toplevel.connect('delete-event', self._on_toplevel__delete_event)

        # This helps kiwis ui test, set the name of ourselves to
        # the classname of the slave, which is much more helpful than
        # just "BasicDialog"
        self.main_dialog.get_toplevel().set_name(self.__class__.__name__)

        if self.hide_footer or self.visual_mode:
            self.main_dialog.hide_footer()

        for name in self.confirm_widgets:
            self.set_confirm_widget(getattr(self, name))

        self.register_validate_function(self._validation_function)
        self.force_validation()
        # We need to use self.model instead of model, since BaseEditorSlave
        # will create one if its None
        EditorCreateEvent.emit(self, self.model, store, visual_mode)

        if store is not None:
            # This needs to be the last thing done on __init__ since we don't want
            # to consider things like self.create_model as a change
            self._store_pending_count = store.get_pending_count()

    #
    #  Private
    #

    def _get_title_format(self):
        if self.visual_mode:
            return _(u"Details of %s")
        if self.edit_mode:
            return _(u'Edit Details of "%s"')
        return _(u"Add %s")

    def _need_cancel_confirmation(self):
        return self.need_cancel_confirmation and self.has_changes()

    #
    #  Public
    #

    def has_changes(self):
        """Check if there are changes on this editor

        By default we will check if there're any pending changes on
        :obj:`.store` and that information will be used by
        :attr:`.need_cancel_confirmation`
        """
        if self.store is None:
            return False
        return self.store.get_pending_count() > self._store_pending_count

    def get_title(self, model):
        if self.title:
            return self.title
        if not model:
            raise ValueError("A model should be defined at this point")

        title_format = self._get_title_format()
        if self.model_name:
            model_name = self.model_name
        else:
            # Fallback to the name of the class
            model_name = type(self.model).__name__

        return title_format % model_name

    def enable_window_controls(self):
        """Enables the window controls
        See :class:`kiwi.ui.views.BaseView.enable_window_controls`.
        """
        self.main_dialog.enable_window_controls()

    def set_description(self, description):
        """Sets the description of the model object which is used by the editor
        :param description:
        """
        format = self._get_title_format()
        self.main_dialog.set_title(format % description)

    def refresh_ok(self, validation_value):
        """ Refreshes ok button sensitivity according to widget validators
        status """
        if self._confirm_disabled:
            return
        self.main_dialog.ok_button.set_sensitive(validation_value)

    def add_button(self, label=None, stock=None):
        """
        Adds a button to editor. The added button is returned which you
        can use to connect signals on.
        :param label: label of the button
        :param stock: stock label of the button
        :param returns: the button added
        :rtype: gtk.Button
        """

        if label is None and stock is None:
            raise TypeError("You need to provide a label or a stock argument")

        button = gtk.Button(label=label, stock=stock)
        button.props.can_focus = True
        self.main_dialog.action_area.pack_start(button, False, False)
        self.main_dialog.action_area.reorder_child(button, 0)
        button.show()
        return button

    def cancel(self):
        """
        Cancel the dialog.
        """
        if (self._need_cancel_confirmation() and
            not yesno(_("If you cancel this dialog all changes will be lost. "
                        "Are you sure?"), gtk.RESPONSE_NO,
                      _("Cancel"), _("Don't cancel"))):
            return False

        # set this before runing BaseEditorSlave.cancel so
        # on_cancel can modify self.retval, if needed
        self.retval = False
        BaseEditorSlave.cancel(self)

        self.main_dialog.close()
        if isinstance(self.store, StoqlibStore):
            self.store.retval = self.retval

        log.info("%s: Closed (cancelled), retval=%r" % (
            self.__class__.__name__, self.retval))

        return True

    def confirm(self):
        """
        Confirm the dialog.
        """
        # set this before runing BaseEditorSlave.confirm so
        # on_confirm can modify self.retval, if needed
        self.retval = self.model

        if self._confirm_disabled:
            return False
        if not BaseEditorSlave.confirm(self):
            return False

        self.main_dialog.close()
        if isinstance(self.store, StoqlibStore):
            self.store.retval = self.retval

        log.info("%s: Closed (confirmed), retval=%r" % (
            self.__class__.__name__, self.retval))

        return True

    def enable_ok(self):
        """
        Enable the ok button of the dialog, eg makes it possible
        to close/confirm the dialog.
        """
        self.main_dialog.enable_ok()
        self._confirm_disabled = False

    def disable_ok(self):
        """
        Enable the ok button of the dialog, eg makes it possible
        to close/confirm the dialog.
        """
        self.main_dialog.disable_ok()
        self._confirm_disabled = True

    def enable_normal_window(self):
        """
        Enable the dialog as a normal window.
        This tells the window manager that the window
        should behave as a normal window instead of a dialog.
        """
        toplevel = self.main_dialog.get_toplevel()
        toplevel.set_type_hint(gdk.WINDOW_TYPE_HINT_NORMAL)

    def set_confirm_widget(self, widget_name):
        """
        Make a widget confirmable, eg activating that widget would
        close the dialog.
        :param widget_name: name of the widget to be confirmable
        """
        self.main_dialog.set_confirm_widget(widget_name)

    def set_message(self, message, message_type=None):
        """Sets a message for this editor
        :param message: message to add
        :param message_type: type of message to add
        """
        if message_type is None:
            message_type = gtk.MESSAGE_INFO
        self.main_dialog.set_message(message, message_type)

    # RunnableView
    # This delegate everything to self.main_dialog

    def close(self):
        self.main_dialog.close()

    def run(self):
        self.main_dialog.run()

    def get_current_toplevel(self):
        return self.main_dialog.get_current_toplevel()

    def destroy(self):
        self.main_dialog.destroy()

    def set_transient_for(self, window):
        self.main_dialog.set_transient_for(window)

    # Callbacks

    def _on_main_dialog__cancel(self, dialog, retval):
        return self.cancel()

    def _on_main_dialog__confirm(self, dialog, retval):
        return self.confirm()

    def _validation_function(self, is_valid):
        self.refresh_ok(is_valid)

    def _on_toplevel__delete_event(self, widget, *args, **kwargs):
        # Avoid the dialog being closed when hitting 'Esc' and we would need
        # confirm the cancelation.
        if self._need_cancel_confirmation():
            return True

    def _on_toplevel__response(self, dialog, response, *args, **kwargs):
        # FIXME: For the delete-event to really stops from destroying the
        # dialog, we also need to stop the response event emission. See
        # http://faq.pygtk.org/index.py?req=show&file=faq10.013.htp
        # for more details
        if (self._need_cancel_confirmation() and
                response == gtk.RESPONSE_DELETE_EVENT):
            dialog.emit_stop_by_name('response')


class BaseRelationshipEditorSlave(GladeSlaveDelegate):
    """An editor for relationships between objects

    BaseRelationshipEditor provides an easy way to edit (add/remove) relations
    between objects.

    It doesn't allow creations of new objects, only linking between them.
    (the linking might require new objects, though)

    For example, you could edit suppliers for a product (or produts supplied
    by an supplier).

    Subclasses must implement get_targets, get_columns, get_relations, and
    create_model.
    """
    domain = 'stoq'
    gladefile = 'RelationshipEditor'
    target_name = None
    model_type = None
    editor = None

    def __init__(self, store, parent=None, visual_mode=False):
        self._parent = parent
        self.store = store
        self.visual_mode = visual_mode
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._setup_widgets()

    def _setup_relations_list(self):
        self.relations_list = ListContainer(self.get_columns(), gtk.ORIENTATION_HORIZONTAL)
        self.relations_list._vbox.padding = 0
        self.model_vbox.pack_start(self.relations_list)

        self.relations_list.set_list_type(ListType.UNADDABLE)

        self.relations_list.connect('remove-item',
                                    self._on_remove_item__clicked)
        self.relations_list.connect('edit-item', self._on_edit_item__clicked)

        self.relations_list.show()

    def _setup_widgets(self):
        self.model_name_label.set_label(self.target_name + ':')
        targets = self.get_targets()
        self.target_combo.prefill(targets)

        self._setup_relations_list()

        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        size_group.add_widget(self.add_button)
        size_group.add_widget(self.relations_list.edit_button)
        size_group.add_widget(self.relations_list.remove_button)

        self.add_button.set_sensitive(False)

        if not self.editor:
            self.relations_list.edit_button.set_sensitive(False)

        self.relations_list.add_items(self.get_relations())

        if self.visual_mode:
            self.target_combo.set_sensitive(False)
            self.add_button.set_sensitive(False)
            self.relations_list.set_list_type(ListType.READONLY)

    def get_targets(self):
        """Returns a list of valid taret objects.

        for instance, if suppliers for a product are being edited, then this
        should return a list fo suppliers.
        """
        raise NotImplementedError

    def get_columns(self):
        """Columns to display"""
        raise NotImplementedError

    def get_relations(self):
        """Returns the already existing relations.

        This may be entries from a maping table or entries from the target
        table itself, depending on the type of relationship
        """
        raise NotImplementedError

    def create_model(self):
        """This method should create the model when adding a new relationship.

        If the addition is canceled. It will automatically be removed.
        """
        raise NotImplementedError

    def add(self):
        model = self.create_model()

        if not model:
            return False

        if not self.editor:
            return model

        res = run_dialog(self.editor, self._parent, self.store, model)

        if not res:
            self.model_type.delete(id=model.id, store=self.store)

        return res

    def edit(self, model):
        return run_dialog(self.editor, self._parent, self.store, model)

    def remove(self, model):
        self.model_type.delete(model.id, store=self.store)
        return True

    def _run_editor(self, model=None):
        """Runs an editor for the relationship (if necessary).

        An editor may be necessary only if there is an mapping table and
        and extra information in this table.
        """
        if model is None:
            res = self.add()
        else:
            res = self.edit(model)

        return res

    def on_add_button__clicked(self, widget):
        result = self._run_editor()
        if result:
            self.relations_list.add_item(result)

    def on_target_combo__content_changed(self, widget):
        has_selected = self.target_combo.read() is not None
        self.add_button.set_sensitive(has_selected and not self.visual_mode)

    def _on_edit_item__clicked(self, list, item):
        if not self.editor:
            return

        result = self._run_editor(item)

        if result:
            self.relations_list.update_item(result)

    def _on_remove_item__clicked(self, list, item):
        if self.remove(item):
            self.relations_list.remove_item(item)

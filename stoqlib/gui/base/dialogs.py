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
""" Basic dialogs definition """

import inspect
import logging

import gtk
from kiwi.ui.dialogs import error, warning, info, yesno
from kiwi.ui.delegates import GladeDelegate
from kiwi.ui.views import BaseView
from kiwi.utils import gsignal
from zope.interface import implementer

from stoqlib.lib.decorators import public
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.interfaces import ISystemNotifier
from stoqlib.gui.base.gtkadds import change_button_appearance
from stoqlib.gui.base.messagebar import MessageBar
from stoqlib.gui.events import DialogCreateEvent, RunDialogEvent

_ = stoqlib_gettext
_toplevel_stack = []

log = logging.getLogger(__name__)

#
# Helper classes
#


class RunnableView:
    """A mixin class for any View or GladeDelegate that offers run/close"""
    retval = None

    def close(self, *args):
        """Handles action to be performed when window is closed."""
        self.get_toplevel().hide()

    def destroy(self):
        self.get_toplevel().destroy()

    def run(self):
        """Handles action to be performed when window is opened. Defaults to
        _open(), which blocks in a mainloop. Returns the value of the retval
        attribute.
        """
        self.show()

    def get_current_toplevel(self):
        return self.get_toplevel()

    def set_transient_for(self, window):
        self.get_toplevel().set_transient_for(window)


class BasicDialog(GladeDelegate, RunnableView):
    """Abstract class that offers a Dialog with two buttons. It should be
    subclassed and customized.
    """

    domain = 'stoq'
    help_section = None
    gsignal('confirm', object, retval=bool)
    gsignal('cancel', object)

    def __init__(self, main_label_text=None, title=" ",
                 header_text="", size=None, hide_footer=False,
                 delete_handler=None, help_section=None):
        self.enable_confirm_validation = False
        self._message_bar = None
        self._create_dialog_ui()
        if delete_handler is None:
            delete_handler = self._delete_handler
        GladeDelegate.__init__(self, delete_handler=delete_handler,
                               gladefile=self.gladefile)
        help_section = help_section or self.help_section
        if help_section:
            self._add_help_button(help_section)

        # FIXME: Create more widgets lazily when needed
        self.set_title(title)
        if size:
            self.get_toplevel().set_size_request(*size)
        if main_label_text:
            self.main_label.set_text(main_label_text)
        if header_text:
            header_label = gtk.Label()
            header_label.set_markup(header_text)
            self.header.add(header_label)
            header_label.show()
        if hide_footer:
            self.hide_footer()

        DialogCreateEvent.emit(self)

    #
    # Private
    #

    def _create_dialog_ui(self):
        self.toplevel = gtk.Dialog()
        self._main_vbox = self.toplevel.get_content_area()

        self.vbox = gtk.VBox()
        self._main_vbox.pack_start(self.vbox, True, True)
        self.vbox.show()

        # FIXME
        # stoqlib/gui/base/search.py - hides the header
        self.header = gtk.EventBox()
        self.vbox.pack_start(self.header, False, False)
        self.header.show()

        self.main = gtk.EventBox()
        self.vbox.pack_start(self.main, padding=6)
        self.main.show()

        # FIXME
        # stoqlib/gui/dialogs/importerdialog.py - setting
        # stoqlib/gui/base/lists.py - removes the label
        # stoqlib/gui/base/search.py - removes the label
        # plugins/ecf/deviceconstanteditor.py - removes the label
        self.main_label = gtk.Label()
        self.main.add(self.main_label)
        self.main_label.show()

        hbox1 = gtk.HBox()
        self.vbox.pack_start(hbox1, False, 6)
        hbox1.show()

        # FIXME
        # stoqlib/gui/dialogs/paymentmethod.py
        # stoqlib/gui/search/salesearch.py
        self.extra_holder = gtk.EventBox()
        hbox1.pack_start(self.extra_holder, True, True, 6)
        self.extra_holder.show()

        # FIXME
        # stoqlib/gui/search/productsearch.py
        # stoqlib/gui/search/servicesearch.py
        self.print_holder = gtk.EventBox()
        hbox1.pack_start(self.print_holder, True, True)
        self.print_holder.show()

        # FIXME
        # stoqlib/gui/base/search.py
        # stoqlib/gui/slaves/productslave.py
        self.details_holder = gtk.EventBox()
        hbox1.pack_end(self.details_holder, False, False, 6)
        self.details_holder.show()

        # FIXME
        # stoqlib/gui/dialogs/quotedialog.py
        self.notice = gtk.EventBox()
        hbox1.pack_start(self.notice, False, 6)
        self.notice.show()

        action_area = self.toplevel.get_action_area()
        action_area.set_border_width(6)
        action_area.set_layout(gtk.BUTTONBOX_END)

        self.cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        action_area.pack_start(self.cancel_button, True, True, 6)
        self.cancel_button.show()

        self.ok_button = gtk.Button(stock=gtk.STOCK_OK)
        self.ok_button.set_use_underline(True)
        action_area.pack_start(self.ok_button, True, True, 6)
        self.ok_button.show()

    def _try_confirm(self, *args):
        """Only confirm if ok button is actually enabled.

        This is so that this dialog doesn't get confirmed in case the ok
        button was specifically disabled.
        """
        # FIXME: There should be a better way to findout valid status
        if self.ok_button.get_sensitive():
            self.confirm()

    def _add_help_button(self, section):
        def on_help__clicked(button):
            from stoqlib.gui.utils.help import show_section
            show_section(section)

        self.action_area.set_layout(gtk.BUTTONBOX_END)
        self.help_button = gtk.Button(stock=gtk.STOCK_HELP)
        self.help_button.connect('clicked', on_help__clicked)
        self.action_area.pack_start(self.help_button, False, False, 6)
        self.action_area.set_child_secondary(self.help_button, True)
        self.help_button.show()

    #
    # Public API
    #

    def confirm(self):
        # SearchDialog and SellableSearch overrides this
        self.retval = True
        # FIXME: Confirm validation should be enabled by default,
        #        but we need to change the dialog API and existing
        #        callsites for that to work.
        if (self.enable_confirm_validation and not
            self.emit('confirm', self.retval)):
            return

        self.close()

    def cancel(self):
        # SearchDialog overrides this
        self.retval = False
        # FIXME: See fixme on confirm
        if (self.enable_confirm_validation and
            not self.emit('cancel', self.retval)):
            return

        self.close()

    def hide_footer(self):
        self.ok_button.hide()
        self.cancel_button.hide()

    def enable_ok(self):
        self.ok_button.set_sensitive(True)

    def disable_ok(self):
        self.ok_button.set_sensitive(False)

    def set_ok_label(self, text, icon=None):
        if not icon:
            icon = gtk.STOCK_OK
        change_button_appearance(self.ok_button, icon, text)

    def set_cancel_label(self, text, icon=None):
        if not icon:
            icon = gtk.STOCK_CANCEL
        change_button_appearance(self.cancel_button, icon, text)

    def set_confirm_widget(self, widget):
        """Enables widget as a confirm widget, the dialog will be closed as
        confirmed if the widget is activated.
        :param widget: a widget
        """
        dialog = self.get_toplevel()
        if not widget.is_ancestor(dialog):
            raise ValueError("dialog %r is not an ancestor of widget %r" % (
                dialog, widget))
        widget.connect('activate', self._try_confirm)

    def add(self, widget):
        for child in self.main.get_children():
            self.main.remove(child)
        self.main.add(widget)

    @property
    def action_area(self):
        return self.get_toplevel().action_area

    def set_message(self, message, message_type=None):
        """Sets a message for this editor
        :param message: message to add or None to remove previous message
        :param message_type: type of message to add
        """
        if message_type is None:
            message_type = gtk.MESSAGE_INFO
        if self._message_bar is not None:
            self._message_bar.destroy()
            self._message_bar = None
        if message is None:
            return
        self._message_bar = MessageBar(message, message_type)
        self._main_vbox.pack_start(self._message_bar, False, False)
        self._main_vbox.reorder_child(self._message_bar, 0)
        self._message_bar.show_all()
        return self._message_bar

    #
    # Kiwi handlers
    #

    def on_ok_button__clicked(self, button):
        self.confirm()

    def on_cancel_button__clicked(self, button):
        self.cancel()

    def _delete_handler(self, window, event):
        self.cancel()


#
# General methods
#

def get_current_toplevel():
    if _toplevel_stack:
        return _toplevel_stack[-1]


def add_current_toplevel(toplevel):
    _toplevel_stack.append(toplevel)


def _pop_current_toplevel():
    if _toplevel_stack:
        _toplevel_stack.pop()


def get_dialog(parent, dialog, *args, **kwargs):
    """Returns a dialog.

    :param parent: the window which is opening the dialog
    :param dialog: the dialog class or instance
    :param args: custom positional arguments
    :param kwargs: custom keyword arguments
    """
    if callable(dialog):
        dialog = dialog(*args, **kwargs)

    # If parent is a BaseView, use GTK+ calls to get the toplevel
    # window. This is a bit of a hack :-/
    if isinstance(parent, BaseView):
        parent = parent.get_toplevel().get_toplevel()
        if parent and not _fullscreen:
            dialog.set_transient_for(parent)
    return dialog


def has_modal_window():
    """Verifies if any of the currently open windows are modal.

    :returns: ``True`` if there are any modal windows open, otherwise ``False``
    """
    windows = _toplevel_stack
    return any(window.get_modal() for window in windows)


@public(since="1.5.0")
def run_dialog(dialog, parent=None, *args, **kwargs):
    """Runs a dialog and return the return value of it.
    If dialog is a class it will be instantiated before running the dialog.

    :param dialog: the dialog class
    :param parent: parent of the dialog
    :param args: custom positional arguments
    :param kwargs: custom keyword arguments
    """

    if dialog is None:
        raise TypeError("dialog cannot be None")

    dialog = RunDialogEvent.emit(dialog, parent, *args, **kwargs)
    if not issubclass(dialog, RunnableView):
        raise TypeError("dialog %r must be subclass of RunnableView" % (
            dialog, ))

    # FIXME: Move this into RunnableView

    #XXX: When create a new Stoq window, even using the parent correctly:
    # The called dialog will be a modal of the latest created window
    # (not necessarily the window that called).
    parent = getattr(parent, 'main_dialog', parent)
    parent = parent or get_current_toplevel()
    if inspect.isclass(dialog):
        dialog_name = dialog.__name__
    else:
        dialog_name = dialog.__class__.__name__

    dialog = get_dialog(parent, dialog, *args, **kwargs)
    orig_dialog = dialog
    toplevel = dialog.get_current_toplevel()
    add_current_toplevel(toplevel)

    if _fullscreen is not None:
        toplevel.set_position(gtk.WIN_POS_CENTER)
    elif parent and isinstance(parent, gtk.Window) and parent.props.visible:
        toplevel.set_transient_for(parent)
        toplevel.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    else:
        if parent:
            toplevel.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        else:
            toplevel.set_position(gtk.WIN_POS_CENTER)
        # FIXME: This should not be necessary, but gnome shell hides window
        # decorations for HINT_DIALOG. We should study what dialogs should
        # have HINT_NORMAL (with window decorations) and what can have
        # HINT_DIALOG
        toplevel.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)

    log.info("%s: Opening" % dialog_name)

    if hasattr(parent, 'on_dialog__opened'):
        parent.on_dialog__opened(orig_dialog)

    retval = run_dialog_internal(dialog, parent, toplevel)

    _pop_current_toplevel()

    return retval


# Mainly for mocking

def run_dialog_internal(dialog, parent, toplevel):
    # FIXME: We should avoid calling dialog.run() here
    # See http://tinyurl.com/lj6ske4
    toplevel.run()

    retval = dialog.retval
    dialog.destroy()

    return retval

_fullscreen = None


def push_fullscreen(window):
    global _fullscreen
    _fullscreen = window


def pop_fullscreen(window):
    global _fullscreen
    _fullscreen = None


@implementer(ISystemNotifier)
class DialogSystemNotifier:
    def info(self, short, description):
        info(short, description, get_current_toplevel())

    def warning(self, short, description, *args, **kwargs):
        return warning(short, description, get_current_toplevel(), *args,
                       **kwargs)

    def error(self, short, description):
        error(short, description, get_current_toplevel())

    def yesno(self, text, default=None, *verbs):
        if default is None:
            default = gtk.RESPONSE_YES
        if len(verbs) != 2:
            raise ValueError(
                "Button descriptions must be a tuple with 2 items")
        if verbs == (_("Yes"), _("No")):
            buttons = gtk.BUTTONS_YES_NO
        else:
            buttons = ((verbs[0], gtk.RESPONSE_YES),
                       (verbs[1], gtk.RESPONSE_NO))
        return (yesno(text, get_current_toplevel(), default, buttons)
                == gtk.RESPONSE_YES)

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

import gtk
from gtk import keysyms
from kiwi.log import Logger
from kiwi.ui.dialogs import error, warning, info, yesno
from kiwi.ui.delegates import GladeDelegate
from kiwi.ui.views import BaseView
from zope.interface import implements

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.interfaces import ISystemNotifier
from stoqlib.gui.base.gtkadds import change_button_appearance
from stoqlib.gui.events import DialogCreateEvent

_ = stoqlib_gettext
_toplevel_stack = []

log = Logger('stoqlib.dialogs')

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


class BasicDialog(GladeDelegate, RunnableView):
    """Abstract class that offers a Dialog with two buttons. It should be
    subclassed and customized.
    """
    gladefile = "BasicDialog"
    help_section = None

    def __init__(self, main_label_text=None, title=" ",
                 header_text="", size=None, hide_footer=False,
                 delete_handler=None):
        if not delete_handler:
            delete_handler = self.cancel
        self.setup_keyactions()
        GladeDelegate.__init__(self, delete_handler=delete_handler,
                               gladefile=self.gladefile,
                               keyactions=self.keyactions)
        if self.help_section:
            self._add_help_button(self.help_section)

        self.set_title(title)
        if size:
            self.get_toplevel().set_size_request(*size)
        if main_label_text:
            self.main_label.set_text(main_label_text)
        if header_text:
            self.header_label.set_text(header_text)
        else:
            self.header_label.hide()
            self.top_separator.hide()
        if hide_footer:
            self.hide_footer()
        self.ok_button.set_use_underline(True)

        DialogCreateEvent.emit(self)

    def _try_confirm(self, *args):
        """Only confirm if ok button is actually enabled.

        This is so that this dialog doesn't get confirmed in case the ok
        button was specifically disabled.
        """
        # FIXME: There should be a better way to findout valid status
        if self.ok_button.get_sensitive():
            self.confirm()

    def setup_keyactions(self):
        self.keyactions = {keysyms.Escape: self.cancel,
                           keysyms.Return: self.confirm,
                           keysyms.KP_Enter: self.confirm}

    def confirm(self, *args):
        self.retval = True
        self.close()

    def cancel(self, *args):
        self.retval = False
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

    def set_cancel_label(self, text):
        self.cancel_button.set_label(text)

    def justify_label(self, just):
        self.main_label.set_justify(just)

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

    def set_cancel_widget(self, widget):
        """Enables widget as a cancel widget, the dialog will be closed as
        canceled if the widget is activated.
        :param widget: a widget
        """
        dialog = self.get_toplevel()
        if not widget.is_ancestor(dialog):
            raise ValueError("dialog %r is not an ancestor of widget %r" % (
                dialog, widget))
        widget.connect('activate', self.cancel)

    def add(self, widget):
        for child in self.main.get_children():
            self.main.remove(child)
        self.main.add(widget)

    @property
    def action_area(self):
        return self.get_toplevel().action_area

    #
    # Private
    #

    def _add_help_button(self, section):
        def on_help__clicked(button):
            from stoqlib.gui.help import show_section
            show_section(section)

        self.action_area.set_layout(gtk.BUTTONBOX_END)
        button = gtk.Button(stock=gtk.STOCK_HELP)
        button.connect('clicked', on_help__clicked)
        self.action_area.add(button)
        self.action_area.set_child_secondary(button, True)
        button.show()

    #
    # Kiwi handlers
    #

    def on_ok_button__clicked(self, button):
        self.confirm()

    def on_cancel_button__clicked(self, button):
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
    """ Returns a dialog.
    - parent: the window which is opening the dialog;
    - dialog: the dialog class or instance;
    - *args, **kwargs: the arguments which should be used on dialog
      instantiation;
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


def run_dialog(dialog, parent=None, *args, **kwargs):
    """Runs a dialog and return the return value of it.
    If dialog is a class it will be instantiated before running the dialog.

    :param dialog: the dialog, could be a class or instance
    :param parent: parent of the dialog
    :param args: custom positional argument
    :param kwargs: custom keyword arguments
    """

    if dialog is None:
        raise TypeError("dialog cannot be None")

    parent = getattr(parent, 'main_dialog', parent)
    parent = parent or get_current_toplevel()
    if inspect.isclass(dialog):
        dialog_name = dialog.__name__
    else:
        dialog_name = dialog.__class__.__name__

    dialog = get_dialog(parent, dialog, *args, **kwargs)
    orig_dialog = dialog
    if hasattr(dialog, 'main_dialog'):
        dialog = dialog.main_dialog

    toplevel = dialog.get_toplevel()
    add_current_toplevel(toplevel)

    if _fullscreen is not None:
        toplevel.set_position(gtk.WIN_POS_CENTER)
    elif parent and isinstance(parent, gtk.Window) and parent.props.visible:
        toplevel.set_transient_for(parent)
        toplevel.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    else:
        toplevel.set_position(gtk.WIN_POS_CENTER)

    if hasattr(parent, 'on_dialog__opened'):
        parent.on_dialog__opened(orig_dialog)

    log.info("%s: Opening" % dialog_name)

    # FIXME: We should avoid calling dialog.run() here
    # See http://stackoverflow.com/questions/3504739/twisted-gtk-should-i-run-gui-things-in-threads-or-in-the-reactor-thread
    toplevel.run()

    retval = getattr(dialog, 'retval', None)
    dialog.destroy()

    _pop_current_toplevel()
    return retval

_fullscreen = None


def push_fullscreen(window):
    global _fullscreen
    _fullscreen = window


def pop_fullscreen(window):
    global _fullscreen
    _fullscreen = None


class DialogSystemNotifier:
    implements(ISystemNotifier)

    def info(self, short, description):
        info(short, description, get_current_toplevel())

    def warning(self, short, description, *args, **kwargs):
        return warning(short, description, get_current_toplevel(), *args,
                       **kwargs)

    def error(self, short, description):
        error(short, description, get_current_toplevel())

    def yesno(self, text, default=gtk.RESPONSE_YES, *verbs):
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

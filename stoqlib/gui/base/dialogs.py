# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source
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
from kiwi.ui.delegates import GladeSlaveDelegate, GladeDelegate
from kiwi.ui.views import BaseView
from kiwi.utils import gsignal
from kiwi.argcheck import argcheck
from zope.interface import implements

from stoqlib.exceptions import ModelDataError
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.interfaces import ISystemNotifier
from stoqlib.gui.base.gtkadds import change_button_appearance

_ = stoqlib_gettext
_toplevel_stack = []

log = Logger('stoqlib.dialogs')

#
# Helper classes
#


class Warnbox(GladeSlaveDelegate):
    def __init__(self):
        GladeSlaveDelegate.__init__(self, gladefile='Warnbox')

    def setup_label(self, message):
        self.label.set_bold(True)
        self.label.set_color('red')
        self.label.set_justify(gtk.JUSTIFY_LEFT)
        self.label.set_text(message)

    def error(self, message):
        self.alert_icon.hide()
        self.error_icon.show()
        self.setup_label(message)
        self.get_toplevel().show()

    def alert(self, message):
        self.alert_icon.show()
        self.error_icon.hide()
        self.setup_label(message)
        self.get_toplevel().show()

    def clear_notices(self):
        # Don't hide warnbox or the vbox collapses it
        self.alert_icon.hide()
        self.error_icon.hide()
        self.label.set_text("")


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

#
# Abstract classes: inherit only, do not use.
#


class AbstractDialog(GladeDelegate, RunnableView):
    """Abstract Dialog class that defines a simple run API."""
    gladefile = None
    help_section = None

    def __init__(self, delete_handler=None):
        if not delete_handler:
            delete_handler = self.close

        self.setup_keyactions()
        GladeDelegate.__init__(self, gladefile=self.gladefile,
                               delete_handler=delete_handler,
                               keyactions=self.keyactions)

        if self.help_section:
            self._add_help_button(self.help_section)

    #
    #  Public API
    #

    def setup_keyactions(self):
        self.keyactions = {}

    #
    #  Private
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
# Special note for BasicDialog and BasicPluggableDialog: if you inherit
# from this class, you *must* call Basic*Dialog._initialize() right after
# calling Basic*Dialog.__init__() or the dialog will not be set up
# correctly. Initialization has been broken into two steps to allow it to
# be called conveniently from a consumer refresh() method. See
# NotifyDialog/PluggableNotifyDialog for an example of how __init__ should
# behave.
#


class BasicDialog(AbstractDialog):
    """Abstract class that offers a Dialog with two buttons. It should be
    subclassed and customized.
    """
    gladefile = "BasicDialog"

    def __init__(self, delete_handler=None):
        if not delete_handler:
            delete_handler = self.cancel
        AbstractDialog.__init__(self, delete_handler=delete_handler)

    # Yes, title=" ". Use a single space to work around *cough* BROKEN
    # window managers that want to set the title as Unnamed or ? when an
    # empty string is set to it.
    def _initialize(self, main_label_text=None, title=" ",
                    header_text="", size=None, hide_footer=False):
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

    def _try_confirm(self, *args):
        """Only confirm if ok button is actually enabled.

        This is so that this dialog doesn't get confirmed in case the ok
        button was specifically disabled.
        """
        # FIXME: There should be a better way to findout valid status
        if self.ok_button.get_sensitive():
            self.confirm()

    def setup_keyactions(self):
        self.keyactions = {keysyms.Escape: self.cancel}

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
        @param widget: a widget
        """
        dialog = self.get_toplevel()
        if not widget.is_ancestor(dialog):
            raise ValueError("dialog %r is not an ancestor of widget %r" % (
                dialog, widget))
        widget.connect('activate', self._try_confirm)

    def set_cancel_widget(self, widget):
        """Enables widget as a cancel widget, the dialog will be closed as
        canceled if the widget is activated.
        @param widget: a widget
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
    # Kiwi handlers
    #

    def on_ok_button__clicked(self, button):
        self.confirm()

    def on_cancel_button__clicked(self, button):
        self.cancel()

#
# Main classes start here. There are two basic types: Notify and
# Confirm dialogs, the only difference between them being that Notify
# offers only an OK button and Confirm offering both OK and Cancel. The
# second set offers a pluggable slave area.
#


class BasicPluggableDialog(BasicDialog):
    """Abstract class for Pluggable*Dialog; two buttons and a slave area"""
    warnbox = None
    slave = None
    gsignal('confirm', object)

    def _initialize(self, slave, title=" ", header_text="", size=None,
                    hide_footer=False):
        """May be called by refresh by subdialogs, as necessary"""
        if self.slave:
            log.warn("%s had self.slave set to %s!" % (self, self.slave))
        self.slave = slave
        self.attach_slave("main", slave)
        if self.warnbox:
            self.clear_notices()
            self.warnbox = None
        BasicDialog._initialize(self, title=title, header_text=header_text,
                                size=size, hide_footer=hide_footer)

    def enable_notices(self):
        """Enables display of notice messages with icons using alert() and
        error().
        """
        self.warnbox = Warnbox()
        self.clear_notices()
        self.attach_slave('notice', self.warnbox)
        self.warnbox.get_toplevel().hide()

    def clear_notices(self):
        self.warnbox.clear_notices()

    def error(self, message):
        if not self.warnbox:
            raise AssertionError
        self.warnbox.error(message)

    def alert(self, message):
        if not self.warnbox:
            raise AssertionError
        self.warnbox.alert(message)

    def confirm(self, *args):
        if not self.slave.validate_confirm():
            return

        # self.slave.on_confirm() should return a considered success
        # value. It can be an integer or a model object.
        self.retval = self.slave.on_confirm()
        self.close()
        self.emit('confirm', self.retval)

        log.info("%s: Closed (confirmed), retval=%r" % (
            self.slave.__class__.__name__, self.retval))

    def cancel(self, *args):
        # self.slave.on_cancel() should return a considered failure
        # value
        self.retval = self.slave.on_cancel()
        self.close()

        log.info("%s: Closed (cancelled), retval=%r" % (
            self.slave.__class__.__name__, self.retval))

#
# Wrapping variants, which take a slave as a parameter and set it up to
# have a "normal" dialog API, which follows the BasicPluggableDialog
# interface for stoqlib.services run_dialog compatibility.
#


class BasicWrappingDialog(BasicPluggableDialog):
    """ Abstract class for Wrapping*Dialog; run and set_transient_for to
    the wrapped slave and ok_button sensitivity control """
    def __init__(self, slave, title=" ", header_text="", size=None,
                 hide_footer=False):
        BasicPluggableDialog.__init__(self)
        BasicPluggableDialog._initialize(self, slave, title, header_text,
                                         size, hide_footer=hide_footer)
        # This helps kiwis ui test, set the name of ourselves to
        # the classname of the slave, which is much more helpful than
        # just "BasicWrappingDialog"
        self.get_toplevel().set_name(slave.__class__.__name__)
        slave.run = self.run
        slave.set_transient_for = self.set_transient_for


class ConfirmDialog(BasicDialog):
    """Dialog offers an option to confirm or cancel an event. It prints text
    in a label and offers OK/Cancel buttons.
    """

    title = _('Confirmation')

    def __init__(self, text='', title=None, size=None, ok_label=None):
        BasicDialog.__init__(self)
        self.justify_label(gtk.JUSTIFY_CENTER)
        BasicDialog._initialize(self, text,
                                title=title or self.title, size=size)
        if ok_label:
            self.set_ok_label(ok_label)

    def setup_keyactions(self):
        self.keyactions = {keysyms.Escape: self.cancel,
                           keysyms.Return: self.confirm,
                           keysyms.KP_Enter: self.confirm}


class NotifyDialog(ConfirmDialog):
    """Dialog that notifies an event. It prints text in a label and offers a
    single OK button.
    """

    title = _('Notification')

    def __init__(self, text, title=None, size=None, ok_label=None):
        ConfirmDialog.__init__(self, text, title, size=size,
                               ok_label=ok_label)
        self.cancel_button.hide()


#
# General methods
#

def get_current_toplevel():
    if _toplevel_stack:
        return _toplevel_stack[-1]


@argcheck(gtk.Window)
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

    @param dialog: the dialog, could be a class or instance
    @param parent: parent of the dialog
    @param args: custom positional argument
    @param kwargs: custom keyword arguments
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


def notify_if_raises(win, check_func, exceptions=ModelDataError,
                     text="An error ocurred: %s"):
    try:
        check_func()
    except exceptions, e:
        warning(text % e)
        return True
    return False


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

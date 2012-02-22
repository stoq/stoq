# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
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
""" Base classes for wizards """

import gtk
from kiwi.log import Logger
from kiwi.ui.delegates import GladeDelegate, GladeSlaveDelegate

from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.gui.base.dialogs import RunnableView
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.help import show_section
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
logger = Logger('stoqlib.gui.base.wizard')


class WizardStep:
    """ This class must be inherited by the steps """
    def __init__(self, previous=None, header=None):
        self.previous = previous
        self.header = header

    def next_step(self):
        # This is a virtual method, which must be redefined on children
        # classes. It should not be called by the last step (in this case,
        # has_next_step should return 0).
        raise NotImplementedError

    def post_init(self):
        """A virtual method that must be defined on child when it's
        necessary. This method will be called right after the change_step
        method on PluggableWizard is concluded for the current step.
        """

    def has_next_step(self):
        # This method should return False on last step classes
        return True

    def has_previous_step(self):
        # This method should return False on first step classes; since
        # self.previous is normally None for them, we can get away with
        # this simplified check. Redefine as necessary.
        return self.previous is not None

    def previous_step(self):
        return self.previous

    def validate_step(self):
        """A hook called always when changing steps. If it returns False
        we can not go forward.
        """
        return True


class PluggableWizard(GladeDelegate):
    """ Wizard controller and view class """
    gladefile = 'PluggableWizard'
    retval = None

    def __init__(self, title, first_step, size=None, edit_mode=False):
        """
        Create a new PluggableWizard object.
        :param title:
        :param first_step:
        :param size:
        :param edit_mode:
        """
        GladeDelegate.__init__(self, delete_handler=self.quit_if_last,
                               gladefile=self.gladefile)
        if not isinstance(first_step, WizardStep):
            raise TypeError("first_step must be a WizardStep "
                "instance, not %r" % (first_step, ))

        self.set_title(title)
        self._current = None
        self._first_step = first_step
        self.edit_mode = edit_mode
        if size:
            self.get_toplevel().set_default_size(size[0], size[1])

        self._change_step(first_step)
        if not self.edit_mode:
            self.ok_button.hide()

    # Callbacks

    def on_next_button__clicked(self, button):
        self.go_to_next()

    def on_ok_button__clicked(self, button):
        self._change_step()

    def on_previous_button__clicked(self, button):
        self._change_step(self._current.previous_step())

    def on_cancel_button__clicked(self, button):
        self.cancel()

    # Private API

    def _change_step(self, step=None):
        if step is None:
            # This is the last step and we can finish the job here
            self.finish()
            return
        # If the next step is the current one, stay on it.
        if step is self._current:
            return
        step.show()
        self._current = step
        self._refresh_slave()
        if step.header:
            self.header_lbl.show()
            self.header_lbl.set_text(step.header)
        else:
            self.header_lbl.hide()
        self.update_view()
        self._current.post_init()

    def _refresh_slave(self):
        holder_name = 'slave_area'
        if self.get_slave(holder_name):
            self.detach_slave(holder_name)
        self.attach_slave(holder_name, self._current)

    def _show_first_page(self):
        self.enable_next()
        self.disable_back()
        self.disable_finish()
        self.notification_lbl.hide()

    def _show_page(self):
        self.enable_back()
        self.enable_next()
        self.disable_finish()
        self.notification_lbl.hide()

    def _show_last_page(self):
        self.enable_back()
        self.notification_lbl.show()
        if self.edit_mode:
            self.disable_next()
        else:
            self.enable_next()
        self.enable_finish()

    # Public API
    def update_view(self):
        if self.edit_mode:
            self.ok_button.set_sensitive(True)

        if not self._current.has_previous_step():
            self._show_first_page()
        elif self._current.has_next_step():
            self._show_page()
        else:
            self._show_last_page()

    def enable_next(self):
        """
        Enables the next button in the wizard.
        """
        self.next_button.set_sensitive(True)

    def disable_next(self):
        """
        Disables the next button in the wizard.
        """
        self.next_button.set_sensitive(False)

    def enable_back(self):
        """
        Enables the back button in the wizard.
        """
        self.previous_button.set_sensitive(True)

    def disable_back(self):
        """
        Disables the back button in the wizard.
        """
        self.previous_button.set_sensitive(False)

    def enable_finish(self):
        """
        Enables the finish button in the wizard.
        """
        if self.edit_mode:
            button = self.ok_button
        else:
            button = self.next_button
        button.set_label(_('_Finish'))

    def disable_finish(self):
        """
        Disables the finish button in the wizard.
        """
        if self.edit_mode:
            self.ok_button.set_label(gtk.STOCK_OK)
        else:
            self.next_button.set_label(gtk.STOCK_GO_FORWARD)

    def set_message(self, message):
        """
        Set message for nofitication.
        :param message:
        """
        self.notification_lbl.set_text(message)

    def cancel(self, *args):
        # Redefine this method if you want something done when cancelling the
        # wizard.
        self.retval = None

    def finish(self):
        # Redefine this method if you want something done when finishing the
        # wizard.
        pass

    def go_to_next(self):
        if not self._current.validate_step():
            return

        if not self._current.has_next_step():
            # This is the last step
            self._change_step()
            return

        self._change_step(self._current.next_step())


class BaseWizardStep(WizardStep, GladeSlaveDelegate):
    """A wizard step base class definition"""
    gladefile = None

    def __init__(self, conn, wizard, previous=None):
        logger.info('Entering wizard step: %s' % self.__class__.__name__)
        self.conn = conn
        self.wizard = wizard
        WizardStep.__init__(self, previous)
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)


class WizardEditorStep(BaseEditorSlave, WizardStep):
    """A wizard step base class definition used when we have a model to be
    edited or created"""

    def __init__(self, conn, wizard, model=None, previous=None):
        logger.info('Entering wizard step: %s' % self.__class__.__name__)
        self.wizard = wizard
        WizardStep.__init__(self, previous)
        BaseEditorSlave.__init__(self, conn, model)


class BaseWizard(PluggableWizard, RunnableView):
    """A wizard base class definition"""
    title = None
    size = ()

    def __init__(self, conn, first_step, model=None, title=None,
                 size=None, edit_mode=False):
        logger.info('Entering wizard: %s' % self.__class__.__name__)
        self.conn = conn
        self.model = model
        if isinstance(self.conn, StoqlibTransaction):
            self.conn.needs_retval = True
        self.retval = None
        size = size or self.size
        title = title or self.title
        if not title:
            raise ValueError('A title argument is required')
        PluggableWizard.__init__(self, title=title, first_step=first_step,
                                 size=size, edit_mode=edit_mode)
        self.enable_window_controls()

    def set_help_section(self, section):
        def on_help__clicked(button):
            show_section(section)

        self.buttonbox.set_layout(gtk.BUTTONBOX_END)
        button = gtk.Button(stock=gtk.STOCK_HELP)
        button.connect('clicked', on_help__clicked)
        self.buttonbox.add(button)
        self.buttonbox.set_child_secondary(button, True)
        button.show()

    def cancel(self):
        logger.info('Canceling wizard: %s' % self.__class__.__name__)
        PluggableWizard.cancel(self)
        self.close()

    def quit_if_last(self, *args):
        """A delete handler method for wizards"""
        self.cancel()

    def refresh_next(self, validation_value):
        if validation_value:
            self.enable_next()
        else:
            self.disable_next()

    def close(self):
        if isinstance(self.conn, StoqlibTransaction):
            self.conn.retval = self.retval
        return super(BaseWizard, self).close()

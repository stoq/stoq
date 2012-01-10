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
from kiwi.ui.wizard import PluggableWizard, WizardStep
from kiwi.ui.delegates import GladeSlaveDelegate

from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.gui.base.dialogs import RunnableView
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.help import show_section

logger = Logger('stoqlib.gui.base.wizard')


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

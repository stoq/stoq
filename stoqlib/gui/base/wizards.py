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
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Base classes for wizards """

from kiwi.ui.wizard import PluggableWizard, WizardStep
from kiwi.ui.delegates import GladeSlaveDelegate

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.base.dialogs import RunnableView


class BaseWizardStep(WizardStep, GladeSlaveDelegate):
    """A wizard step base class definition"""
    gladefile = None

    def __init__(self, conn, wizard, previous=None):
        self.conn = conn
        self.wizard = wizard
        WizardStep.__init__(self, previous)
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)


class WizardEditorStep(BaseEditorSlave, WizardStep):
    """A wizard step base class definition used when we have a model to be
    edited or created"""

    def __init__(self, conn, wizard, model=None, previous=None):
        self.wizard = wizard
        WizardStep.__init__(self, previous)
        BaseEditorSlave.__init__(self, conn, model)


class BaseWizard(PluggableWizard, RunnableView):
    """A wizard base class definition"""
    title = None
    size = ()

    def __init__(self, conn, first_step, model=None, title=None,
                 size=None, edit_mode=False):
        self.conn = conn
        self.model = model
        size = size or self.size
        title = title or self.title
        if not title:
            raise ValueError('A title argument is required')
        PluggableWizard.__init__(self, title=title, first_step=first_step,
                                 size=size, edit_mode=edit_mode)

    def cancel(self):
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

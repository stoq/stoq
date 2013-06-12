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
""" Basic slave definitions """

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditorSlave

_ = stoqlib_gettext


# FIXME: s/NoteSlave/NotesSlave/ and move this to stoqlib.gui.slaves.notesslave
class NoteSlave(BaseEditorSlave):
    """ Slave store general notes. The model must have an attribute 'notes'
    to work.
    """
    gladefile = 'NoteSlave'
    proxy_widgets = ('notes', )

    def __init__(self, store, model, visual_mode=False):
        self.model = model
        self.model_type = self.model_type or type(model)
        BaseEditorSlave.__init__(self, store, self.model,
                                 visual_mode=visual_mode)
        self.notes.set_accepts_tab(False)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    NoteSlave.proxy_widgets)

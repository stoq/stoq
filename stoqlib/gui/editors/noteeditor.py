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

from stoqlib.domain.base import Domain
from stoqlib.gui.editors.baseeditor import BaseEditor


class NoteEditor(BaseEditor):
    """ Simple editor that offers a label and a textview. """
    gladefile = "NoteSlave"
    proxy_widgets = ('notes', )
    size = (500, 200)

    def __init__(self, store, model, attr_name, title='', label_text=None,
                 visual_mode=False):
        assert model, (u"You must supply a valid model to this editor "
                       "(%r)" % self)
        self.model_type = type(model)
        self.title = title
        self.label_text = label_text
        self.attr_name = attr_name

        # Keep this for a later rollback.
        self.original_notes = model.notes

        BaseEditor.__init__(self, store, model, visual_mode=visual_mode)
        self._setup_widgets()

    def _setup_widgets(self):
        if self.label_text:
            self.notes_label.set_text(self.label_text)
        self.notes.set_accepts_tab(False)

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self.notes.set_property('model-attribute', self.attr_name)
        self.add_proxy(self.model, NoteEditor.proxy_widgets)

    def get_title(self, *args):
        return self.title

    def on_cancel(self):
        # FIXME: When Kiwi allows proxies to save upon confirm, apply this
        # here.
        # If model is not a Domain, changes to it can't be undone by a
        # store.rollback(). Therefore, we must do the rollback by hand.
        if not isinstance(self.model, Domain):
            self.model.notes = self.original_notes

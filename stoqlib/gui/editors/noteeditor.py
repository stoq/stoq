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


class Note(object):
    """A helper to generate notes on :class:`NoteEditor`

    You can use this as a temporary object to get notes when you
    don't have a real model to use.
    """

    def __init__(self, notes=u''):
        self.notes = notes

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.notes == other.notes


# FIXME: s/NoteEditor/NotesEditor/ and propagate that change to the module
class NoteEditor(BaseEditor):
    """ Simple editor that offers a label and a textview. """
    gladefile = "NoteSlave"
    proxy_widgets = ('notes', )
    size = (500, 200)

    def __init__(self, store, model, attr_name='notes', title=u'',
                 label_text=None, message_text=None, mandatory=False,
                 visual_mode=False, ok_button_label=None, cancel_button_label=None):
        """
        :param store: a store
        :param model: the model that's going to have it's notes edited
        :param attr_name: the name of the attribute that contains the
            text to be edited
        :param title: if not ``None``, will be used as the dialog's title
        :param label_text: the text that will be used as a description
            for the notes' text view. If ``None``, the default "Notes"
            will be used
        :param message_label: if not ``None``, it will be used
            to display a message at the top of the dialog
        :param mandatory: if we should set the notes' text view as
            mandatory, making the dialog impossible to confirm if
            the notes are empty
        :param visual_mode: if we are working on visual mode
        """
        assert model, (u"You must supply a valid model to this editor "
                       "(%r)" % self)
        self.model_type = type(model)
        self.title = title
        self.label_text = label_text
        self.message_text = message_text
        self.mandatory = mandatory
        self.attr_name = attr_name

        # Keep this for a later rollback.
        self.original_notes = getattr(model, attr_name)

        BaseEditor.__init__(self, store, model, visual_mode=visual_mode)
        self._setup_widgets()

        if ok_button_label is not None:
            self.main_dialog.ok_button.set_label(ok_button_label)
        if cancel_button_label is not None:
            self.main_dialog.cancel_button.set_label(cancel_button_label)

    #
    # Private
    #

    def _setup_widgets(self):
        if self.message_text:
            self.message_label.set_text(self.message_text)
            self.message_label.set_visible(True)
        if self.label_text:
            self.observations_label.set_text(self.label_text)
        self.notes.set_accepts_tab(False)
        self.notes.set_property('mandatory', self.mandatory)

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
            setattr(self.model, self.attr_name, self.original_notes)

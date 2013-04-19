# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##


import gobject
import gtk

from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.feedbackdialog import FeedbackDialog
from stoqlib.lib.translation import stoqlib_gettext as _


class ShellStatusbar(gtk.Statusbar):
    __gtype_name__ = 'ShellStatusbar'

    def __init__(self, window):
        gtk.Statusbar.__init__(self)
        self._disable_border()
        self.message_area = self._create_message_area()
        self._create_default_widgets()
        self.shell_window = window

    def _disable_border(self):
        # Disable border on statusbar
        children = self.get_children()
        if children and isinstance(children[0], gtk.Frame):
            frame = children[0]
            frame.set_shadow_type(gtk.SHADOW_NONE)

    def _create_message_area(self):
        for child in self.get_children():
            child.hide()
        area = gtk.HBox(False, 4)
        self.add(area)
        area.show()
        return area

    def _create_default_widgets(self):
        alignment = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        # FIXME: These looks good on Mac, might need to tweak
        # on Linux to look good
        alignment.set_padding(2, 3, 5, 5)
        self.message_area.pack_start(alignment, True, True)
        alignment.show()

        widget_area = gtk.HBox(False, 0)
        alignment.add(widget_area)
        widget_area.show()

        self._text_label = gtk.Label()
        self._text_label.set_alignment(0.0, 0.5)
        widget_area.pack_start(self._text_label, True, True)
        self._text_label.show()

        vsep = gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()
        from stoqlib.gui.stockicons import STOQ_FEEDBACK
        self._feedback_button = gtk.Button(_('Feedback'))
        image = gtk.Image()
        image.set_from_stock(STOQ_FEEDBACK, gtk.ICON_SIZE_MENU)
        self._feedback_button.set_image(image)
        image.show()
        self._feedback_button.set_can_focus(False)
        self._feedback_button.connect('clicked',
                                      self._on_feedback__clicked)
        self._feedback_button.set_relief(gtk.RELIEF_NONE)
        widget_area.pack_start(self._feedback_button, False, False, 0)
        self._feedback_button.show()

        vsep = gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()

    def do_text_popped(self, ctx, text):
        self._text_label.set_label(text)

    def do_text_pushed(self, ctx, text):
        self._text_label.set_label(text)

    #
    # Callbacks
    #

    def _on_feedback__clicked(self, button):
        if self.shell_window.current_app:
            screen = self.shell_window.current_app.app_name + ' application'
        else:
            screen = 'launcher'
        run_dialog(FeedbackDialog, self.get_toplevel(), screen)

gobject.type_register(ShellStatusbar)

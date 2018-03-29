# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
#  Author(s): Stoq Team <stoq-devel@async.com.br>
#

from gi.repository import Gtk


class Section(Gtk.Box):
    """A simple section marker

    This is just a label with a line in front of it.
    """
    __gtype_name__ = 'Section'

    def __init__(self, title):
        super(Section, self).__init__()
        self.set_name('Section')
        label = Gtk.Label.new(title)
        label.set_xalign(0)
        label.get_style_context().add_class('h1')

        sep = Gtk.Separator()
        sep.set_hexpand(True)
        sep.set_valign(Gtk.Align.CENTER)
        self.pack_start(label, False, False, 6)
        self.pack_start(sep, True, True, 6)

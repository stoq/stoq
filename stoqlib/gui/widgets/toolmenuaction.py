# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source
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
##

import gobject
import gtk


class ToolMenuAction(gtk.Action):
    def add_actions(self, uimanager, actions, add_separator=True, position=None):
        new_item = self.get_proxies()[0]
        # FIXME: Temporary workaround until set_tool_item_type works
        if not hasattr(new_item, 'get_menu'):
            return []
        menu = new_item.get_menu()

        menu_items = []
        # Insert a separator only if menu already had children
        if add_separator and len(menu.get_children()):
            sep = gtk.SeparatorMenuItem()
            sep.set_visible(True)
            menu_items.append(sep)
            menu.prepend(sep)

        # Do this reversed because we are prepending
        for action in reversed(actions):
            action.set_accel_group(uimanager.get_accel_group())
            menu_item = action.create_menu_item()
            # Toolmenus doesn't use the trailing '...' menu pattern
            menu_item.set_label(menu_item.get_label().replace('...', ''))
            menu_items.append(menu_item)
            if position is not None:
                menu.insert(menu_item, position)
            else:
                menu.prepend(menu_item)

        return menu_items


gobject.type_register(ToolMenuAction)

# FIXME: This is at least present in PyGTK 2.22
MenuToolButton = getattr(gtk, 'MenuToolButton', None)
if MenuToolButton is None:
    MenuToolButton = gobject.type_from_name('GtkMenuToolButton').pytype

ToolMenuAction.set_tool_item_type(MenuToolButton)

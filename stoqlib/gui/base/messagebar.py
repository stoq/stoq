# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import gtk


class MessageBar(gtk.InfoBar):
    def __init__(self, message, message_type=None):
        if message_type is None:
            message_type = gtk.MESSAGE_INFO
        self.label = gtk.Label(message)
        self.label.set_use_markup(True)
        self.label.set_line_wrap(True)
        self.label.set_width_chars(100)
        self.label.set_alignment(0, 0)
        self.label.set_padding(12, 0)
        self.label.show()

        gtk.InfoBar.__init__(self)
        self.get_content_area().add(self.label)
        self.set_message_type(message_type)

    def set_message(self, message, message_type=None):
        """Sets or update a new message in the message bar. Can also be used to
        change the message type

        :param message: the message to be displayed
        :param message_type: defines the color and urgency of a message. One of
          gtk.MESSAGE_* .
        """
        # If the message type changed
        if message_type:
            self.set_message_type(message_type)

        self.label.set_text(message)

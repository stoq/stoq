# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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

"""Events used in the domain code
"""

from stoqlib.lib.event import Event


#
# Application events
#

class StartApplicationEvent(Event):
    """Emmited when an application is activated

    :param appname: the name of the application
    :param app: the app itself
    """


class StopApplicationEvent(Event):
    """Emmited when an application is deactivated

    :param appname: the name of the application
    :param app: the app itself
    """


#
# Dialog events
#

class DialogCreateEvent(Event):
    """Emited when a dialog is instantialized

    :param dialog: an instance of :class:`stoqlib.gui.base.dialogs.BasicDialog`
    """


class EditorSlaveCreateEvent(Event):
    """Emited when a dialog is instantialized

    :param editor: a subclass of
        :class:`stoqlib.gui.editor.baseeditor.BaseEditorSlave`
    :param model: a subclass of :class:`stoqlib.domain.base.Domain`
    :param conn: the connection used in editor and model
    :param visual_mode: a bool defining if the editor was created
        on visual_mode.
    """


#
# CouponCreatedEvent
#

class CouponCreatedEvent(Event):
    pass

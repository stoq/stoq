# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## Foundation, Outc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

from gi.repository import Gtk

from stoqlib.lib.translation import stoqlib_gettext as _


def render_icon(icon_name, size):
    theme = Gtk.IconTheme.get_default()
    return theme.load_icon(icon_name, size, Gtk.IconLookupFlags.FORCE_SVG)


def get_workorder_state_icon(work_order):
    """Get a stockicon for work_order

    This icon can be used to display a visual hint that the |workorder|
    is in some state (e.g. In transport, rejected) together with a tooltip
    that can be used on that icon when rendered.

    :param work_order: a |workorder|
    :returns: a tuple containing (stock_id, tooltip). Those 2 can
        be ``None`` if the state is not threated here
    """
    # This is ordered by priority
    if work_order.is_in_transport():
        from stoq.lib.gui.stockicons import STOQ_TRANSPORTER
        return STOQ_TRANSPORTER, _(u"In transport")
    elif work_order.is_rejected:
        return Gtk.STOCK_DIALOG_WARNING, _(u"Rejected")
    elif work_order.is_approved():
        return Gtk.STOCK_APPLY, _(u"Approved")

    return (None, None)


def get_delivery_state_icon(delivery):
    """Get a stockicon for the delivery.

    This icon can be used to display a visual hint that the |delivery|
    is in some state together with a tooltip that can be used on that
    icon when rendered.

    :param delivery: a |delivery|
    :returns: a tuple containing (stock_id, tooltip). Those 2 can
        be ``None`` if the state is not threated here
    """
    # FIXME
    return (None, None)

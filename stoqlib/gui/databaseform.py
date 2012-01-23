# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.uiform import UIForm


class DatabaseForm(object):
    def __init__(self, conn, form_name):
        self.conn = conn
        self.form_name = form_name
        self.form = UIForm.selectOneBy(form_name=form_name,
                                  connection=conn)

    def update_widget(self, widget, field_name=None, other=None):
        if not self.form:
            return
        if field_name is None:
            field_name = widget.model_attribute
        field = self.form.get_field(field_name)
        if field is None:
            return
        widget.props.mandatory = field.mandatory
        widget.props.visible = field.visible
        if other:
            if type(other) not in [list, tuple]:
                other = [other]
            for o in other:
                o.props.visible = field.visible

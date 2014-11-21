# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
""" Templating """

from kiwi.environ import environ
from mako.lookup import TemplateLookup
from mako.template import Template


def render_template(filename, **ns):
    """Renders a template giving a filename and a keyword dictionary
    @filename: a template filename to render
    @kwargs: keyword arguments to send to the template
    @return: the rendered template
    """
    directories = environ.get_resource_filename('stoq', 'template')
    lookup = TemplateLookup(directories=directories,
                            output_encoding='utf8', input_encoding='utf8',
                            default_filters=['h'])
    tmpl = lookup.get_template(filename)

    return tmpl.render(**ns)


def render_template_string(template, **ns):
    """Renders a template giving a string and a keyword dictionary
    :param str template: a template filename to render
    :param kwargs: keyword arguments to send to the template
    :return: the rendered template
    """
    return Template(template,
                    output_encoding='utf8', input_encoding='utf8',
                    default_filters=['h']).render(**ns)

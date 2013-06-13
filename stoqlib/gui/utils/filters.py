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

import gtk

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


def get_filters_for_images():
    """Return a list with a single gtk.FileFilter for all images
    """
    ffilter = gtk.FileFilter()
    ffilter.set_name(_('All Images'))
    ffilter.add_pixbuf_formats()
    return [ffilter]


def get_filters_for_attachment():
    """This function creates a list of gtk.FileFilter to be used when choosing
    a file for attachment.
    :returns: a list of gtk.FileFilter
    """
    def add_mimetype_filter(filters, name, mimetype):
        ffilter = gtk.FileFilter()
        ffilter.set_name(name)
        ffilter.add_mime_type(mimetype)
        filters.append(ffilter)

    filters = []

    # Generates filter for all files.
    ffilter = gtk.FileFilter()
    ffilter.set_name(_('All Files'))
    ffilter.add_pattern('*')
    filters.append(ffilter)

    # Add a filter for all images.
    filters.extend(get_filters_for_images())

    add_mimetype_filter(filters, _('PDF'), 'application/pdf')
    add_mimetype_filter(filters, _('Text'), 'text/plain')

    return filters

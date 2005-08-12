# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2005 Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

import gettext
import os.path

# This sort of sucks, but it's the cheapest solution for now.

# prefix = $DIR/..
# if a locale directoy exists in directory, be happy
# otherwise, check ../../../share/locale
# if any of them exist, pass in the path to gettext.bindtextdomain

prefix = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
locale = os.path.join(prefix, 'locale')
if not os.path.exists(locale):
    locale = os.path.abspath(os.path.join(prefix,
                                          '..', '..', '..',
                                          'share', 'locale'))

if os.path.exists(locale):
    gettext.bindtextdomain('stoqlib', locale)
    gettext.bind_textdomain_codeset('stoqlib', 'utf-8')

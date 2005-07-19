# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
lib/defaults.py

    Default values for Stoq applications.
"""
    
import datetime



#
# Defaults for dates
#



MONTH_PERIOD = 30

dtime_type = datetime.datetime
START_DATE = dtime_type.today()
END_DATE = dtime_type.today() + datetime.timedelta(days=MONTH_PERIOD)



#
# Defaults for Kiwi combobox
#



ALL_BRANCHES = _('All branches'), None


# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2011 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

program_name = "Stoq"
website = 'http://www.stoq.com.br'

#: Major version, should only increase when big, important features
#: are integrated.
major_version = 1

#: Minor version, increase when doing a new stable release
minor_version = 11

#: Micro version, increase when doing a bug fix for a stable release
micro_version = 0

#: extra version, rc1, rc2, etc goes here.
extra_version = ''

#: the date the software was released
release_date = (2016, 5, 20)

#: if this is a stable release
stable = True

#: stoq version as a tuple
stoq_version = (major_version, minor_version, micro_version)

#: stoq version as a string
version = '.'.join(map(str, stoq_version))

#: stoq version as a string, sans the extra version
short_version = version[:]

if extra_version:
    stoq_version = stoq_version + (extra_version,)
    version += extra_version

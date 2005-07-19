# -- Mode: Python; coding: iso-8859-1 --
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
lib/version.py:

    Stoq version, authors and contributors list.
"""

version      = (0,1,0)
release_date = (2005, 07, 14)

AUTHORS = """
Christian Robotton Reis         <kiko@async.com.br>
Evandro Vale Miquelito          <evandro@async.com.br>
Henrique Romano                 <henrique@async.com.br>
Daniel Saran Rodrigues da Cunha <daniel@async.com.br>
Lorenzo Gil Sanchez             <lgs@sicem.biz>
Johan Dahlin                    <jdahlin@async.com.br>
"""

CONTRIBUTORS= """
Bruno Trevisan                  <bt@async.com.br>
Ricardo Froehlich               <ricardo@async.com.br>
Juan Pinazo                     <pinazo@async.com.br>
"""

def get_members(strings):
    members_list = []
    for line in strings.split('\n'):
        if line.find('@') != -1:
            email = line.split()[-1]
            name = line[:-len(email)].strip()
            members_list.append((name, email))
    return members_list

authors = get_members(AUTHORS)
contributors = get_members(CONTRIBUTORS)


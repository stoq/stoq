# -*- coding: utf-8 -*-
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
"""Command line configuration options"""

import optparse


def get_option_parser():
    """
    Get the option parser used to parse arguments on the command line
    @returns: an optparse.OptionParser
    """

    # Note: only generic command line options here, specific ones
    #       should be added at callsite

    parser = optparse.OptionParser()

    group = optparse.OptionGroup(parser, 'General')
    group.add_option('-f', '--filename',
                     action="store",
                     type="string",
                     dest="filename",
                     default=None,
                     help='Use this file name for config file')
    group.add_option('-v', '--verbose',
                     action="store_true",
                     dest="verbose",
                     default=False)
    group.add_option('', '--sql',
                     action="store_true",
                     dest="sqldebug")
    group.add_option('', '--debug',
                     action="store_true",
                     dest="debug")
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Database access')
    group.add_option('-d', '--dbname',
                     action="store",
                     dest="dbname",
                     help='Database name to use')
    group.add_option('-H', '--hostname',
                     action="store",
                     dest="address",
                     help='Database address to connect to')
    group.add_option('-p', '--port',
                     action="store",
                     dest="port",
                     help='Database port')
    group.add_option('-u', '--username',
                     action="store",
                     dest="username",
                     help='Database username')
    group.add_option('-w', '--password',
                     action="store",
                     type="str",
                     dest="password",
                     help='user password',
                     default='')
    group.add_option('', '--no-load-config',
                     action='store_false',
                     help="do not load stoq.conf",
                     default=True,
                     dest='load_config')
    # These options are parsed in gtk_init() which is
    # called when the gtk module is imported.
    # To be able to use them and still have optparse complain
    # about invalid arguments we need to add fake verious of
    # them here.
    group.add_option('', '--g-fatal-warnings',
                     help=optparse.SUPPRESS_HELP,
                     action='store_true',
                     dest='fatal_warnings')
    parser.add_option_group(group)
    return parser

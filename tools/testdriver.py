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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Johan Dahlin             <jdahlin@async.com.br>
##

import optparse
import sys

from kiwi.python import namedAny

from stoqdrivers.devices.serialbase import SerialPort

def main(args):
    usage = "usage: %prog [options] command [args]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-t', '--type',
                      action="store",
                      dest="type",
                      default="printers",
                      help='Device type')
    parser.add_option('-b', '--brand',
                      action="store",
                      dest="brand",
                      help='Device brand')
    parser.add_option('-m', '--model',
                      action="store",
                      dest="model",
                      help='Device model')
    parser.add_option('-p', '--port',
                      action="store",
                      dest="port",
                      default="/dev/ttyS0",
                      help='Printer port')

    options, args = parser.parse_args(args)
    if len(args) < 2:
        raise SystemExit("Need a command")

    driver = namedAny('stoqdrivers.devices.%s.%s.%s.%s' % (
        options.type, options.brand, options.model, options.model))

    device = driver(port=SerialPort(options.port))

    command = args[1]
    cb = getattr(device, command)

    args = map(int, tuple(args[2:]))
    retval = cb(*args)
    if retval is not None:
        print '%s returned: %r' % (command, retval)
    return 0

if __name__  == '__main__':
    sys.exit(main(sys.argv))

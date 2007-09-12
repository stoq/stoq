# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Johan Dahlin              <jdahlin@async.com.br>
##
#
# Documentation references:
#
#   http://en.wikipedia.org/wiki/ESC/P
#   http://www.epson.co.uk/support/manuals/pdf/ESCP/Part_1.pdf
#   http://www.epson.co.uk/support/manuals/pdf/ESCP/Part_2.pdf
#
""" Driver for EPSON Esc/P and Esc/P2 printers. """

import struct

ESC = '\x1b'

CMD_INIT = '@'
CMD_PRINT_QUALITY = 'x'
CMD_PROPORTIONAL = 'p'
CMD_FORM_FEED = '\xff'
CMD_EJECT = '\x19'

QUALITY_DRAFT = '0'
QUALITY_LQ = '1'
QUALITY_NLQ = '1'

class EscPPrinter(object):
    def __init__(self, device):
        self.device = device
        self.fp = open(device, 'w')

        self._command(CMD_INIT)

    def _command(self, command, *args):
        chars = command
        for arg in args:
            if arg == True:
                v = '1'
            elif arg == False:
                v = '0'
            else:
                v = arg

            chars += v
        cmd = '%s%s' % (ESC, chars)
        self.send(cmd)

    def send(self, data):
        self.fp.write(data)
        self.fp.flush()

    def set_draft_mode(self):
        self._command(CMD_PRINT_QUALITY, QUALITY_DRAFT)

    def set_proportional(self, proportional):
        self._command(CMD_PROPORTIONAL, proportional)

    def done(self):
        self._command(CMD_INIT)

    def form_feed(self):
        self._command(CMD_FORM_FEED)

    def set_vertical_position(self, position):
        args = struct.pack('b', position)
        self._command('J', *args)

def test():
    printer = EscPPrinter('/dev/lp0')
    printer.send(
        'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. '
        'Ut a velit sit amet nisl hendrerit lacinia. Nunc eleifend '
        'cursus risus. Vivamus libero libero, dignissim ut, pulvinar id, '
        'blandit a, leo amet.\n'.upper())

    printer.done()

if __name__ == '__main__':
    test()

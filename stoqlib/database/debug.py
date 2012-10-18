# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import os
import sys
import fcntl
import termios
import struct

from storm.tracer import BaseStatementTracer

try:
    from sqlparse import engine, filters, sql
    has_sqlparse = True
except ImportError:
    has_sqlparse = False


# http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
def getTerminalSize():
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return None
        return cr

    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass

    if not cr:
        try:
            cr = (env['LINES'], env['COLUMNS'])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])

if has_sqlparse:
    class MyReindentFilter(filters.ReindentFilter):

        def __init__(self, max_width):
            self.max_width = max_width
            filters.ReindentFilter.__init__(self)

        def _process_identifierlist(self, tlist):
            identifiers = tlist.get_identifiers()
            if len(identifiers) > 1 and not tlist.within(sql.Function):
                # This is not working in some cases
                #first = list(identifiers[0].flatten())[0]
                #num_offset = self._get_offset(first) - len(first.value)
                num_offset = 7
                self.offset += num_offset
                width = self.offset
                for token in identifiers:
                    width += len(str(token)) + 2
                    if width > self.max_width:
                        tlist.insert_before(token, self.nl())
                        width = self.offset + len(str(token))
                self.offset -= num_offset

            self._process_default(tlist)
            return True

    def format_sql(statement):
        width, height = getTerminalSize()
        stack = engine.FilterStack()
        stack.enable_grouping()
        stack.stmtprocess.append(filters.StripWhitespaceFilter())
        stack.stmtprocess.append(MyReindentFilter(width - 30))
        stack.postprocess.append(filters.SerializerUnicode())
        statement = ''.join(stack.run(statement))

        lines = statement.split('\n')
        new_lines = [lines[0]]
        for line in lines[1:]:
            new_lines.append(' ' * 18 + line)
        statement = '\n'.join(new_lines)
        return statement


class StoqlibDebugTracer(BaseStatementTracer):
    ATTRIBUTES = dict(bold=1, dark=2, underline=4, blink=5,
                      reverse=7, concealed=8)
    COLORS = dict(grey=30, red=31, green=32, yellow=33, blue=34,
                  magenta=35, cyan=36, white=37)
    RESET = '\033[0m'

    def __init__(self, stream=None):
        if stream is None:
            stream = sys.stderr
        self._stream = stream

    def _colored(self, text, color=None, attrs=None):
        if os.getenv('ANSI_COLORS_DISABLED') is None:
            fmt_str = '\033[%dm%s'
            if color is not None:
                text = fmt_str % (self.COLORS[color], text)

            if attrs is not None:
                for attr in attrs:
                    text = fmt_str % (self.ATTRIBUTES[attr], text)

            text += self.RESET
        return text

    def _format_statement(self, statement):
        if has_sqlparse:
            statement = format_sql(statement)

        replaces = []
        if statement.startswith('SELECT'):
            color = 'blue'
            replaces = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'JOIN', 'LEFT',
                        'AND', 'OR', 'ORDER BY']
        elif statement.startswith('UPDATE'):
            color = 'yellow'
            replaces = ['UPDATE', 'SET', 'WHERE']
        elif statement.startswith('INSERT'):
            color = 'green'
            replaces = ['INSERT', 'INTO', 'VALUES']
        elif statement.startswith('DELETE'):
            color = 'red'
            replaces = ['DELETE', 'FROM', 'WHERE']

        for i in replaces:
            statement = statement.replace(i + ' ', self._colored(i, color) + ' ')
            statement = statement.replace(i + '\n', self._colored(i, color) + '\n')
        return statement

    def _expanded_raw_execute(self, connection, raw_cursor, statement):
        time = datetime.datetime.now().isoformat()[11:]
        statement = self._format_statement(statement)

        self._stream.write(
            "[%s] %s\n" % (self._colored(time, 'grey', ['bold']), statement))
        self._stream.flush()

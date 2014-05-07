# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2012-2013 Async Open Source <http://www.async.com.br>
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
import platform
import struct

import psycopg2

from storm.tracer import BaseStatementTracer, install_tracer

try:
    from sqlparse import engine, filters, sql
    has_sqlparse = True
except ImportError:
    has_sqlparse = False


# http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
def getTerminalSize():
    if platform.system() != 'Linux':
        return 80, 20

    import fcntl
    import termios
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return 80, 20
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
            identifiers = list(tlist.get_identifiers())
            if len(identifiers) > 1 and not tlist.within(sql.Function):
                # This is not working in some cases
                # first = list(identifiers[0].flatten())[0]
                # num_offset = self._get_offset(first) - len(first.value)
                num_offset = 7
                self.offset += num_offset
                width = self.offset
                for token in identifiers:
                    width += len(str(token)) + 2
                    if width > self.max_width:
                        tlist.insert_before(token, self.nl())
                        width = self.offset + len(str(token))
                self.offset -= num_offset

            return True

    def format_sql(statement, prefix_length=0):
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
            new_lines.append(' ' * prefix_length + line)
        statement = '\n'.join(new_lines)
        return statement


class StoqlibDebugTracer(BaseStatementTracer):
    ATTRIBUTES = dict(bold=1, dark=2, underline=4, blink=5,
                      reverse=7, concealed=8)
    COLORS = dict(grey=30, red=31, green=32, yellow=33, blue=34,
                  magenta=35, cyan=36, white=37)
    RESET = '\033[0m'   # pylint: disable=W1401

    def __init__(self, stream=None):
        # This colors will be used to highlight the transaction
        self._available_colors = ['blue', 'green', 'magenta', 'yellow', 'cyan',
                                  'red']
        self._current_color = 0
        # Mapping pid > color
        self._transactions = {}
        # Mapping pid > query count
        self._transactions_count = {}

        if stream is None:
            stream = sys.stderr
        self._stream = stream

    def _colored(self, text, color=None, attrs=None):
        if os.getenv('ANSI_COLORS_DISABLED') is None:
            fmt_str = '\033[%dm%s'   # pylint: disable=W1401
            if color is not None:
                text = fmt_str % (self.COLORS[color], text)

            if attrs is not None:
                for attr in attrs:
                    text = fmt_str % (self.ATTRIBUTES[attr], text)

            text += self.RESET
        return text

    def _format_statement(self, statement, header_size):
        if has_sqlparse:
            statement = format_sql(statement, header_size)

        replaces = []
        if statement.startswith('SELECT'):
            color = 'blue'
            replaces = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'JOIN', 'LEFT',
                        'AND', 'OR', 'ORDER BY']
        elif statement.startswith('UPDATE'):
            color = 'yellow'
            replaces = ['UPDATE', 'SET', 'WHERE']
        elif statement.startswith('INSERT INTO transaction_entry'):
            # transaction entry inserting is quite common and always the same query.
            # Make it less prominent
            statement = self._colored(statement, 'white')
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

    def write(self, msg):
        self._stream.write(msg)
        self._stream.flush()

    def header(self, pid, color, header, tail='\n'):
        pid = self._colored('%s' % pid, color)
        header = self._colored('%5s' % header, 'grey', ['bold'])

        self.write("[%s %s]%s" % (pid, header, tail))

    def _expanded_raw_execute(self, transaction, raw_cursor, statement):
        pid = raw_cursor.connection.get_backend_pid()
        self._transactions_count.setdefault(pid, 0)
        self._transactions_count[pid] += 1
        count = self._transactions_count[pid]
        header_size = 9 + len(str(pid))
        color = self._get_transaction_color(pid)
        pid = self._colored(pid, color)

        self._start_time = datetime.datetime.now()
        self.statement = self._format_statement(statement, header_size)

        # Dont write new line, so we can print the time at the end
        self.header(pid, color, count, tail=' ')
        self.write(self.statement + '\n')

    def connection_raw_execute_success(self, transaction, raw_cursor, statement,
                                       params):
        pid = raw_cursor.connection.get_backend_pid()
        header_size = 9 + len(str(pid))
        now = datetime.datetime.now()
        duration = now - self._start_time
        seconds = duration.seconds + float(duration.microseconds) / 10 ** 6
        rows = raw_cursor.rowcount

        text = '%s%s seconds | %s rows | %s' % (
            ' ' * header_size,
            self._colored(seconds, attrs=['bold']),
            self._colored(rows, attrs=['bold']),
            self._colored(now.strftime('%F %T.%f'), attrs=['bold']))

        if statement.startswith('INSERT') and rows == 1:
            try:
                rowid = raw_cursor.fetchone()[0]
                raw_cursor.scroll(-1)
                text += ' | id: ' + self._colored(repr(rowid), attrs=['bold'])
            except psycopg2.ProgrammingError:
                text = ''
        self.write(text + '\n')

    def _get_transaction_color(self, pid):
        if pid not in self._transactions:
            self._transactions[pid] = self._available_colors[self._current_color]
            self._current_color += 1
            if self._current_color == len(self._available_colors):
                self._current_color = 0
        return self._transactions[pid]

    def transaction_create(self, store):
        pid = store._connection._raw_connection.get_backend_pid()
        color = self._get_transaction_color(pid)

        self.header(pid, color, 'BEGIN')

    def transaction_commit(self, store):
        pid = store._connection._raw_connection.get_backend_pid()
        color = self._get_transaction_color(pid)
        self.header(pid, color, 'COMIT')

    def transaction_rollback(self, store, xid=None):
        pid = store._connection._raw_connection.get_backend_pid()
        color = self._get_transaction_color(pid)
        self.header(pid, color, 'ROLLB')

    def transaction_close(self, store):
        pid = store._connection._raw_connection.get_backend_pid()
        color = self._get_transaction_color(pid)
        del self._transactions[pid]

        self.header(pid, color, 'CLOSE')


def enable():
    install_tracer(StoqlibDebugTracer())

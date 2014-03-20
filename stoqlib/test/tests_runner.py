# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br> ##

import doctest
import os
import re
import sys

import nose
from nose.plugins.doctests import DocFileCase
from nose.plugins import Plugin

import stoqlib


#
# YANC nose plugin
# Copyright 2011-2013 Arthur Noel
#

_RESET = '\033[0m'  # pylint: disable=W1401
_ATTRIBUTES = dict(
    bold=1, dark=2, underline=4, blink=5, reverse=7, concealed=8)
_COLORS = dict(
    grey=30, red=31, green=32, yellow=33, blue=34, magenta=35, cyan=36, white=37)


def _colored(text, color=None, attrs=None):
    if os.getenv('ANSI_COLORS_DISABLED') is None:
        fmt_str = '\033[%dm%s'  # pylint: disable=W1401
        if color is not None:
            text = fmt_str % (_COLORS[color], text)

        if attrs is not None:
            for attr in attrs:
                text = fmt_str % (_ATTRIBUTES[attr], text)

        text += _RESET
    return text


class ColorStream(object):
    _colors = {
        "green": ("OK", "ok", "."),
        "red": ("ERROR", "FAILED", "errors", "E"),
        "yellow": ("FAILURE", "FAIL", "failures", "F"),
        "magenta": ("SKIP", "S"),
        "blue": ("-" * 70, "=" * 70),
    }

    def __init__(self, stream):
        self._stream = stream
        self._color_map = {}
        self._patten_map = {}
        for color, labels in self._colors.items():
            for label in labels:
                self._color_map[label] = color
                if len(label) > 1:
                    self._patten_map[label] = re.compile(r"%s=\d+" % label)

    def __getattr__(self, key):
        return getattr(self._stream, key)

    def _colorize(self, string, color=None):
        if not string or color is not None:
            return string

        color = self._color_map.get(string)
        if color is None:
            for key in self._color_map:
                # looking for a test failure as LABEL: str(test)
                if string.startswith(key + ":"):
                    segments = string.split(":")
                    label = self._colorize(segments[0] + ":",
                                           self._color_map[key])
                    desc = ":".join(segments[1:])
                    if desc.startswith(" Failure: "):
                        desc = _colored(desc, self._color_map[key])
                    return label + desc
            for key, key_color in self._color_map.items():
                # looking for label=number in the summary
                pattern = self._patten_map.get(key)
                if pattern is not None:
                    for match in pattern.findall(string):
                        string = string.replace(
                            match, self._colorize(match, key_color))
        if color is not None:
            string = _colored(string, color, attrs=("bold",))
        return string

    def write(self, string):
        self._stream.write(self._colorize(string))

    def writeln(self, string=""):
        self._stream.writeln(self._colorize(string))


class YANC(Plugin):
    """Yet another nose colorer"""

    name = "yanc"
    previous_path = None
    previous_klass = None

    def options(self, parser, env):
        super(YANC, self).options(parser, env)

    def configure(self, options, conf):
        super(YANC, self).configure(options, conf)
        self.color = (
            hasattr(self.conf, "stream") and
            hasattr(self.conf.stream, "isatty") and
            self.conf.stream.isatty())

    def startContext(self, context):
        self.should_format = True

    def stopContext(self, context):
        self.should_format = False

    def describeTest(self, test):
        path = test.id()
        parts = path.split('.')

        method = parts.pop()
        try:
            klass = parts.pop()
        except IndexError:
            return test.test._dt_test.filename[len(os.getcwd()) + 1:]

        path = '.'.join(parts)
        return '%s:%s.%s' % (path, klass, method)

    def begin(self):
        if self.color:
            self.conf.stream = ColorStream(self.conf.stream)

    def finalize(self, result):
        if self.color:
            self.conf.stream = self.conf.stream._stream


#
# Stoq nose plugin
#

class Stoq(Plugin):
    """Stoq plugin for nose tests

    This plugin is reponsible for setting up the environment so Stoq
    and it's plugins can be tested right.
    """

    name = "stoq"

    def begin(self):
        # The tests require that the environment is currently set to C, to avoid
        # translated strings and use the default date/number/currency formatting
        os.environ['LC_ALL'] = 'C'
        os.environ['LANG'] = 'C'
        os.environ['LANGUAGE'] = 'C'

        if 'STOQ_USE_GI' in os.environ:
            from stoq.lib import gicompat
            gicompat.enable()

        # If we import tests.base before Cover.setup() in the coverage plugin
        # is called the statistics will skip the modules imported by tests.base
        from stoqlib.database.testsuite import bootstrap_suite

        hostname = os.environ.get('STOQLIB_TEST_HOSTNAME')
        dbname = os.environ.get('STOQLIB_TEST_DBNAME')
        username = os.environ.get('STOQLIB_TEST_USERNAME')
        password = os.environ.get('STOQLIB_TEST_PASSWORD')
        port = int(os.environ.get('STOQLIB_TEST_PORT') or 0)
        quick = os.environ.get('STOQLIB_TEST_QUICK', None) is not None

        config = os.path.join(
            os.path.dirname(stoqlib.__file__), 'tests', 'config.py')
        if os.path.exists(config):
            execfile(config, globals(), locals())

        bootstrap_suite(address=hostname, dbname=dbname, port=port,
                        username=username, password=password, quick=quick)


# The doctests plugin in nosetests 1.1.2 doesn't have --doctest-options,
# which we need to set to ELLIPSIS, so monkeypatch that support in.
# We can remove this monkeypatch as soon as we migrate to trusty
def _init(self, test, optionflags=0, setUp=None, tearDown=None,
          checker=None, obj=None, result_var='_'):
    self._result_var = result_var
    self._nose_obj = obj
    super(DocFileCase, self).__init__(
        test, optionflags=doctest.ELLIPSIS | doctest.REPORT_ONLY_FIRST_FAILURE,
        setUp=setUp, tearDown=tearDown,
        checker=checker)
DocFileCase.__init__ = _init


def _collect_coverage_modules(filenames):
    # Collects a list of coverage modules given a set of filenames

    # stoqlib/domain -> stoqlib.domain
    # stoqlib/domain/test -> stoqlib.domain
    # stoqlib/domain/test/test_account -> stoqlib.domain.account
    # stoqlib/domain/test/test_account.py -> stoqlib.domain.account
    # (for instance via __tests__ global attribute in test_account.py)
    for filename in filenames:
        if os.path.isdir(filename):
            filename = filename.rstrip('/')
            if filename.endswith('/test'):
                filename = filename[:-5]
            yield filename.replace('/', '.')
            continue

        try:
            fd = open(filename)
        except IOError:
            continue

        for line in fd.readlines():
            if not line.startswith('__tests__'):
                continue
            line = line[:-1]
            test_filename = line.split(' = ', 1)[1][1:-1]
            if test_filename.endswith('.py'):
                test_filename = test_filename[:-3]
            test_filename = test_filename.replace('/', '.')
            yield test_filename
            break

# FIXME: This is mimicking what is done on the module containing the IPlugin
# implemented class. Different from stoq that will always import that module,
# nosetests will try to look for tests in each .py, producing ImportErrors.
# This can be removed when the plugins import situation is solved.
plugins_topdir = os.path.join(
    os.path.dirname(os.path.dirname(stoqlib.__file__)), 'plugins')
for plugin_dir in os.listdir(plugins_topdir):
    sys.path.append(os.path.join(plugins_topdir, plugin_dir))


def main(args, extra_plugins=None):
    if '--sql' in args:
        args.remove('--sql')
        from stoqlib.database.debug import enable
        enable()

    if '--coverage' in args:
        args.remove('--coverage')
        modules = _collect_coverage_modules(args)
        if modules:
            args.append('--with-coverage')
            args.append('--cover-package=%s' % (','.join(modules), ))

    for extra_option in [
        # Disable capturing of stdout, we often use this for print debugging
        '--nocapture',
        # Disable logging capture, kiwi is quite verbose and doesn't give
        # a lot of useful information
        '--nologcapture',
        # Be verbose, one line per test instead of just a dot (like trial)
        '--verbose',
        # Detailed errors, useful for tracking down assertEquals
        '--detailed-errors',
        # Enable doctests
        '--with-doctest',
        # Our doctests ends with .txt, eg sellable.txt
        '--doctest-extension=txt']:
        if not extra_option in args:
            args.append(extra_option)

    plugins = [Stoq(), YANC()]
    if extra_plugins is not None:
        plugins.extend(extra_plugins)

    # --with-plugin must be the last args
    for p in plugins:
        args.append('--with-%s' % p.name)

    return nose.main(argv=args, addplugins=plugins)

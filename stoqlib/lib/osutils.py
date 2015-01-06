# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import errno
import fnmatch
import locale
import logging
import os
import platform

_system = platform.system()
log = logging.getLogger(__name__)


def _get_xdg_dir(envname, default):
    default = os.path.expanduser(default)
    filename = os.path.expanduser("~/.config/user-dirs.dirs")
    try:
        f = open(filename)
    except IOError as e:
        if e.errno == errno.ENOENT:
            return default
    for line in f:
        if line.startswith(envname):
            return os.path.expandvars(line[len(envname) + 2:-2])
    return default


def get_application_dir(appname="stoq"):
    """Fetches a application specific directory,
    this can be used to save temporary files and other state.
    This also creates the directory if it doesn't exist
    :returns: the application directory
    """
    if _system == 'Linux':
        appdir = os.path.join(os.environ['HOME'], '.' + appname)
    elif _system == 'Windows':
        appdir = os.path.join(os.environ['APPDATA'], appname)
    elif _system == 'Darwin':
        appdir = os.path.join(os.environ['HOME'], 'Library',
                              'Application Support', 'Stoq')
    else:
        raise SystemExit("unknown system: %s" % (_system, ))
    if not os.path.exists(appdir):
        os.makedirs(appdir)
    return appdir


def get_documents_dir():
    """:returns: the documents dir for the current user"""
    if _system == 'Linux':
        return _get_xdg_dir("XDG_DOCUMENTS_DIR", "~/Documents")
    elif _system == 'Windows':
        from win32com.shell import shell
        MY_DOCUMENTS = "::{450d8fba-ad25-11d0-98a8-0800361b1103}"
        folder = shell.SHGetDesktopFolder()
        pidl = folder.ParseDisplayName(0, None, MY_DOCUMENTS)[1]
        return shell.SHGetPathFromIDList(pidl)
    elif _system == 'Darwin':
        return os.path.join(os.environ['HOME'], 'Documents')
    else:
        raise SystemExit("unknown system: %s" % (_system, ))


def get_username():
    """:returns: the current username"""
    if _system == 'Linux' or _system == 'Darwin':
        return os.environ.get('USER')
    elif _system == 'Windows':
        return os.environ['USERNAME']
    else:
        raise SystemExit("unknown system: %s" % (_system, ))


def read_registry_key(root, key, value):
    """Reads a registry key and return it's value.
    None is returned if the value couldn't be read
    """
    if platform.system() != 'Windows':
        return None
    import exceptions
    import _winreg

    if root == 'HKCC':
        root = _winreg.HKEY_CURRENT_USER
    elif root == 'HKLM':
        root = _winreg.HKEY_LOCAL_MACHINE
    else:
        raise ValueError(root)

    try:
        k = _winreg.OpenKey(root, key)
        reg_value, key_type = _winreg.QueryValueEx(k, value)
    except exceptions.WindowsError:
        # log.info('Error while reading %s/%s/%s: %r' % (root, k, value, e))
        return None
    return reg_value


def list_recursively(directory, pattern):
    """Returns files recursively from directory matching pattern
    :param directory: directory to list
    :param pattern: glob mattern to match
    """
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, pattern):
            # skip backup files
            if (filename.startswith('.#') or
                filename.endswith('~')):
                continue
            matches.append(os.path.join(root, filename))
    return matches


def find_program(program):
    """Looks for program in PATH.
    :param program: name of the program to find
    :returns: the complete path of the program or None if it couldn't be found
    """
    for path in os.environ['PATH'].split(':'):
        fullpath = os.path.join(path, program)
        if os.path.exists(fullpath):
            return fullpath


def get_system_locale():
    """Fetches the current locale according to the system.

    :returns: the current locale
    """
    # Locale comes in a tuple like ('en_US', 'UTF-8')
    if _system == 'Linux':
        lang = locale.getlocale(locale.LC_MESSAGES)
    elif _system == 'Windows':
        lang = locale.getlocale(locale.LC_ALL)
    elif _system == 'Darwin':
        lang = locale.getlocale(locale.LC_ALL)
    else:
        raise SystemExit("unknown system: %s" % (_system, ))
    return lang[0]


def get_product_key():
    """Fetches the product key

    :returns: the product key
    """
    if _system == 'Linux':
        app_dir = get_application_dir()
        filename = os.path.join(app_dir, "product_key")
        try:
            return open(filename).read()
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
        return None
    elif _system == 'Windows':
        product_key = read_registry_key('HKCC', r'Software\Stoq',
                                        'ProductKey')
    elif _system == 'Darwin':
        product_key = None
    else:
        raise SystemExit("unknown system: %s" % (_system, ))

    return product_key

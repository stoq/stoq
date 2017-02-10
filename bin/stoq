#!/usr/bin/env python
#
# Copyright (C) 2005-2011 by Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import string
import sys

if hasattr(sys, 'frozen'):
    # We're using py2exe:
    # - no need to check python version
    # - no need to setup python path
    # - no need to workaround setuptools
    # By default, when using py2exe, there is only one item in PYTHONPATH, and
    # thats the library.zip it created. We are also adding some eggs (including
    # stoq, kiwi and stoqdrivers), so make sure those are also in the path
    executable = os.path.realpath(os.path.abspath(sys.executable))
    root = os.path.dirname(executable)
    for name in os.listdir(root):
        if not name.endswith(('.egg', 'whl')):
            continue
        sys.path.insert(0, os.path.join(root, name))

    # Also add it to the OS PATH, so that the libraries are correclty found.
    os.environ['PATH'] = root + os.pathsep + os.environ['PATH']
else:
    # Required version of Python
    REQUIRED_VERSION = (2, 6)

    # Directory name, defaults to name of binary, it is relative to ..
    # a, __init__.py and main.py is expected to be found there.
    DIRNAME = None

    # Application name, defaults to capitalized name of binary
    APPNAME = None

    # Do not modify code below this point
    dirname = DIRNAME or os.path.split(sys.argv[0])[1]
    appname = APPNAME or dirname.capitalize()

    if sys.version_info[0] == 3:
        raise SystemExit("ERROR: Sorry, Stoq is not yet compatible with Python 3.x.")

    if sys.hexversion < int('%02x%02x0000' % REQUIRED_VERSION, 16):
        raise SystemExit("ERROR: Python %s or higher is required to run %s, "
                         "%s found" % ('.'.join(map(str, REQUIRED_VERSION)),
                                       appname,
                                       string.split(sys.version)[0]))

    # Disable Ubuntus scrollbar, if it's not set, users can
    # force it by setting LIBOVERLAY_SCROLLBAR=1
    import os
    if os.environ.get('LIBOVERLAY_SCROLLBAR') != '1':
        os.environ['LIBOVERLAY_SCROLLBAR'] = '0'

    # FIXME: The gail module is misbehaving on xenial and making Stoq
    # segfault on some ocasions, and since pygtk/gtk2 has been deprecated,
    # this is not something that is going to be fixed. Disable it for
    # now but we can reenable it once we migrate our codebase to gtk3
    if 'gail' in os.environ.get('GTK_MODULES', ''):
        mods = os.environ['GTK_MODULES'].split(':')
        os.environ['GTK_MODULES'] = ':'.join(
            m for m in mods if m not in ['gail', 'atk-bridge'])

    # Disable global menu for stoq, since it breakes the order and removal of
    # our dinamic menus
    os.environ['UBUNTU_MENUPROXY'] = '0'


# We only support portuguese locale on Windows for now
import platform
if platform.system() == 'Windows':
    import errno
    import locale
    import os
    from ctypes import cdll

    def putenv(key, value):
        os.environ[key] = value
        cdll.msvcrt._putenv('%s=%s' % (key, value, ))

    locale.setlocale(locale.LC_ALL, '')
    putenv('LANGUAGE', 'pt_BR')

    stoq_dir = os.path.join(os.environ['ALLUSERSPROFILE'], 'stoq')
    os.environ['PGPASSFILE'] = os.path.join(stoq_dir, 'pgpass.conf')
    logdir = os.path.join(stoq_dir, 'logs')
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    # http://www.py2exe.org/index.cgi/StderrLog
    if not sys.argv[0].startswith('stoq-cmd'):
        for name in ['stdout', 'stderr']:
            filename = os.path.join(logdir, name + ".log")
            try:
                fp = open(filename, "w")
            except IOError, e:
                if e.errno != errno.EACCES:
                    raise
                fp = open(os.devnull, "w")
            setattr(sys, name, fp)


if len(sys.argv) > 1 and sys.argv[1] == 'dbadmin':
    from stoq.dbadmin import main
    sys.argv.pop(1)
else:
    from stoq.main import main

try:
    sys.exit(main(sys.argv))
except KeyboardInterrupt:
    raise SystemExit

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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

import sys

from gi.repository import Gtk, GObject

try:
    from aptdaemon.client import AptClient
    from aptdaemon.enums import ERROR_UNKNOWN
    from aptdaemon.errors import NotAuthorizedError, TransactionFailed
    from aptdaemon.gtk3widgets import (AptErrorDialog, AptProgressDialog,
                                       AptConfirmDialog)
    has_apt = True
except ImportError:
    has_apt = False


class PackageInstaller(GObject.GObject):

    __gsignals__ = {
        'auth-failed': (GObject.SIGNAL_RUN_LAST, None, ()),
        'done': (GObject.SIGNAL_RUN_LAST, None, (object, )),
    }

    def __init__(self):
        super(PackageInstaller, self).__init__()

        self._client = AptClient()

    #
    #  Public API
    #

    def install(self, *packages):
        def reply(transaction):
            transaction.connect('finished', self._on_transaction__finished)
            self._transaction = transaction
            # dependencis not available on lucid
            for p in getattr(transaction, 'dependencies', []):
                if p:
                    self._confirm()
                    break
            else:
                self._install()

        self._client.install_packages(list(packages),
                                      reply_handler=reply,
                                      error_handler=self._error_handler)

    #
    #  Private
    #

    def _confirm(self):
        dia = AptConfirmDialog(self._transaction)
        response = dia.run()
        dia.destroy()
        if response == Gtk.ResponseType.OK:
            self._install()

    def _install(self):
        dialog = AptProgressDialog(self._transaction)
        dialog.run(close_on_finished=True,
                   show_error=True,
                   reply_handler=lambda: True,
                   error_handler=self._error_handler)

    def _error_handler(self, error):
        try:
            raise error
        except NotAuthorizedError:
            # Silently ignore auth failures
            sys.exit(11)
            return
        except TransactionFailed as error:
            pass
        except Exception as error:
            error = TransactionFailed(ERROR_UNKNOWN, str(error))

        dia = AptErrorDialog(error)
        dia.run()
        sys.exit(10)

    #
    #  Callbacks
    #

    def _on_transaction__finished(self, transaction, exitcode):
        sys.exit(0 if exitcode in [0, 'exit-success'] else 10)


if __name__ == '__main__':
    if not has_apt:
        sys.exit(1)

    pi = PackageInstaller()
    pi.install(*sys.argv[1:])
    Gtk.main()

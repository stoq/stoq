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

import gobject
import gtk

from kiwi.utils import gsignal

try:
    from aptdaemon.client import AptClient
    from aptdaemon.enums import ERROR_UNKNOWN
    from aptdaemon.errors import NotAuthorizedError, TransactionFailed
    from aptdaemon.gtkwidgets import AptErrorDialog, AptProgressDialog
    has_apt = True
except ImportError:
    has_apt = False


class AptPackageInstaller(gobject.GObject):
    gsignal('done', object)
    gsignal('auth-failed')

    def __init__(self, parent=None):
        gobject.GObject.__init__(self)
        self.client = AptClient()
        self.parent = parent

    def install(self, package):
        def reply(transaction):
            transaction.connect("finished", self._on_transaction__finished)
            self._transaction = transaction
            # dependencis not available on lucid
            for p in getattr(transaction, 'dependencies', []):
                if p:
                    self._confirm()
                    break
            else:
                self._install()
        self.client.install_packages([package],
                                     reply_handler=reply,
                                     error_handler=self._error_handler)

    def _on_transaction__finished(self, transaction, exitcode):
        print transaction, exitcode
        if exitcode not in [0, 'exit-success']:
            error = exitcode
        else:
            error = None
        self.emit('done', error)

    def _error_handler(self, error):
        try:
            raise error
        except NotAuthorizedError:
            # Silently ignore auth failures
            self.emit('auth-failed')
            return
        except TransactionFailed, error:
            pass
        except Exception, error:
            error = TransactionFailed(ERROR_UNKNOWN, str(error))
        dia = AptErrorDialog(error)
        dia.run()
        dia.destroy()

    def _confirm(self):
        from aptdaemon.gtkwidgets import AptConfirmDialog
        dia = AptConfirmDialog(self._transaction,
                               parent=self.parent)
        response = dia.run()
        dia.destroy()
        if response == gtk.RESPONSE_OK:
            self._install()

    def _install(self):
        def reply():
            return True
        dialog = AptProgressDialog(self._transaction,
                                   parent=self.parent)
        dialog.run(close_on_finished=True,
                   show_error=True,
                   reply_handler=reply,
                   error_handler=self._error_handler)

if __name__ == '__main__':
    api = AptPackageInstaller()
    api.install('postgresql')
    gtk.main()

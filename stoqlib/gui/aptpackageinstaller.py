#!/bin/bash
#
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

import gtk

from aptdaemon.client import AptClient
from aptdaemon.enums import ERROR_UNKNOWN
from aptdaemon.errors import NotAuthorizedError, TransactionFailed
from aptdaemon.gtkwidgets import (AptConfirmDialog, AptErrorDialog,
                                  AptProgressDialog)

class AptPackageInstaller(object):
    def __init__(self, parent=None):
        self.client = AptClient()
        self.parent = parent
    def install(self, package):
        def reply(transaction):
            transaction.connect("finished", self._on_transaction__finished)
            self._transaction = transaction
            for p in transaction.dependencies:
                if p:
                    self._confirm()
                    break
            else:
                self._install()
        self.client.install_packages([package],
                                     reply_handler=reply,
                                     error_handler=self._error_handler)

    def _on_transaction__finished(self, transaction, exitcode):
        print 'DONE', repr(exitcode)
        gtk.main_quit()

    def _error_handler(self, error):
        try:
            raise error
        except NotAuthorizedError:
            # Silently ignore auth failures
            return
        except TransactionFailed, error:
            pass
        except Exception, error:
            error = TransactionFailed(ERROR_UNKNOWN, str(error))
        dia = AptErrorDialog(error)
        dia.run()
        dia.destroy()

    def _confirm(self):
        dia = AptConfirmDialog(self._transaction,
                               parent=self.parent)
        respone = dia.run()
        dia.destroy()
        if respones == gtk.RESPONSE_OK:
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

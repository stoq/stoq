# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2016 Async Open Source
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

"""Stoq server utilities"""

import socket
import xmlrpclib

from twisted.web.xmlrpc import Proxy

from stoqlib.api import api
from stoqlib.database.settings import db_settings
from stoqlib.lib.configparser import get_config
from stoqlib.lib.translation import stoqlib_gettext as _


class ServerError(Exception):
    """Base error for :class:`.ServerProxy` connection issues"""

    def __init__(self, message, code=None):
        super(ServerError, self).__init__(message)
        self.fault_code = code

    def __str__(self):
        message = super(ServerError, self).__str__()
        if self.fault_code is not None:
            message = "%s: %s" % (self.fault_code, )

        return message


class ServerProxy(object):
    """Proxy to communicate with a Stoq Server instance"""

    def __init__(self):
        self._proxy = None

    #
    #  Public API
    #

    @api.async
    def call(self, method, *args):
        """Call a remote method on stoq server.

        :param method: the method to call
        :param args: extra args to pass to add to the call
        :return: the response
        :raises: :exc:`ServerError` in case of errors
        """
        try:
            proxy = yield self._get_proxy()
            retval = yield proxy.callRemote(method, *args)
        except xmlrpclib.Fault as e:
            raise ServerError(e.faultString, e.faultCode)
        except socket.error as e:
            raise ServerError(str(e))

        api.asyncReturn(retval)

    @api.async
    def check_running(self):
        """Call a remote method on stoq server.

        :param method: the method to call
        :param args: extra args to pass to add to the call
        :return: the response
        :raises: :exc:`ServerError` in case of errors
        """
        try:
            proxy = yield self._get_proxy()
        except Exception:
            api.asyncReturn(False)

        api.asyncReturn(bool(proxy))

    #
    #  Private
    #

    @api.async
    def _get_proxy(self):
        if self._proxy is None:
            config = get_config()

            address = config.get('General', 'serveraddress')
            if not address:
                with api.new_store() as store:
                    query = ("SELECT client_addr FROM pg_stat_activity "
                             "WHERE application_name LIKE ? AND "
                             "      datname = ? "
                             "LIMIT 1")
                    params = [u'stoqserver%', unicode(db_settings.dbname)]
                    res = store.execute(query, params=params).get_one()
                if res is not None and res[0] is not None:
                    address = res[0]
                elif res is not None:
                    # If the client_addr is NULL, then stoqserver is connected
                    # using the unix socket, which means that he is in the same
                    # ip as postgresql
                    address = db_settings.address
                    if not address:
                        # We are also on unix socket, so use localhost
                        address = 'localhost'
                else:
                    address = None

            if not address:
                raise ServerError(_("Stoq server not found"))

            port = config.get('General', 'serverport') or 6970
            url = 'http://%s:%s/XMLRPC' % (address, port)

            self._proxy = Proxy(url)

        try:
            yield self._check_proxy(self._proxy)
        except Exception:
            self._proxy = None
            raise

        api.asyncReturn(self._proxy)

    @api.async
    def _check_proxy(self, proxy):
        retval = yield proxy.callRemote('ping')
        if not retval:
            raise ServerError(_("Server not responding to pings"))


if __name__ == '__main__':
    from twisted.internet import reactor

    api.prepare_test()
    proxy = ServerProxy()

    @api.async
    def ping():
        try:
            retval = yield proxy.call('ping')
        except ServerError as e:
            print "error: %s" % (e, )
        else:
            print retval
        reactor.stop()

    reactor.callWhenRunning(ping)
    reactor.run()

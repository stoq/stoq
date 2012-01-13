# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Utils for communication with Magento"""

import datetime
import decimal

from dateutil.relativedelta import relativedelta
from kiwi.component import get_utility, provide_utility
from kiwi.datatypes import converter, ValidationError
from kiwi.log import Logger
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue
from twisted.web.xmlrpc import Proxy, Fault, Boolean

from stoqlib.lib.translation import stoqlib_gettext

from magentointerfaces import IMagentoProxyMapper

_ = stoqlib_gettext
log = Logger('plugins.magento.magentolib')


def get_proxy(config):
    """Return a singleton instance of L{MagentoProxy}.

    @attention: Always use this instead of instantializing L{MagentoProxy}
        directly, as it's designed to be a singleton.

    @returns: a L{MagentoProxy} instance
    """
    proxy_mapper = get_utility(IMagentoProxyMapper, None)
    if not proxy_mapper:
        proxy_mapper = dict()
        provide_utility(IMagentoProxyMapper, proxy_mapper)

    # Allow multiple servers, using a singleton for each one
    key = config.url
    proxy = proxy_mapper.get(key, None)
    if not proxy:
        proxy = proxy_mapper.setdefault(key, MagentoProxy(config.url,
                                                          config.api_user,
                                                          config.api_key,
                                                          config.tz_hours))
    return proxy


def validate_connection(url, api_user, api_key):
    """Validate a connection with Magento.

    This is useful to be used as a gui validator.

    @param url: the xmlrpc server to which we will try to connect
    @param api_user: the api user configured on Magento
    @param api_key: the C{api_user}'s key
    @returns: C{True} if all valid, C{False} otherwise
    """
    # Using synchronous code here because this is a validation.
    # We can't let interfaces exit without giving the properly result.
    from xmlrpclib import ServerProxy, Fault as Fault_ # pyflakes

    try:
        proxy = ServerProxy(str(url))
    except IOError:
        raise ValidationError(_("The url provided is not valid"))

    try:
        session = proxy.login(api_user, api_key)
    except Fault_ as err:
        if err.faultCode == MagentoProxy.ERROR_ACCESS_DENIED:
            raise ValidationError(_("Access denied for the given user"))
        else:
            raise ValidationError(str(err.faultString))

    return bool(session)


class MagentoProxy(object):
    """Proxy for magento api communication"""

    (ERROR_UNKNOWN,
     ERROR_INTERNAL,
     ERROR_ACCESS_DENIED,
     ERROR_API_PATH_INVALID,
     ERROR_API_PATH_NOT_CALLABLE,
     ERROR_SESSION_EXPIRED,
     ERROR_WRONG_PARAMETERS) = range(7)

    def __init__(self, url, api_user, api_key, tz_hours=0):
        self._api_user = api_user
        self._api_key = api_key
        self._lock = DeferredLock()
        self._rdelta = relativedelta(hours=float(tz_hours))
        self._session = ''

        self.proxy = Proxy(str(url))
        self.login()

    #
    #  Public API
    #

    @inlineCallbacks
    def call(self, method, args=None, lock=True):
        """Call C{method} with {args} on magento server.

        @param method: the method path as a L{basestring}
        @param args: a L{list} that will be used in call as the
            C{method} args
        @param lock: if this call should inhibit others
        @returns: the magento result
        """
        args = args or list()
        if lock:
            yield self.acquire()

        log.info("Calling method '%s' with args %s" % (method, args))
        try:
            retval = yield self.proxy.callRemote('call', self._session, method,
                                                 self._marshal_arg(args))
        except Fault as err:
            if err.faultCode == self.ERROR_SESSION_EXPIRED:
                # If session expired, login and try again
                retval = yield self.login(lock=False)
                if retval:
                    retval = yield self.call(method, args, lock=False)
                    returnValue(retval)
            else:
                raise
        else:
            returnValue(self._unmarshal_arg(retval))
        finally:
            # Make sure we released the lock
            lock and self.release()

    @inlineCallbacks
    def login(self, lock=True):
        """Open a session for communication with magento api.

        @param lock: if we should lock calls while logging in.
        @returns: C{True} on success, C{False} otherwise
        """
        if lock:
            yield self.acquire()

        log.info("Trying to login...")
        try:
            retval = yield self.proxy.callRemote('login', self._api_user,
                                                 self._api_key)
        except Fault as err:
            if err.faultCode == self.ERROR_ACCESS_DENIED:
                log.error("Access denied for user '%s'" % self._api_user)
                returnValue(False)
            else:
                raise
        else:
            log.info("Login successful!")
            self._session = retval
            returnValue(True)
        finally:
            # Make sure we released the lock
            lock and self.release()

    @inlineCallbacks
    def acquire(self):
        """Wraps C{defer.DeferredLock.acquire} method"""
        yield self._lock.acquire()

    def release(self):
        """Wraps C{defer.DeferredLock.release} method"""
        self._lock.release()

    #
    #  Private API
    #

    def _marshal_arg(self, arg):
        if arg is None:
            return ''
        elif isinstance(arg, decimal.Decimal):
            return str(arg)
        elif isinstance(arg, bool):
            return Boolean(arg)
        elif isinstance(arg, datetime.datetime):
            arg = arg.replace(microsecond=0)
            arg -= self._rdelta
            return arg.isoformat(' ')
        elif isinstance(arg, dict):
            args = dict()
            for k, v in arg.items():
                args[k] = self._marshal_arg(v)
            return args
        elif isinstance(arg, (list, tuple)):
            args = list()
            for v in arg:
                args.append(self._marshal_arg(v))
            return args

        return arg

    def _unmarshal_arg(self, arg):
        # FIXME: Unmarshal using a mapper. Don't try to discover the arg's
        #        type as this could lead to unknown errors.

        if isinstance(arg, dict):
            args = dict()
            for k, v in arg.items():
                args[k] = self._unmarshal_arg(v)

            return args
        elif isinstance(arg, (list, tuple)):
            args = list()
            for v in arg:
                args.append(self._unmarshal_arg(v))

            return args

        # The order here matter. int has to be tested before Decimal.
        # If not, all int will be converted to Decimal.
        for type_ in (int, decimal.Decimal):
            try:
                arg = converter.from_string(type_, arg)
            except (ValidationError, AttributeError):
                pass
            else:
                return arg

        try:
            # Magento date comes in isoformat. Convert it to datetime.
            arg = datetime.datetime.strptime(arg, '%Y-%m-%d %H:%M:%S')
        except (TypeError, ValueError):
            pass
        else:
            return arg

        return arg

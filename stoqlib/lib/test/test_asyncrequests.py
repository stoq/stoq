# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2016 Async Open Source <http://www.async.com.br>
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
##

import mock

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib import asyncrequests


class _TestException(Exception):
    pass


class TestAsyncRequest(DomainTest):

    @mock.patch('stoqlib.lib.asyncrequests.requests.request')
    def test_run_ok(self, request):
        retval = object
        request.return_value = retval
        callback = mock.Mock()
        errback = mock.Mock()

        ar = asyncrequests.AsyncRequest('foo', 'bar',
                                        callback=callback, errback=errback)
        ar.start()
        ar.join()

        self.assertIs(ar.retval, retval)
        self.assertIsNone(ar.error)
        self.assertCalledOnceWith(callback, retval)
        self.assertNotCalled(errback)

    @mock.patch('stoqlib.lib.asyncrequests.requests.request')
    def test_run_error(self, request):
        retval = object
        error = _TestException()
        request.return_value = retval
        request.side_effect = error
        callback = mock.Mock()
        errback = mock.Mock()

        ar = asyncrequests.AsyncRequest('foo', 'bar',
                                        callback=callback, errback=errback)
        ar.start()
        ar.join()

        self.assertIsNone(ar.retval)
        self.assertIs(ar.error, error)
        self.assertCalledOnceWith(errback, error)
        self.assertNotCalled(callback)

    @mock.patch('stoqlib.lib.asyncrequests.requests.request')
    def test_get_response_ok(self, request):
        retval = object
        request.return_value = retval
        callback = mock.Mock()
        errback = mock.Mock()

        ar = asyncrequests.AsyncRequest('foo', 'bar',
                                        callback=callback, errback=errback)
        ar.start()
        self.assertIs(ar.get_response(), retval)

        self.assertIs(ar.retval, retval)
        self.assertIsNone(ar.error)
        self.assertCalledOnceWith(callback, retval)
        self.assertNotCalled(errback)

    @mock.patch('stoqlib.lib.asyncrequests.requests.request')
    def test_get_response_error(self, request):
        retval = object
        error = _TestException()
        request.return_value = retval
        request.side_effect = error
        callback = mock.Mock()
        errback = mock.Mock()

        ar = asyncrequests.AsyncRequest('foo', 'bar',
                                        callback=callback, errback=errback)
        ar.start()
        with self.assertRaises(_TestException):
            ar.get_response()

        self.assertIsNone(ar.retval)
        self.assertIs(ar.error, error)
        self.assertCalledOnceWith(errback, error)
        self.assertNotCalled(callback)


class TestRequestsApi(DomainTest):

    @mock.patch('stoqlib.lib.asyncrequests.request')
    def test_get(self, request):
        asyncrequests.get('foobar', baz=1)
        self.assertCalledOnceWith(request, 'get', 'foobar', baz=1)

    @mock.patch('stoqlib.lib.asyncrequests.request')
    def test_post(self, request):
        asyncrequests.post('foobar', baz=1)
        self.assertCalledOnceWith(request, 'post', 'foobar', baz=1)

    @mock.patch('stoqlib.lib.asyncrequests.AsyncRequest')
    def test_request(self, AsyncRequest):
        r = mock.Mock()
        AsyncRequest.return_value = r

        callback = object()
        errback = object()
        asyncrequests.request('method', 'foobar',
                              callback=callback, errback=errback, baz=1)
        self.assertCalledOnceWith(AsyncRequest, 'method', 'foobar',
                                  callback=callback, errback=errback, baz=1)
        self.assertCalledOnceWith(r.start)

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

"""Asynchronous requests utilities.

This module tries to mimic the `requests` api, providing functions with
the same signature as it. The only difference is that the requests
here are executed asynchronously on a separated thread.
"""

import requests
import threading


class AsyncRequest(threading.Thread):
    """Async request implementation.

    Responsible for doing the request asynchronously, and optionally
    call a callback/errback on success/failure.
    """

    #: The default request timeout if none is defined
    DEFAULT_TIMEOUT = 5

    def __init__(self, method, url, callback=None, errback=None, **kwargs):
        super(AsyncRequest, self).__init__()

        self.daemon = True
        self._method = method
        self._url = url
        self._callback = callback
        self._errback = errback
        self._kwargs = kwargs
        self.retval = None
        self.error = None

    #
    #  threading.Thread
    #

    def run(self):
        """Do the real request.

        This will be called by the thread api. Do not call this
        directly, use :meth:`.start` instead.
        """
        kwargs = self._kwargs.copy()
        kwargs.setdefault('timeout', self.DEFAULT_TIMEOUT)

        try:
            self.retval = requests.request(self._method, self._url, **kwargs)
        except Exception as e:
            self.error = e
            if self._errback is not None:
                self._errback(e)
        else:
            if self._callback is not None:
                self._callback(self.retval)

    #
    #  Public API
    #

    def get_response(self):
        """Get the response from the object.

        Joins the thread and returns its retval. Note that,
        if the thread raised an error, it will be reraise here.

        :return: the `requests.Response` object or `None` if
            the an error happened
        """
        self.join()
        if self.error:
            raise self.error
        return self.retval


def request(method, url, callback=None, errback=None, **kwargs):
    """Do a request asynchronously.

    :param method: The http method to use on the request
    :param url: The url to do the request
    :parm callback: An optional callback to be called after
        the request has been sucessfully executed. The request's
        retval will be passed as an argument to it
    :param errback: An optional callback to be called if
        the request produces any error. The traceback object will
        be passed as an argument to it
    :return: The :class:`.AsyncRequest` that is running the request.
        One can :meth:`threading.Thread.join` it when wanting to
        wait for it to finish
    """
    request = AsyncRequest(method, url,
                           callback=callback, errback=errback, **kwargs)
    request.start()
    return request


def get(url, **kwargs):
    """Do a GET request asynchronously.

    :param url: The url to do the request
    :param kwargs: Extra keywords that will be passed to :func:`.request`
    :return: The :class:`.AsyncRequest` that is running the request.
        One can :meth:`threading.Thread.join` it when wanting to
        wait for it to finish
    """
    return request('get', url, **kwargs)


def post(url, **kwargs):
    """Do a POST request asynchronously.

    :param url: The url to do the request
    :param kwargs: Extra keywords that will be passed to :func:`.request`
    :return: The :class:`.AsyncRequest` that is running the request.
        One can :meth:`threading.Thread.join` it when wanting to
        wait for it to finish
    """
    return request('post', url, **kwargs)

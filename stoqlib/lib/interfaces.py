# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006,2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin   <jdahlin@async.com.br>
##

""" Stoqlib Interfaces """

from zope.interface.interface import Interface, Attribute


class CookieError(Exception):
    pass

class ICookieFile(Interface):
    def get():
        """Fetch the cookie or raise CookieError if a problem occurred

        @returns: (username, password)
        @rtype: tuple
        """

    def store(username, password):
        """Stores a username and password

        @param username: username
        @param password: password
        """

    def clear():
        """Resets the cookie
        """

class IApplicationDescriptions(Interface):
    """Get a list of application names, useful for launcher programs
    """

    def get_application_names():
        """
        Gets a list of application names.
        @returns: a list of application names.
        """

    def get_descriptions():
        """
        Gets a list of tuples with some important Stoq application
        informations. Each tuple jas the following data:
        * Application name
        * Application full name
        * Application icon name
        * Application description
        @returns: a list of tuples with Stoq application informations.
        """

class IXMLRPCService(Interface):
    def __init__(hostname, port):
        """
        Create a new IXMLRPCService object.
        @param port: port to listen to
        @param hostname: hostname to bind to or an empty string
                         to bind to all addresses
        """

    def serve():
        """Starts the XMLRPC service so it's ready
        to accept clients.
        This call will block until stop() is called
        """

    def stop():
        """Stops the service, eg break out of serve
        """

class ISystemNotifier(Interface):

    def info(short, description):
        pass

    # FIXME: Remove *args/**kwargs
    def warning(short, description, *args, **kwargs):
        pass

    def error(short, description):
        pass

    def yesno(text, default, *verbs):
        pass

class IPluginManager(Interface):
    """
    """


class IPlugin(Interface):
    def install():
        pass

    def activate(context):
        pass



class IPaymentOperation(Interface):
    """An object implementing IPaymentOperation is a 1:1
    mapping to a payment method. It's responsible for the
    logic specific parts of a method.
    """
    name = Attribute('name')
    description = Attribute('description')
    max_installments = Attribute('max_installments')

    def payment_create(payment):
        """This is called when a payment is created
        @param payment: the created payment
        """

    def payment_delete(payment):
        """This is called just before a payment is deleted
        @param payment: the payment which is going to be deleted
        """

    def selectable(method):
        """This is called to find out if the method should
        be shown in the slave list of payment methods
        @returns: True if it should be shown, otherwise
        """


class IPaymentOperationManager(Interface):
    """This is a singleton for storing payment
    operations. You can register one and fetch by name
    """
    def get_operation_names():
        """Get the operation names registered in this manager
        @returns: payment names
        @rtype: list of strings
        """

    def register(name, operation):
        """Register a payment operation.
        @param name: name of the payment operation
        @param operation: the payment operation
        @type operation: an object implementing L{IPaymentOperation}
        """
    def get(name):
        """Get an operation given a name
        @param name: name of the operation
        @returns: the operation
        @rtype operation: an object implementing L{IPaymentOperation}
        """
    

# -*- Mode: Python; coding: utf-8 -*-
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

""" Stoqlib Interfaces """

# pylint: disable=E0102,E0211,E0213

from zope.interface.interface import Interface, Attribute


class CookieError(Exception):
    pass


class ICookieFile(Interface):
    def get():
        """Fetch the cookie or raise CookieError if a problem occurred

        :returns: (username, password)
        :rtype: tuple
        """

    def store(username, password):
        """Stores a username and password

        :param username: username
        :param password: password
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
        :returns: a list of application names.
        """

    def get_descriptions():
        """
        Gets a list of tuples with some important Stoq application
        informations. Each tuple jas the following data:
        * Application name
        * Application full name
        * Application icon name
        * Application description
        :returns: a list of tuples with Stoq application informations.
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
    """A manager for plugins.
    """


class IPlugin(Interface):

    name = Attribute('name')

    def activate():
        """Called everytime the plugins gets activated

        This is where the init plugin logic should be, like events
        connection and so on.
        """
        pass

    def get_migration():
        """Get the database migration for the plugin

        :returns: a :class:`stoqlib.database.migration.PluginSchemaMigration`
        """
        pass

    def get_tables():
        """Returns a C{list} of domain classes

        This should return a C{list} of tuples, each one containing the
        domain path as the first item, and a list of classes as
        the second. e.g. A 'from a.b import C, D' should be
        translated into the C{tuple} ('a.b', ['C', 'D']).
        @note: this information is used for database synchronization

        :returns: a C{list} of C{tuple} containing domain info
        """
        pass

    def get_server_tasks():
        """Get a list of tasks that the server will be responsible to run

        A task is a object implementing :class:`.IPluginTask`.

        :returns: a list of tasks
        """
        pass

    def get_dbadmin_commands():
        """Returns a list of available commands for dbadmin

        :returns: a C{list} of available commands
        """
        pass

    def handle_dbadmin_command(command, options, args):
        """Handle a dbadmin command

        :param command: the command string
        :param options: extra optparser options
        :param args: a list of C{args}
        """
        pass


class IPluginTask(Interface):
    """A plugin task that can run on stoq server"""

    name = Attribute('name')
    handle_actions = Attribute('handle_actions')

    def start(**kwargs):
        """Called to start the task.

        :keyword pipe_connection: the connection used to communicate
            with the stoqserver api. Will only be present if
            :attr:`.handle_actions` is ``True``
        """


class IPaymentOperation(Interface):
    """An object implementing IPaymentOperation is a 1:1
    mapping to a payment method. It's responsible for the
    logic specific parts of a method.
    """
    name = Attribute('name')
    description = Attribute('description')
    max_installments = Attribute('max_installments')

    def pay_on_sale_confirm():
        """If we should set the payment as paid when confirming a sale"""

    def payment_create(payment):
        """This is called when a payment is created

        :param payment: the created payment
        """

    def payment_delete(payment):
        """This is called just before a payment is deleted

        :param payment: the payment which is going to be deleted
        """

    def create_transaction():
        """If this payment method should create a transaction when
          paid

        :returns: True if an AccountTransaction should be created
        """

    def selectable(method):
        """This is called to find out if the method should
        be shown in the slave list of payment methods

        :returns: True if it should be shown
        """

    def creatable(method, payment_type, separate):
        """If it's possible to create new payments of this payment method type

        :param method: payment method
        :param payment_type: kind of payment
        :param separate: if it's created separately from a sale/purchase
        :returns: True if you can create new methods of this type
        """

    def can_cancel(payment):
        """If it's possible to cancel a payment

        :param payment: the payment to cancel
        """

    def can_change_due_date(payment):
        """If it's possible to change the due date of a payment

        :param payment: the payment to change due date
        """

    def can_pay(payment):
        """If it's possible to pay a payable

        :param payment: the payment to pay
        """

    def can_print(payment):
        """If it's possible to print this payment

        :param payment: the payment to print
        """

    def can_set_not_paid(payment):
        """If it can be set as not paid once it has been paid

        :param payment: the payment to be set as not paid
        """

    def print_(payment):
        """Prints this payment

        :param payment: the payment to print
        """

    def get_constant(payment):
        """This should return a stoqdriver payment method constant

        :param payment: the payment whose method we shout return a stoqdrivers
                        constant
        :returns: one :class:`PaymentMethodConstant`
        """

    def require_person(payment_type):
        """If this payment requires a person to be created

        :param payment_type: the kind of payment
        """


class IPaymentOperationManager(Interface):
    """This is a singleton for storing payment
    operations. You can register one and fetch by name
    """
    def get_operation_names():
        """Get the operation names registered in this manager

        :returns: payment names
        :rtype: list of strings
        """

    def register(name, operation):
        """Register a payment operation.

        :param name: name of the payment operation
        :param operation: the payment operation
        :type operation: an object implementing :class:`IPaymentOperation`
        """
    def get(name):
        """Get an operation given a name

        :param name: name of the operation
        :returns: the operation
        :rtype operation: an object implementing :class:`IPaymentOperation`
        """


class IStoqConfig(Interface):
    pass


class IAppInfo(Interface):
    """Store global application data, such as
    name, version.
    """

    def set(name, value):
        """Sets a variable to value

        :param name: string, variable name
        :param value: value of the key
        """

    def get(name):
        """Gets a variable

        :param name: name of the variable to fetch
        :returns: the key for @name
        """


class IPermissionManager(Interface):
    """A permission manager controling what parts of the system are acessible.

    To completely disable access to a feature, set permission=0.
    """

    def set(key, permission):
        """Set the credentials the current user have to access a feature.

        If the feature should be completely disabled (user cannot access the
        feature), permission should be 0.

        If the key is a domain object, available credentials are: PERM_SEARCH,
        PERM_CREATE, PERM_EDIT, PERM_DETAILS. This credentials are used by
        SearchEditors and will disable/enable create, edit and details button.

        If the key is a menu action, the only credential is PERM_ACCESS. If the
        user has it, he will be allowed to access the feature, oherwise it will
        be hidden.

        :param key: String identifing the feature. This should be the name of
                    the domain object (Product, Client, etc..), or an
                    identifier for the related menu action (app.admin.new_order,
                    for instance).
        :param permission: The credentials the current user has for accessing
                    the feature.
        """

    def get(key):
        """Returns the current user credentials for the feature

        the value returned should be checked agains PERM_* flags.
        """

    def can_search(key):
        """Returns if the user has permission to search the given feature"""

    def can_edit(key):
        """Returns if the user has permission to edit the given feature"""

    def can_create(key):
        """Returns if the user has permission to create new objects of the given
        feature"""

    def can_see_details(key):
        """Returns if the user has permission to see details of objects of the
        given feature"""

# pylint: enable=E0102,E0211,E0213

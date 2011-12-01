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

import datetime

from kiwi.log import Logger
from twisted.internet.defer import inlineCallbacks, returnValue, maybeDeferred
from twisted.web.xmlrpc import Fault

from stoqlib.database.orm import BoolCol, IntCol, ForeignKey, AND
from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.base import Domain

from magentolib import get_proxy

log = Logger('plugins.magento.domain.magentobase')


class MagentoBase(Domain):
    """Base class for all Magento domain classes

    @cvar API_NAME: the api name for method calls
    @cvar API_ID_NAME: the key name that represents the id of the
        record on magento api.

    @ivar keep_need_sync: if set to C{True} on obj, even C{process}
        returning True, it'll keep c{need_sync} as C{True}. That way,
        on next C{MagentoBase.synchronize} call, that obj will be
        processed again.
    @ivar magento_id: the record ID on Magento
    @ivar need_sync: if we need to sync this object
    @ivar config: the L{magentoconfig.MagentoConfig} associated with
        this object.
    """

    API_NAME = None
    API_ID_NAME = None

    keep_need_sync = False
    magento_id = IntCol(default=None)
    need_sync = BoolCol(default=True)
    config = ForeignKey('MagentoConfig')

    #
    #  Properties
    #

    @property
    def proxy(self):
        return get_proxy(self.config)

    #
    #  Classmethods
    #

    @classmethod
    @inlineCallbacks
    def synchronize(cls, config):
        """Sync clients between Stoq and Magento.

        We will iterate over all records marked wit C{need_sync} and
        call it's C{process} method.
        @note: Only objs associated to C{config} will be synchronized,
            that means, the objs will be synchronized to the server
            pointed by C{config}.

        @param config: the L{magentoconfig.MagentoConfig} that will
            be used to synchronize objs
        @returns: C{True} if all sync went well, C{False} otherwise
        """
        retval_list = list()
        trans = new_transaction()

        table_config = config.get_table_config(cls)
        if table_config.need_ensure_config:
            retval = yield cls.ensure_config(trans.get(config))
            if not retval:
                returnValue(False)

            table_config.need_ensure_config = not retval
            finish_transaction(trans, retval)

        for obj in cls.select(connection=trans,
                              clause=AND(cls.q.configID == config.id,
                                         cls.q.need_sync == True)):
            retval = yield maybeDeferred(obj.process)
            retval_list.append(retval)

            if not obj.keep_need_sync:
                obj.need_sync = not retval
            # Objs are responsible for setting this on every process
            # if they need to.
            obj.keep_need_sync = False

            finish_transaction(trans, retval)

        trans.close()
        returnValue(not retval_list or all(retval_list))

    @classmethod
    @inlineCallbacks
    def list_remote(cls, config, *args, **kwargs):
        """Request a list of records on Magento

        @param config: the L{magentoconfig.MagentoConfig} that will
            be used to retrieve the record list
        @param args: additional args that will be used on info
            request
        @param kwargs: additional filters that will be used on
            info request
        @returns: a L{list} of records
        """
        proxy = get_proxy(config)
        method = "%s.list" % cls.API_NAME
        args = list(args)
        args.append(kwargs)

        try:
            retval = yield proxy.call(method, args)
        except Fault as err:
            log.warning("An error occurred when requesting API '%s' "
                        "for a list of records: %s" % (cls.API_NAME,
                                                       err.faultString))
            returnValue(False)

        returnValue(retval)

    @classmethod
    @inlineCallbacks
    def info_remote(cls, config, id_, *args):
        """Request info about the record represented by C{id_} on Magento

        @param config: the L{magentoconfig.MagentoConfig} that will
            be used to retrieve the record information
        @param id_: the register identification on Magento
        @param args: additional args that will be used on info request
        @returns: a L{dict} containing info
        """
        proxy = get_proxy(config)
        method = "%s.info" % cls.API_NAME
        args = list(args)
        # The id needs to be the first item
        args.insert(0, id_)

        try:
            retval = yield proxy.call(method, args)
        except Fault as err:
            log.warning("An error occurred when requesting API '%s' "
                        "for info about ID '%s' on Magento: %s"
                        % (cls.API_NAME, id_, err.faultString))
            returnValue(False)

        returnValue(retval)

    @classmethod
    def ensure_config(cls, config):
        """A helper to get specific configs for C{cls} before sync

        This can be implemented on subclasses to allow more advanced
        logic on C{synchronize}.

        @param config: the L{MagentoConfig} we are working on
        @returns: C{True} if ensure went well, C{False} otherwise
        """
        return True

    #
    #  Public API
    #

    def process(self, **kwargs):
        """Called when C{self} needs sync on synchronization process

        This must be implemented on subclasses to take actions on how
        to properly synchronize C{self}.
        @note: Use C{super} on subclasses to avoid breaking diamond
            inheritances (like in L{MagentoBaseSyncBoth})

        @returns: C{True} if all process went well, C{False} otherwise
        """
        # Returning instead of raising to allow super logic.
        return NotImplementedError

    #
    #  Domain hooks
    #

    def _init(self, *args, **kwargs):
        if not self.__class__.API_NAME:
            raise ValueError("The class %s must implement API_NAME "
                             "attribute." % self.__class__.__name__)
        if not self.__class__.API_ID_NAME:
            raise ValueError("The class %s must implement API_ID_NAME "
                             "attribute." % self.__class__.__name__)

        super(MagentoBase, self)._init(*args, **kwargs)


class MagentoBaseSyncUp(MagentoBase):
    """A L{MagentoBase} that syncs from Stoq => Magento"""

    #
    #  Public API
    #

    def need_create_remote(self):
        """Called to see if we need to create C{self} on Magento

        This can be implemented on subclasses to properly decide
        if C{self} needs to be created or not

        @returns: C{True} needs to be created, C{False} otherwise
        """
        return not self.magento_id

    def create_remote(self):
        """Called when C{self} needs to be created on Magento

        This must be implemented on subclasses to take actions
        to properly create C{self} on Magento

        @returns: C{True} if create went well, C{False} otherwise
        """
        raise NotImplementedError

    def update_remote(self):
        """Called when C{self} needs to be updated on Magento

        This must be implemented on subclasses to take actions
        to properly update the record on Magento

        @returns: C{True} if update went well, C{False} otherwise
        """
        raise NotImplementedError

    #
    #  MagentoBase hooks
    #

    @inlineCallbacks
    def process(self, **kwargs):
        """
        @see: L{MagentoBase.process}
        """
        # Allow more advanced logic on MagentoBaseSyncBoth
        sync_up = kwargs.get('sync_up', True)

        if not sync_up:
            retval = True
        else:
            if self.need_create_remote():
                retval = yield maybeDeferred(self.create_remote)
            else:
                retval = yield maybeDeferred(self.update_remote)

        # Avoid doing more process if we failed here.
        if retval:
            retval = yield maybeDeferred(super(MagentoBaseSyncUp,
                                               self).process,
                                         **kwargs)
        returnValue(retval)


class MagentoBaseSyncDown(MagentoBase):
    """A L{MagentoBase} that syncs from Magento => Stoq"""

    #
    #  Public API
    #

    def need_create_local(self):
        """Called to see if we need to create the Magento record on C{self}

        This must be implemented on subclasses to properly decide
        if C{self} needs to be created or not

        @returns: C{True} needs to be created, C{False} otherwise
        """
        raise NotImplementedError

    def create_local(self, info):
        """Called when we need to create the Magento record on C{self}

        This must be implemented on subclasses to take actions
        to properly create the Magento record on C{self}

        @param info: a L{dict} containing the info returned by Magento
        @returns: C{True} if cnot reate went well, C{False} otherwise
        """
        raise NotImplementedError

    def update_local(self, info):
        """Called when we need to update the Magento record on C{self}

        This must be implemented on subclasses to take actions
        to properly update the Magento record on C{self}

        @param info: a L{dict} containing the info returned by Magento
        @returns: C{True} if update went well, C{False} otherwise
        """
        raise NotImplementedError

    #
    #  MagentoBase hooks
    #

    @classmethod
    @inlineCallbacks
    def synchronize(cls, config):
        """Extends L{MagentoBase.sync} functionality

        Before doing the real sync, we request for a list of records
        on Magento and mark their C{need_sync} attribute as C{True}.

        @returns: C{True} if all sync went well, C{False} otherwise
        """
        trans = new_transaction()
        table_config = trans.get(config.get_table_config(cls))

        last_sync_date = table_config.last_sync_date
        filters = {
            # Only retrieve records modified after last_sync_date
            'updated_at': {'gteq': last_sync_date},
            }
        mag_records = yield cls.list_remote(config, **filters)

        if mag_records:
            for mag_record in mag_records:
                magento_id = mag_record[cls.API_ID_NAME]
                obj = cls.selectOneBy(connection=trans,
                                      config=config,
                                      magento_id=magento_id)
                if not obj:
                    obj = cls(connection=trans,
                              config=config,
                              magento_id=magento_id)

                obj.need_sync = True
                last_sync_date = max(last_sync_date,
                                     # Some records dont have 'updated_at'
                                     # visible on list. Their last_sync should
                                     # be updated manually on their class.
                                     mag_record.get('updated_at',
                                                    datetime.datetime.min))

            table_config.last_sync_date = last_sync_date
            finish_transaction(trans, True)

        trans.close()
        retval = yield super(MagentoBaseSyncDown, cls).synchronize(config)
        returnValue(retval)

    @inlineCallbacks
    def process(self, **kwargs):
        """
        @see: L{MagentoBase.process}
        """
        # Allow more advanced logic on MagentoBaseSyncBoth
        sync_down = kwargs.get('sync_down', True)

        if not sync_down:
            retval = True
        else:
            info = yield self.__class__.info_remote(self.config,
                                                    self.magento_id)
            if not info:
                returnValue(False)

            if self.need_create_local():
                retval = yield maybeDeferred(self.create_local, info)
            else:
                retval = yield maybeDeferred(self.update_local, info)

        # Avoid doing more process if we failed here.
        if retval:
            retval = yield maybeDeferred(super(MagentoBaseSyncDown,
                                               self).process,
                                         **kwargs)
        returnValue(retval)


class MagentoBaseSyncBoth(MagentoBaseSyncDown, MagentoBaseSyncUp):
    """A combination of L{MagentoBaseSyncDown} and L{MagentoBaseSyncUp}

    This implementation can synchronize Magento objects both ways (up
    and down) or represent something that can do that, but will choose
    which one to do.
    @note: The C{process} mro will first call L{MagentoBaseSyncDown.process}
        and then, L{MagentoBaseSyncUp.process}. Be prepared to workaround
        that if you need something else. C{self.keep_need_sync} can help
        a lot on that.
    """

    #
    #  MagentoBase hooks
    #

    @inlineCallbacks
    def process(self, **kwargs):
        """
        @see: L{MagentoBaseSyncDown.process} and L{MagentoBaseSyncUp.process}
        """
        retval = yield maybeDeferred(super(MagentoBaseSyncBoth, self).process,
                                     **kwargs)
        returnValue(retval)

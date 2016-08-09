# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2016 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import os
import threading

import dateutil.parser
import glib
import gobject
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.lib.threadutils import threadit, schedule_in_main_thread
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.webservice import WebService
from stoqlib.net.server import ServerProxy


class ResourceStatus(gobject.GObject):
    """The status of a given resource"""

    gsignal('status-changed', int, str)

    (STATUS_OK,
     STATUS_WARNING,
     STATUS_ERROR) = range(3)

    status_label = {
        STATUS_OK: _("OK"),
        STATUS_WARNING: _("WARNING"),
        STATUS_ERROR: _("ERROR"),
    }

    name = None
    label = None
    priority = 0

    def __init__(self):
        super(ResourceStatus, self).__init__()

        assert self.name is not None
        self.status = self.STATUS_OK
        self.reason = None
        self.reason_long = None

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

    @property
    def status_str(self):
        return self.status_label[self.status]

    def refresh(self):
        """Refresh the resource status

        Subclasses should override this and update
        :obj:`.status` and :obj:`.reason`

        Note that this will not be running on the main thread,
        so be cautelous with non thread-safe operations.
        """
        raise NotImplementedError

    def refresh_and_notify(self):
        """Refresh the resource status and notify for changes"""
        old_status, old_reason = self.status, self.reason
        self.refresh()

        if (self.status, self.reason) != (old_status, old_reason):
            # This is running on another so schedule the emit in the main one
            schedule_in_main_thread(
                self.emit, 'status-changed', self.status, self.reason)


class ResourceStatusManager(gobject.GObject):

    gsignal('status-changed', int)

    REFRESH_TIMEOUT = int(os.environ.get('STOQ_STATUS_REFRESH_TIMEOUT', 60))
    _instance = None

    def __init__(self):
        super(ResourceStatusManager, self).__init__()

        self._lock = threading.Lock()
        self.resources = {}
        glib.timeout_add_seconds(self.REFRESH_TIMEOUT,
                                 self.refresh_and_notify)

    #
    #  Public API
    #

    @classmethod
    def get_instance(cls):
        """Get the manager singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def status(self):
        """The general status of the resources"""
        if any(resource.status == ResourceStatus.STATUS_ERROR
               for resource in self.resources.itervalues()):
            return ResourceStatus.STATUS_ERROR
        elif any(resource.status == ResourceStatus.STATUS_WARNING
                 for resource in self.resources.itervalues()):
            return ResourceStatus.STATUS_WARNING
        else:
            return ResourceStatus.STATUS_OK

    @property
    def statuses(self):
        """A list of resources' (status, reason)"""
        return [(r.status, r.reason) for r in self.resources.itervalues]

    def add_resource(self, resource):
        """Add a :class:`.ResourceStatus` on the manager"""
        assert resource.name not in self.resources
        assert isinstance(resource, ResourceStatus)
        self.resources[resource.name] = resource

    def refresh_and_notify(self, force=False):
        """Refresh the status and notify for changes"""
        # Do not run checks if we are running tests. It breaks the whole suite
        if os.environ.get('STOQ_TESTSUIT_RUNNING', '0') == '1':
            return False
        return threadit(self._refresh_and_notify, force=force)

    #
    #  Private
    #

    def _refresh_and_notify(self, force=False):
        with self._lock:
            old_status = self.status
            for resource in self.resources.itervalues():
                resource.refresh_and_notify()

            status = self.status
            if status != old_status or force:
                # This is running on another so schedule the emit in the main one
                schedule_in_main_thread(
                    self.emit, 'status-changed', status)


def register(resource_class):
    manager = ResourceStatusManager.get_instance()
    manager.add_resource(resource_class())
    return resource_class


@register
class _ServerStatus(ResourceStatus):

    name = "stoqserver"
    label = _("Stoq server")
    priority = 99

    def __init__(self):
        ResourceStatus.__init__(self)
        self._proxy = ServerProxy()

    def refresh(self):
        if not api.sysparam.get_bool('ONLINE_SERVICES'):
            self.status = ResourceStatus.STATUS_WARNING
            self.reason = _('Stoq server not running because the parameter '
                            '"Online Services" is disabled')
            self.reason_long = _('Enable the parameter "Online Services" '
                                 'on the "Admin" app to solve this issue')
            return

        if self._proxy.check_running():
            self.status = self.STATUS_OK
            self.reason = _("Stoq server is alive and running")
            self.reason_long = None
        else:
            self.status = ResourceStatus.STATUS_ERROR
            self.reason = _("Stoq server not found")
            self.reason_long = _("Install and configure the stoq-server "
                                 "package to solve this issue.")


@register
class _BackupStatus(ResourceStatus):

    name = "backup"
    label = _("Backup")
    priority = 98

    def __init__(self):
        ResourceStatus.__init__(self)
        self._webservice = WebService()

    def refresh(self):
        if not api.sysparam.get_bool('ONLINE_SERVICES'):
            self.status = ResourceStatus.STATUS_WARNING
            self.reason = _('Backups not running because the parameter '
                            '"Online Services" is disabled')
            self.reason_long = _('Enable the parameter "Online Services" '
                                 'on the "Admin" app to solve this issue')
            return

        request = self._webservice.status()
        try:
            response = request.get_response()
        except Exception as e:
            self.status = self.STATUS_WARNING
            self.reason = _("Could not communicate with Stoq.link")
            self.reason_long = str(e)
            return

        if response.status_code != 200:
            self.status = self.STATUS_WARNING
            self.reason = _("Could not communicate with Stoq.link")
            self.reason_long = None
            return

        data = response.json()
        if data['latest_backup_date']:
            backup_date = dateutil.parser.parse(data['latest_backup_date'])
            delta = datetime.datetime.today() - backup_date

            if delta.days > 3:
                self.status = self.STATUS_WARNING
                self.reason = _("Backup is late. Last backup date is %s") % (
                    backup_date.strftime('%x'))
                self.reason_long = _("Check your Stoq Server logs to see if "
                                     "there's any problem with it")
            else:
                self.status = self.STATUS_OK
                self.reason = _("Backup is up-to-date. Last backup date is %s") % (
                    backup_date.strftime('%x'))
                self.reason_long = None
        else:
            self.status = self.STATUS_WARNING
            self.reason = _("There's no backup data yet")
            self.reason_long = None

# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##

import gtk
from kiwi.log import Logger
from stoqdrivers.exceptions import CouponOpenError, DriverError
from stoqlib.database.runtime import get_current_station, get_connection
from stoqlib.domain.events import (SaleConfirmEvent, TillAddCashEvent,
                                   TillRemoveCashEvent, TillOpenEvent,
                                   TillCloseEvent)
from stoqlib.domain.till import Till
from stoqlib.exceptions import TillError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.events import StartApplicationEvent, CouponCreatedEvent
from stoqlib.lib.message import info, warning, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

from couponprinter import CouponPrinter
from ecfdomain import ECFPrinter
from ecfprinterdialog import ECFListDialog
from ecfprinterstatus import ECFAsyncPrinterStatus
from ecfmemorydialog import FiscalMemoryDialog

_ = stoqlib_gettext
log = Logger("stoq-ecf-plugin")


class ECFUI(object):
    def __init__(self):
        self.conn = get_connection()
        self._printer_verified = False
        self._printer = self._create_printer()

        SaleConfirmEvent.connect(self._on_SaleConfirm)
        TillOpenEvent.connect(self._on_TillOpen)
        TillCloseEvent.connect(self._on_TillClose)
        TillAddCashEvent.connect(self._on_TillAddCash)
        TillRemoveCashEvent.connect(self._on_TillRemoveCash)
        StartApplicationEvent.connect(self._on_StartApplicationEvent)
        CouponCreatedEvent.connect(self._on_CouponCreatedEvent)

        self._till_summarize_action = gtk.Action(
            'Summary', _('Summary'), None, None)
        self._till_summarize_action.connect(
            'activate', self._on_TillSummary__activate)

    #
    # Private
    #

    def _create_printer(self):
        station = get_current_station(self.conn)
        printer = ECFPrinter.selectOneBy(station=station, is_active=True,
                                         connection=self.conn)
        if printer:
            return CouponPrinter(printer)

    def _validate_printer(self):
        if self._printer is None:
            warning(_("This operation requires a connected fiscal printer"))
            return False

        if self._printer_verified:
            return True

        domain = self._printer.get_printer()
        driver = self._printer.get_driver()
        self._status = ECFAsyncPrinterStatus(domain.device_name, printer=driver)

        if not self._printer.check_serial():
            warning(_("Fiscalprinters serial number is different!"))
            return False

        self._printer_verified = True

        return True

    def _add_ui_menus(self, appname, uimanager):
        if appname == 'pos':
            self._add_pos_menus(uimanager)
        elif appname == 'till':
            self._add_till_menus(uimanager)
        elif appname == 'admin':
            self._add_admin_menus(uimanager)
        self._update_ui_actions()

    def _add_admin_menus(self, uimanager):
        ui_string = """<ui>
          <menubar name="menubar">
            <menu action="settings_menu" name="settings_menu">
            <placeholder name="PluginSettings">
              <menuitem action="ConfigurePrinter"/>
            </placeholder>
            </menu>
          </menubar>
        </ui>"""

        ag = gtk.ActionGroup('ECFMenuActions')
        ag.add_actions([
            ('ECFMenu', None, _('ECF')),
            ('ConfigurePrinter', None, _('Configure fiscal printer...'),
             None, None, self._on_ConfigurePrinter__activate),
            ])
        uimanager.insert_action_group(ag, 0)
        uimanager.add_ui_from_string(ui_string)

    def _add_pos_menus(self, uimanager):
        if sysparam(self.conn).POS_SEPARATE_CASHIER:
            return

        ui_string = """<ui>
          <menubar name="menubar">
            <placeholder name="PluginMenus">
              <menu action="ECFMenu">
                <menuitem action="CancelLastDocument" name="CancelLastDocument"/>
                <menuitem action="Summary" name="Summary"/>
                <menuitem action="ReadMemory" name="ReadMemory"/>
              </menu>
            </placeholder>
          </menubar>
        </ui>"""

        ag = gtk.ActionGroup('ECFMenuActions')
        ag.add_actions([
            ('ECFMenu', None, _('ECF')),
            ('ReadMemory', None, _('Read Memory'),
             '<Control>F9', None, self._on_ReadMemory__activate),
            ('CancelLastDocument', None, _('Cancel Last Document'),
             None, None, self._on_CancelLastDocument__activate),
            ])
        ag.add_action_with_accel(self._till_summarize_action, '<Control>F11')

        uimanager.insert_action_group(ag, 0)
        uimanager.add_ui_from_string(ui_string)

    def _add_till_menus(self, uimanager):
        ui_string = """<ui>
          <menubar name="menubar">
            <menu action="ECFMenu">
              <menuitem action="Summary"/>
              <menuitem action="ReadMemory"/>
            </menu>
          </menubar>
        </ui>"""
        ag = gtk.ActionGroup('ECFMenuActions')
        ag.add_actions([
            ('ECFMenu', None, _('ECF')),
            ('ReadMemory', None, _('Read Memory'),
             '<Control>F9', None, self._on_ReadMemory__activate),
            ])
        ag.add_action_with_accel(self._till_summarize_action, '<Control>F11')
        uimanager.insert_action_group(ag, 0)
        uimanager.add_ui_from_string(ui_string)

    def _update_ui_actions(self):
        try:
            has_till = Till.get_current(self.conn) is not None
            till_summarize = has_till
        except TillError:
            till_summarize = False

        self._till_summarize_action.set_sensitive(till_summarize)

    def _open_till(self, till):
        log.info('ECFCouponPrinter.open_till(%r)' % (till,))

        if not self._validate_printer():
            return False

        # Don't do anything on till_open, eg the driver is responsible
        # for sending the LeituraX if needed
        return True

        retval = True
        while True:
            try:
                self._printer.open_till()
            except CouponOpenError:
                self._printer.cancel()
                retval = False
            except DriverError:
                response = warning(
                    _(u"It's not possible to emit a read X for the "
                          "configured printer.\nWould you like to ignore "
                          "this error and continue?"),
                    buttons=((_(u"Cancel"), gtk.RESPONSE_CANCEL),
                             (_(u"Ignore"), gtk.RESPONSE_YES),
                             (_(u"Try Again"), gtk.RESPONSE_NONE)))
                if response == gtk.RESPONSE_NONE:
                    continue
                elif response == gtk.RESPONSE_CANCEL:
                    retval = False

            break

        return retval

    def _close_till(self, till):
        log.info('ECFCouponPrinter.close_till(%r)' % (till,))

        if not self._validate_printer():
            return False

        retval = True
        while True:
            try:
                self._printer.close_till()
            except CouponOpenError:
                self._printer.cancel()
                retval = False
            except DriverError:
                response = warning(
                    short=_(u"It's not possible to emit a reduce Z for the "
                            "configured printer.\nWould you like to ignore "
                            "this error and continue?"),
                    buttons=((_(u"Cancel"), gtk.RESPONSE_CANCEL),
                             (_(u"Ignore"), gtk.RESPONSE_YES),
                             (_(u"Try Again"), gtk.RESPONSE_NONE)))
                if response == gtk.RESPONSE_NONE:
                    continue
                elif response == gtk.RESPONSE_CANCEL:
                    retval = False

            break

        return retval

    def _add_cash(self, till, value):
        log.info('ECFCouponPrinter.add_cash(%r, %r)' % (till, value,))

        if not self._validate_printer():
            return

        self._printer.add_cash(value)

    def _remove_cash(self, till, value):
        log.info('ECFCouponPrinter.remove_cash(%r, %r)' % (till, value,))

        if not self._validate_printer():
            return

        self._printer.remove_cash(value)

    def _confirm_sale(self, sale):
        log.info('ECFCouponPrinter.confirm_sale(%r)' % (sale,))

        if not self._validate_printer():
            return

    def _coupon_create(self, fiscalcoupon):
        if not self._validate_printer():
            return

        coupon = self._printer.create_coupon(fiscalcoupon)
        assert coupon
        for signal, callback in [
            ('open', self._on_coupon__open),
            ('identify-customer', self._on_coupon__identify_customer),
            ('add-item', self._on_coupon__add_item),
            ('remove-item', self._on_coupon__remove_item),
            ('add-payments', self._on_coupon__add_payments),
            ('totalize', self._on_coupon__totalize),
            ('close', self._on_coupon__close),
            ('cancel', self._on_coupon__cancel)
            ]:
            fiscalcoupon.connect_object(signal, callback, coupon)
        return coupon

    def _cancel_last_document(self):
        if yesno(
            _(u"Do you really want to cancel the last document?"),
            gtk.RESPONSE_NO, _(u"Not now"), _("Cancel Last Document")):
            return

        if not self._validate_printer():
            return

        cancelled = self._printer.cancel()
        if not cancelled:
            info(_("Cancelling sale failed, nothing to cancel"))
        else:
            info(_("Document was cancelled"))

    def _till_summarize(self):
        if not self._validate_printer():
            return

        self._printer.summarize()

    #
    # Events
    #

    def _on_StartApplicationEvent(self, appname, app):
        self._add_ui_menus(appname, app.main_window.uimanager)

    def _on_SaleConfirm(self, sale):
        self._confirm_sale(sale)

    def _on_TillOpen(self, till):
        return self._open_till(till)

    def _on_TillClose(self, till):
        return self._close_till(till)

    def _on_TillAddCash(self, till, value):
        self._add_cash(till, value)

    def _on_TillRemoveCash(self, till, value):
        self._remove_cash(till, value)

    def _on_CouponCreatedEvent(self, coupon):
        self._coupon_create(coupon)

    #
    # Callbacks
    #


    def _on_coupon__open(self, coupon):
        coupon.open()

    def _on_coupon__identify_customer(self, coupon, person):
        coupon.identify_customer(person)

    def _on_coupon__add_item(self, coupon, item):
        return coupon.add_item(item)

    def _on_coupon__remove_item(self, coupon, item_id):
        coupon.remove_item(item_id)

    def _on_coupon__add_payments(self, coupon, sale):
        coupon.add_payments(sale)

    def _on_coupon__totalize(self, coupon, sale):
        coupon.totalize(sale)

    def _on_coupon__close(self, coupon):
        return coupon.close()

    def _on_coupon__cancel(self, action):
        self._cancel_last_document()

    def _on_TillSummary__activate(self, action):
        self._till_summarize()

    def _on_ReadMemory__activate(self, action):
        run_dialog(FiscalMemoryDialog, None, self.conn)

    def _on_CancelLastDocument__activate(self, action):
        self._cancel_last_document()

    def _on_ConfigurePrinter__activate(self, action):
        run_dialog(ECFListDialog, None)

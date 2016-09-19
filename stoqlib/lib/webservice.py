# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Web Service APIs """

import datetime
import logging
import os
import platform

from kiwi.component import get_utility

from stoqlib.database.runtime import get_default_store
from stoqlib.lib import asyncrequests
from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.kiwilibrary import library
from stoqlib.lib.osutils import get_product_key
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import InstalledPlugin

log = logging.getLogger(__name__)


def get_main_cnpj(store):
    """Get the MAIN_COMPANY' cnpj without ORM interaction"""
    # We avoid using Storm, otherwise crash-reporting will break
    # for errors that happens in patches modifying any of the
    # tables in the FROM clause below
    result = store.execute("""
        SELECT company.cnpj
        FROM parameter_data, branch, company
        WHERE field_name = 'MAIN_COMPANY' AND
              branch.id::text = field_value AND
              branch.person_id = company.person_id;""")

    data = result.get_one()
    result.close()

    return data[0] if data else ''


class WebService(object):

    API_SERVER = os.environ.get('STOQ_API_HOST', 'http://api.stoq.com.br')

    #
    #   Private API
    #

    def _get_version(self):
        import stoq
        return stoq.version

    def _get_headers(self):
        user_agent = 'Stoq'
        app_info = get_utility(IAppInfo, None)
        if app_info:
            user_agent += ' %s' % (app_info.get('version'), )
        headers = {'User-Agent': user_agent}

        return headers

    def _do_request(self, method, endpoint, **kwargs):
        url = '%s/%s' % (self.API_SERVER, endpoint)
        return asyncrequests.request(
            method, url, headers=self._get_headers(), **kwargs)

    def _get_request(self, endpoint, **kwargs):
        return self._do_request('GET', endpoint, **kwargs)

    def _post_request(self, endpoint, **kwargs):
        return self._do_request('POST', endpoint, **kwargs)

    def _get_usage_stats(self, store):
        from stoqlib.domain.sale import Sale
        from stoqlib.domain.purchase import PurchaseOrder
        from stoqlib.domain.workorder import WorkOrder
        from stoqlib.domain.production import ProductionOrder
        from stoqlib.domain.product import Sellable
        from stoqlib.domain.person import Client, Employee, LoginUser, Branch
        stats = {
            'sale_count': Sale,
            'purchase_count': PurchaseOrder,
            'work_order_count': WorkOrder,
            'production_count': ProductionOrder,
            'sellable_count': Sellable,
            'client_count': Client,
            'user_count': Employee,
            'employeee_count': LoginUser,
            'branch_count': Branch,
        }
        return {key: store.find(value).count() for key, value in stats.items()}

    def _get_company_details(self, store):
        person = sysparam.get_object(store, 'MAIN_COMPANY').person
        company = person.company
        address = person.address
        return {
            # Details
            'stoq_name': person.name,
            'stoq_fancy_name': company.fancy_name,
            'stoq_phone_number': person.phone_number,
            'stoq_email': person.email,
            'stoq_street': address.street,
            'stoq_number': unicode(address.streetnumber or ''),
            'stoq_district': address.district,
            'stoq_complement': address.complement,
            'stoq_postal_code': address.postal_code,
            'stoq_city': address.city_location.city,
            'stoq_state': address.city_location.state,
            'stoq_country': address.city_location.country,
        }

    #
    #   Public API
    #

    def version(self, store, app_version, **kwargs):
        """Fetches the latest version

        :param store: a store
        :param app_version: application version
        """
        try:
            bdist_type = library.bdist_type
        except Exception:
            bdist_type = None

        # We should use absolute paths when looking for /etc
        if os.path.exists(os.path.join(os.sep, 'etc', 'init.d', 'stoq-bootstrap')):
            source = 'livecd'
        elif bdist_type in ['egg', 'wheel']:
            source = 'pypi'
        elif is_developer_mode():
            source = 'devel'
        else:
            source = 'ppa'

        params = {
            'demo': sysparam.get_bool('DEMO_MODE'),
            'dist': ' '.join(platform.dist()),
            'cnpj': get_main_cnpj(store),
            'plugins': ' '.join(InstalledPlugin.get_plugin_names(store)),
            'product_key': get_product_key(),
            'uname': ' '.join(platform.uname()),
            'version': app_version,
            'source': source,
        }
        params.update(self._get_company_details(store))
        params.update(self._get_usage_stats(store))

        endpoint = 'api/stoq/v1/version/%s' % (sysparam.get_string('USER_HASH'), )
        return self._do_request('POST', endpoint, json=params, **kwargs)

    def bug_report(self, report, **kwargs):
        params = {
            'product_key': get_product_key(),
            'report': report,
        }
        endpoint = 'api/stoq/v1/bugreport/%s' % (sysparam.get_string('USER_HASH'), )
        return self._do_request('POST', endpoint, json=params, **kwargs)

    def link_registration(self, name, email, phone, **kwargs):
        params = {
            'hash': sysparam.get_string('USER_HASH'),
            'name': name,
            'email': email,
            'phone': phone,
            'product_key': get_product_key(),
        }
        return self._do_request('POST', 'api/stoq-link/user', data=params, **kwargs)

    def feedback(self, screen, email, feedback, **kwargs):
        default_store = get_default_store()
        params = {
            'cnpj': get_main_cnpj(default_store),
            'demo': sysparam.get_bool('DEMO_MODE'),
            'dist': ' '.join(platform.dist()),
            'email': email,
            'feedback': feedback,
            'plugins': ', '.join(InstalledPlugin.get_plugin_names(default_store)),
            'product_key': get_product_key(),
            'screen': screen,
            'time': datetime.datetime.today().isoformat(),
            'uname': ' '.join(platform.uname()),
            'version': self._get_version(),
        }

        endpoint = 'api/stoq/v1/feedback/%s' % (sysparam.get_string('USER_HASH'), )
        return self._do_request('POST', endpoint, json=params, **kwargs)

    def download_plugin(self, plugin_name, md5sum=None, **kwargs):
        params = {
            'hash': sysparam.get_string('USER_HASH'),
            'md5': md5sum or '',
            'version': self._get_version(),
        }

        endpoint = 'api/stoq-link/egg/%s' % (plugin_name, )
        return self._do_request('GET', endpoint, params=params, **kwargs)

    def status(self, **kwargs):
        endpoint = 'api/stoq/v1/status/%s' % (sysparam.get_string('USER_HASH'), )
        return self._do_request('GET', endpoint, **kwargs)

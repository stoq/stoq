# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Henrique Romano             <henrique@async.com.br>
##
"""Default values for applications"""

import datetime


from stoqlib.domain.interfaces import (IMoneyPM, ICheckPM, IBillPM,
                                       ICardPM, IMultiplePM, IFinancePM,
                                       IGiftCertificatePM)
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


#
# Dates and time
#

MONTH_PERIOD = 30
ONE_DAY = 1

dtime_type = datetime.datetime
START_DATE = dtime_type.today()
END_DATE = dtime_type.today() + datetime.timedelta(days=MONTH_PERIOD)


(INTERVALTYPE_DAY,
 INTERVALTYPE_WEEK,
 INTERVALTYPE_MONTH,
 INTERVALTYPE_YEAR) = range(4)

interval_types = {INTERVALTYPE_DAY:      _('Days'),
                  INTERVALTYPE_WEEK:     _('Weeks'),
                  INTERVALTYPE_MONTH:    _('Months'),
                  INTERVALTYPE_YEAR:     _('Years')}

interval_values = {INTERVALTYPE_DAY:        1,
                   INTERVALTYPE_WEEK:       7,
                   INTERVALTYPE_MONTH:      30,
                   INTERVALTYPE_YEAR:       365}

def calculate_interval(interval_type, intervals):
    """Get the interval type value for a certain INTERVALTYPE_* constant.
    Intervals are useful modes to calculate payment duedates.
    """
    if not interval_values.has_key(interval_type):
        raise KeyError('Invalid interval_type argument for '
                       'calculate_interval function.')
    if not type(intervals) == int:
        raise TypeError('Invalid type for intervals argument. It must be '
                        'integer, got %s' % type(intervals))
    return interval_values[interval_type] * intervals

#
# Payment Methods
#

(METHOD_MONEY,
 METHOD_CHECK,
 METHOD_BILL,
 METHOD_CARD,
 METHOD_FINANCE,
 METHOD_GIFT_CERTIFICATE,
 METHOD_MULTIPLE) = range(7)

def get_method_names():
    return {METHOD_MONEY: _(u'Money'),
            METHOD_CHECK: _(u'Check'),
            METHOD_BILL: _(u'Bill'),
            METHOD_CARD: _(u'Card'),
            METHOD_FINANCE: _(u'Finance'),
            METHOD_GIFT_CERTIFICATE: _(u'Gift Certificate'),
            METHOD_MULTIPLE: _(u'Multiple')}

def get_all_methods_dict():
    return {METHOD_MONEY: IMoneyPM,
            METHOD_CHECK: ICheckPM,
            METHOD_BILL: IBillPM,
            METHOD_CARD: ICardPM,
            METHOD_GIFT_CERTIFICATE: IGiftCertificatePM,
            METHOD_FINANCE: IFinancePM,
            METHOD_MULTIPLE: IMultiplePM}

#
# Kiwi combobox
#

ALL_ITEMS_INDEX = -1

ALL_BRANCHES = _('All branches'), ALL_ITEMS_INDEX

#
# Common methods
#

def get_country_states():
    # This is Brazil-specific information.
    return [ 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
             'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
             'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO' ]


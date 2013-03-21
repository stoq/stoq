# -*- coding: utf-8 -*-

# 2161: Implementar suporte para múltiplas formas de pagamento no wizard de
#      vendas.

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.lib.translation import stoqlib_gettext as _

# Add the 'multiple' payment method when we are updating the database,
# otherwise the payment method will be added automaticaly when setting up the
# system.


def apply_patch(store):
    has_methods = store.find(PaymentMethod).count() > 0
    if has_methods:
        multiple = store.find(PaymentMethod, method_name=u'multiple').one()
        if multiple is None:
            PaymentMethod(method_name=u'multiple',
                          description=_(u'Multiple'),
                          store=store)

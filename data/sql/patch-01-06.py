# -*- coding: utf-8 -*-

#2161: Implementar suporte para múltiplas formas de pagamento no wizard de
#      vendas.

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.lib.translation import stoqlib_gettext as _

# Add the 'multiple' payment method when we are updating the database,
# otherwise the payment method will be added automaticaly when setting up the
# system.

def apply_patch(trans):
    has_methods = PaymentMethod.select(connection=trans).count() > 0
    if has_methods:
        multiple = PaymentMethod.selectOneBy(method_name='multiple',
                                             connection=trans)
        if multiple is None:
            PaymentMethod(method_name=u'multiple',
                          description=_(u'Multiple'),
                          connection=trans)

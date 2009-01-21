# -*- coding: utf-8 -*-

#2161: Implementar suporte para múltiplas formas de pagamento no wizard de
#      vendas.

from stoqlib.domain.payment.method import PaymentMethod

# Add the 'multiple' payment method.

def apply_patch(trans):
    multiple = PaymentMethod.selectOneBy(method_name='multiple',
                                         connection=trans)
    if multiple is None:
        PaymentMethod(method_name=u'multiple',
                      description=u'Multiple',
                      connection=trans)

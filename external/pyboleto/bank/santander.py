#-*- coding: utf-8 -*-
from pyboleto.data import BoletoData, custom_property

class BoletoSantander(BoletoData):
    """Banco Santander
    """
    codigo_banco = '033'
    logo = 'logo_santander.jpg'

    # Numero fixo na posição 5
    fixo = '9'

    # IOS - somente para Seguradoras (Se 7% informar 7, limitado 9%)
    # Demais clientes usar 0 (zero)
    ios = '0'

    nosso_numero = custom_property('nosso_numero', 7)

    def __init__(self, **kwargs):
        BoletoData.__init__(self, **kwargs)
        self.carteira = '102'

    def format_nosso_numero(self):
        return "00000%s-%s" % (
            self.nosso_numero,
            self.modulo11(self.nosso_numero))

    @property
    def campo_livre(self):
        conta = self.formata_numero(self.conta, 7)
        dv_nosso_numero = self.modulo11(self.nosso_numero)

        return '%s%s00000%s%s%s%s' % (self.fixo,
                                      conta,
                                      self.nosso_numero,
                                      dv_nosso_numero,
                                      self.ios,
                                      self.carteira)


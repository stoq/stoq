#-*- coding: utf-8 -*-
from pyboleto.data import BoletoData, custom_property

class BoletoCaixa(BoletoData):
    """Caixa Economica Federal
    """
    codigo_banco = '104'
    logo = 'logo_bancocaixa.jpg'

    inicio_nosso_numero = '80'

    # Nosso numero (sem dv) sao 10 digitos
    def _nosso_numero_get(self):
        return self._nosso_numero
    '''
        Nosso Número sem DV, máximo 8 chars
    '''
    def _nosso_numero_set(self, val):
        self._nosso_numero = (self.inicio_nosso_numero +
                              self.formata_numero(val, 8))

    nosso_numero = property(_nosso_numero_get, _nosso_numero_set)

    @property
    def dv_nosso_numero(self):
        resto2 = self.modulo11(self.nosso_numero.split('-')[0], 9, 1)
        digito = 11 - resto2
        if digito == 10 or digito == 11:
            dv = 0
        else:
            dv = digito
        return dv

    conta= custom_property('conta', 11)

    @property
    def campo_livre(self):
        return "%10s%4s%11s" % (self.nosso_numero,
                                self.agencia,
                                self.conta.split('-')[0])

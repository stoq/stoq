# -*- coding: utf-8
from pyboleto.data import BoletoData, custom_property

class BoletoBradesco( BoletoData ):
    codigo_banco = "237"
    logo = "logo_bancobradesco.jpg"

    def format_nosso_numero(self):
        return "%s/%s-%s" % (
            self.carteira,
            self.nosso_numero,
            self.dv_nosso_numero
        )

    # Nosso numero (sem dv) sao 11 digitos
    nosso_numero = custom_property('nosso_numero', 11)

    @property
    def dv_nosso_numero(self):
        resto2 = self.modulo11(self.nosso_numero,7,1)
        digito = 11 - resto2
        if digito == 10:
            dv = 'P'
        elif digito == 11:
            dv = 0
        else:
            dv = digito
        return dv

    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 7)

    @property
    def campo_livre(self):
        return "%4s%2s%11s%7s%1s" % (self.agencia.split('-')[0],
                                     self.carteira,
                                     self.nosso_numero,
                                     self.conta.split('-')[0],
                                     '0')

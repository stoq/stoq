from pyboleto.data import BoletoData, custom_property

class BoletoItau(BoletoData):
    codigo_banco = '341'
    logo = 'logo_itau.gif'

    nosso_numero = custom_property('nosso_numero', 8)
    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 5)

    @property
    def dac_nosso_numero(self):
        return self.modulo10(self.agencia +
                             self.conta +
                             self.carteira +
                             self.nosso_numero)

    def format_nosso_numero(self):
        return '%s/%s-%s' % (self.carteira,
                             self.nosso_numero,
                             self.dac_nosso_numero)

    @property
    def agencia_conta(self):
        agencia = self.agencia.split('-')[0]
        conta = self.conta.split('-')[0]
        return '%s / %s-%s' % (agencia,
                               conta,
                               self.modulo10(agencia+conta))

    @property
    def campo_livre(self):
        agencia = self.agencia
        conta = self.conta.split('-')[0]
        return "%3s%8s%1s%4s%5s%1s%3s" % (
            self.carteira,
            self.nosso_numero,
            self.dac_nosso_numero,
            agencia,
            conta,
            self.modulo10(agencia+conta),
            '000'
        )

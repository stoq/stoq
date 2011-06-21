from pyboleto.data import BoletoData

class BoletoReal(BoletoData):
    codigo_banco = '356'
    logo = 'logo_bancoreal.jpg'

    @property
    def agencia_conta(self):
        return "%s/%s-%s" % (self.agencia,
                             self.conta,
                             self.digitao_cobranca)

    @property
    def digitao_cobranca(self):
        num = "%s%s%s" % (self.nosso_numero,
                          self.agencia,
                          self.conta)
        return self.modulo10(num)

    @property
    def campo_livre(self):
        return "%4s%7s%1s%13s" % (self.agencia,
                                  self.conta,
                                  self.digitao_cobranca,
                                  self.nosso_numero)

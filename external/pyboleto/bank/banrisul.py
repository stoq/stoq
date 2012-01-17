#-*- coding: utf-8 -*-
from pyboleto.data import BoletoData, custom_property

class BoletoBanrisul(BoletoData):
    """Banco Banrisul
    """
    codigo_banco = '041'
    logo = 'logo_banrisul.jpg'

    nosso_numero = custom_property('nosso_numero', 8)
    conta = custom_property('conta', 6)

    def __init__(self, **kwargs):
        BoletoData.__init__(self, **kwargs)

    # From http://jrimum.org/bopepo/browser/trunk/src/br/com/nordestefomento/jrimum/bopepo/campolivre/AbstractCLBanrisul.java
    def calculaDuploDigito(self, seisPrimeirosCamposConcatenados):
        somaMod10 = self.modulo10(seisPrimeirosCamposConcatenados)
        restoMod10 = self.calculeRestoMod10(somaMod10)
        primeiroDV = self.calculePrimeiroDV(restoMod10)
        somaMod11 = self.modulo11(
            str(int(seisPrimeirosCamposConcatenados) + primeiroDV), 7)
        restoMod11 = self.calculeRestoMod11(somaMod11)
        while restoMod11 == 1:
            primeiroDV = self.encontreValorValidoParaPrimeiroDV(primeiroDV)
            somaMod11 = self.modulo11(
                str(int(seisPrimeirosCamposConcatenados) + primeiroDV), 7)
            restoMod11 = self.calculeRestoMod11(somaMod11)
        segundoDV = self.calculeSegundoDV(restoMod11)
        return str(primeiroDV) + str(segundoDV)

    def calculeSegundoDV(self, restoMod11):
        if restoMod11 == 0:
            return restoMod11
        else:
            return 11 - restoMod11

    def calculePrimeiroDV(self, restoMod10):
        if restoMod10 == 0:
            return 0
        else:
            return restoMod10

    def calculeRestoMod10(self, somaMod10):
        if somaMod10 < 10:
            return somaMod10
        else:
            return somaMod10 % 10

    def encontreValorValidoParaPrimeiroDV(self, primeiroDV):
        if primeiroDV == 9:
            return 0
        else:
            return primeiroDV + 1

    def calculeRestoMod11(self, somaMod11):
        if somaMod11 < 11:
            return somaMod11
        else:
            return somaMod11 % 11

    @property
    def campo_livre(self):
        first = '21%s%s0%s40' % (self.agencia,
                                 self.conta,
                                 self.nosso_numero)
        dv = self.calculaDuploDigito(first)
        # FIXME: probably wrong
        dv = str(int(dv)-1)
        return '21%s%s0%s40%s' % (self.agencia,
                                  self.conta,
                                  self.nosso_numero,
                                  dv)


# -*- coding: utf-8
from pyboleto.data import BoletoData, custom_property

### CAUTION - NÃO TESTADO ###
class BoletoBB( BoletoData ):
    """Gera Dados necessários para criação de boleto para o Banco do Brasil

    @ivar{len_convenio}: Tamanho do campo convenio: 4, 6, 7 ou 8
    @ivar{format_nnumero}: Formato do nosso numero: 1 ou 2 (somente para o
                            convenio com tamanho 6)

    #  Nosso Numero format. 1 or 2
    #  1: Nosso Numero with 5 positions
    #  2: Nosso Numero with 17 positions
    """

    codigo_banco = '001'
    logo = 'logo_bb.gif'

    def __init__(self, **kwargs):
        if not kwargs.has_key('carteira'):
            kwargs['carteira'] = '18'

        self.len_convenio = 7
        if kwargs.has_key('len_convenio'):
            self.len_convenio = int(kwargs.pop('len_convenio'))

        self.format_nnumero = 1
        if kwargs.has_key('format_nnumero'):
            self.format_nnumero = int(kwargs.pop('format_nnumero'))

        super(BoletoBB , self).__init__(**kwargs)

    def format_nosso_numero(self):
        return "%s-%s" % (
            self.nosso_numero,
            self.dv_nosso_numero
        )

    # Nosso numero (sem dv) sao 11 digitos
    def _get_nosso_numero(self):
        return self.convenio + self._nosso_numero

    def _set_nosso_numero(self,val):
        val = str(val)
        if self.len_convenio == 4:
            nn = val.zfill(7)
        if self.len_convenio == 6:
            if self.format_nnumero == 1:
                nn = val.zfill(5)
            elif self.format_nnumero == 2:
                nn = val.zfill(17)
        elif self.len_convenio == 7:
            nn = val.zfill(10)
        elif self.len_convenio == 8:
            nn = val.zfill(9)
        self._nosso_numero = nn

    nosso_numero = property(_get_nosso_numero, _set_nosso_numero)

    def _get_convenio(self):
        return self._convenio

    def _set_convenio(self, val):
        self._convenio = str(val).ljust(self.len_convenio, '0')
    convenio = property(_get_convenio, _set_convenio)

    @property
    def agencia_conta(self):
        return "%s-%s / %s-%s" % (
            self.agencia,
            self.modulo11(self.agencia),
            self.conta,
            self.modulo11(self.conta)
        )

    @property
    def dv_nosso_numero(self):
        return self.modulo11(self.nosso_numero)

    agencia = custom_property('agencia', 4)
    conta = custom_property('conta', 8)

    @property
    def campo_livre(self):
        if self.len_convenio in (7, 8):
            return "%6s%s%s" % ('000000',
                                self.nosso_numero,
                                self.carteira)
        elif self.len_convenio is 6:
            if self.format_nnumero is 1:
                return "%s%s%s%s" % (self.nosso_numero,
                                     self.agencia,
                                     self.conta,
                                     self.carteira)
            if self.format_nnumero is 2:
                return "%s%2s" % (self.nosso_numero,
                                  '21') # numero do serviço

# -*- coding: utf-8 -*-
import unittest
import datetime

from pyboleto.bank.itau import BoletoItau

class TestBancoItau(unittest.TestCase):
    def setUp(self):
        self.dados = BoletoItau(
            carteira = '175',
            conta = '13877-4',
            agencia = '1565',
            data_vencimento = datetime.date(2011, 3, 9),
            valor_documento = 2952.95,
            nosso_numero = '12345678',
        )

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
            '34191.75124 34567.861561 51387.710000 3 49010000295295'
        )

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
            '34193490100002952951751234567861565138771000'
        )

if __name__ == '__main__':
    unittest.main()

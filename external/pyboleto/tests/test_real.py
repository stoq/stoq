# -*- coding: utf-8 -*-
import unittest
import datetime

from pyboleto.bank.real import BoletoReal

class TestBancoReal(unittest.TestCase):
    def setUp(self):
        self.dados = BoletoReal(
            carteira = '06',
            agencia = '0531',
            conta = '5705853',
            data_vencimento = datetime.date(2011, 2, 5),
            valor_documento = 355.00,
            nosso_numero = '123',
        )

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
            '35690.53154 70585.390001 00000.001230 8 48690000035500'
        )

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
            '35698486900000355000531570585390000000000123'
        )

if __name__ == '__main__':
    unittest.main()

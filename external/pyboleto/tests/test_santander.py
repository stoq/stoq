# -*- coding: utf-8 -*-
import unittest
import datetime

from pyboleto.bank.santander import BoletoSantander

class TestSantander(unittest.TestCase):
    def setUp(self):
        self.dados = BoletoSantander(
            agencia = '1333',
            conta = '0707077',
            data_vencimento = datetime.date(2012, 1, 22),
            valor_documento = 2952.95,
            nosso_numero = '1234567',
        )

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
            '03399.07073 07700.000123 34567.901029 6 52200000295295'
        )

    def test_tamanho_codigo_de_barras(self):
        self.assertEqual(len(self.dados.barcode), 44)

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
            '03396522000002952959070707700000123456790102'
        )

if __name__ == '__main__':
    unittest.main()

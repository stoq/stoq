# -*- coding: utf-8 -*-
import unittest
import datetime

from pyboleto.bank.banrisul import BoletoBanrisul

class TestBancoBanrisul(unittest.TestCase):
    def setUp(self):
        self.dados = BoletoBanrisul(
            agencia = '1102',
            conta = '900015',
            data_vencimento = datetime.date(2000, 7, 4),
            valor_documento = 550,
            nosso_numero = '22832563',
        )

    def test_linha_digitavel(self):
        self.assertEqual(
            self.dados.linha_digitavel,
            '04192.11107 29000.150226 83256.340593 8 10010000055000'
        )

    def test_tamanho_codigo_de_barras(self):
        self.assertEqual(len(self.dados.barcode), 44)

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
                         '04198100100000550002111029000150228325634059')

if __name__ == '__main__':
    unittest.main()

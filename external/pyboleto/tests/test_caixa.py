# -*- coding: utf-8 -*-
import unittest
import datetime

from pyboleto.bank.caixa import BoletoCaixa

class TestBancoCaixa(unittest.TestCase):
    def setUp(self):
        self.dados = BoletoCaixa(
            carteira = 'SR',
            agencia = '1565',
            conta = '414-3',
            data_vencimento = datetime.date(2011, 2, 5),
            valor_documento = 355.00,
            nosso_numero = '19525086',
        )

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
            '10498.01952 25086.156509 00000.004143 7 48690000035500'
        )

    def test_tamanho_codigo_de_barras(self):
        self.assertEqual(len(self.dados.barcode), 44)

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
            '10497486900000355008019525086156500000000414'
        )

if __name__ == '__main__':
    unittest.main()

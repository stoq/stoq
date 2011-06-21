# -*- coding: utf-8 -*-
import unittest
import datetime

from pyboleto.bank.bb import BoletoBB

class TestBB(unittest.TestCase):
    def setUp(self):
        d = BoletoBB(
            data_vencimento = datetime.date(2011, 3, 8),
            valor_documento = 2952.95,
            agencia = '9999',
            conta = '99999',
            convenio = '7777777',
            nosso_numero = '87654',
        )
        self.dados = d

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
            '00190.00009 07777.777009 00087.654182 6 49000000295295'
        )

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
            '00196490000002952950000007777777000008765418'
        )

if __name__ == '__main__':
    unittest.main()

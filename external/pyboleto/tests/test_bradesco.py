# -*- coding: utf-8 -*-
import unittest
import datetime

from pyboleto.bank.bradesco import BoletoBradesco

class TestBancoBradesco(unittest.TestCase):
    def setUp(self):
        self.dados = BoletoBradesco(
            carteira = '06',
            agencia = '278-0',
            conta = '039232-4',
            data_vencimento = datetime.date(2011, 2, 5),
            valor_documento = 8280.00,
            nosso_numero = '2125525',
        )

        self.dados2 = BoletoBradesco(
            carteira = '06',
            agencia = '1172',
            conta = '403005',
            data_vencimento = datetime.date(2011, 3, 9),
            valor_documento = 2952.95,
            nosso_numero = '75896452',
            numero_documento = '75896452',
        )

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
            '23790.27804 60000.212559 25003.923205 4 48690000828000'
        )

        self.assertEqual(self.dados2.linha_digitavel,
            '23791.17209 60007.589645 52040.300502 1 49010000295295'
        )

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
            '23794486900008280000278060000212552500392320'
        )
        self.assertEqual(self.dados2.barcode,
            '23791490100002952951172060007589645204030050'
        )

    def test_agencia(self):
        self.assertEqual(self.dados.agencia, '0278-0')

    def test_conta(self):
        self.assertEqual(self.dados.conta, '0039232-4')

if __name__ == '__main__':
    unittest.main()

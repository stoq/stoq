# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Test for lib/cardinals_ptbr module. """

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.cardinals_ptbr import to_words, to_words_as_money


class TestParameter(DomainTest):

    def testToWords(self):
        self.assertEqual(to_words(0), "zero")
        self.assertEqual(to_words(00), "zero")
        self.assertEqual(to_words(000), "zero")
        self.assertEqual(to_words(0000), "zero")
        self.assertEqual(to_words(2), "dois")
        self.assertEqual(to_words(2, feminine=1), "duas")
        self.assertEqual(to_words(3), u"três")
        self.assertEqual(to_words(10), "dez")
        self.assertEqual(to_words(11), "onze")
        self.assertEqual(to_words(15), "quinze")
        self.assertEqual(to_words(20), "vinte")
        self.assertEqual(to_words(25), "vinte e cinco")
        self.assertEqual(to_words(49), "quarenta e nove")
        self.assertEqual(to_words(100), "cem")
        self.assertEqual(to_words(101), "cento e um")
        self.assertEqual(to_words(116), "cento e dezesseis")
        self.assertEqual(to_words(136), "cento e trinta e seis")
        self.assertEqual(to_words(125), "cento e vinte e cinco")
        self.assertEqual(to_words(225), "duzentos e vinte e cinco")
        self.assertEqual(to_words(201), "duzentos e um")
        self.assertEqual(to_words(202), "duzentos e dois")
        self.assertEqual(to_words(202, feminine=1), "duzentas e duas")
        self.assertEqual(to_words(212, feminine=1), "duzentas e doze")
        self.assertEqual(to_words(1000), "um mil")
        self.assertEqual(to_words(2000), "dois mil")
        self.assertEqual(to_words(8000), "oito mil")
        self.assertEqual(to_words(8001), "oito mil e um")
        self.assertEqual(to_words(8101), "oito mil cento e um")
        self.assertEqual(to_words(8301), "oito mil trezentos e um")
        self.assertEqual(to_words(8501), "oito mil quinhentos e um")
        self.assertEqual(to_words(8511), "oito mil quinhentos e onze")
        self.assertEqual(to_words(7641),
                                "sete mil seiscentos e quarenta e um")
        self.assertEqual(to_words(8600), "oito mil e seiscentos")
        self.assertEqual(to_words(10000), "dez mil")
        self.assertEqual(to_words(100000), "cem mil")
        self.assertEqual(to_words(1000000), u"um milhão")
        self.assertEqual(to_words(2000000), u"dois milhões")
        self.assertEqual(to_words(2000100), u"dois milhões e cem")
        self.assertEqual(to_words(2000111), u"dois milhões cento e onze")
        self.assertEqual(to_words(2000102), u"dois milhões cento e dois")
        self.assertEqual(to_words(2000102, feminine=1),
                                    u"dois milhões cento e duas")
        self.assertEqual(to_words(10000111), u"dez milhões cento e onze")
        self.assertEqual(to_words(10000118),
                                    u"dez milhões cento e dezoito")
        self.assertEqual(to_words(100000111),
                                    u"cem milhões cento e onze")
        self.assertEqual(to_words(100010111),
                                   u"cem milhões, dez mil cento e onze")
        names = ['metro', 'metros']
        self.assertEqual(to_words(1, unit_names=names), "um metro")
        self.assertEqual(to_words(2, unit_names=names), "dois metros")
        self.assertEqual(to_words(100, unit_names=names), "cem metros")
        self.assertEqual(to_words(101, unit_names=names),
                                                    "cento e um metros")
        self.assertEqual(to_words(2202, unit_names=names),
                                            "dois mil duzentos e dois metros")
        self.assertEqual(to_words(1000009, unit_names=names),
                                                   u"um milhão e nove metros")

    def testToWordsAsMoney(self):
        names = ['real', 'reais', 'centavo', 'centavos']
        self.assertEqual(to_words_as_money(1, names), "um real")
        self.assertEqual(to_words_as_money(0.01, names), "um centavo")
        self.assertEqual(to_words_as_money(0.25, names),
                                            "vinte e cinco centavos")
        self.assertEqual(to_words_as_money(100.02, names),
                                            "cem reais e dois centavos")
        self.assertEqual(to_words_as_money(100.20, names),
                                        "cem reais e vinte centavos")
        self.assertEqual(to_words_as_money(100.31, names),
                                    "cem reais e trinta e um centavos")
        self.assertEqual(to_words_as_money(100.01, names),
                                                "cem reais e um centavo")
        self.assertEqual(to_words_as_money(100.91, names),
                                    "cem reais e noventa e um centavos")

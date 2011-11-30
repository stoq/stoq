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
""" Test for lib/cardinals_en.py module. """

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.cardinals_en import to_words, to_words_as_money


class TestParameter(DomainTest):

    def testToWords(self):
        self.assertEqual(to_words(0), "zero")
        self.assertEqual(to_words(00), "zero")
        self.assertEqual(to_words(000), "zero")
        self.assertEqual(to_words(0000), "zero")
        self.assertEqual(to_words(2), "two")
        self.assertEqual(to_words(3), "three")
        self.assertEqual(to_words(10), "ten")
        self.assertEqual(to_words(11), "eleven")
        self.assertEqual(to_words(15), "fifteen")
        self.assertEqual(to_words(20), "twenty")
        self.assertEqual(to_words(25), "twenty-five")
        self.assertEqual(to_words(49), "forty-nine")
        self.assertEqual(to_words(100), "one hundred")
        self.assertEqual(to_words(101), "one hundred one")
        self.assertEqual(to_words(116), "one hundred sixteen")
        self.assertEqual(to_words(136), "one hundred thirty-six")
        self.assertEqual(to_words(125), "one hundred twenty-five")
        self.assertEqual(to_words(225), "two hundred twenty-five")
        self.assertEqual(to_words(201), "two hundred one")
        self.assertEqual(to_words(202), "two hundred two")
        self.assertEqual(to_words(1000), "one thousand")
        self.assertEqual(to_words(2000), "two thousand")
        self.assertEqual(to_words(8000), "eight thousand")
        self.assertEqual(to_words(8001), "eight thousand one")
        self.assertEqual(to_words(8101),
                                    "eight thousand one hundred one")
        self.assertEqual(to_words(8301),
                                    "eight thousand three hundred one")
        self.assertEqual(to_words(8501),
                                    "eight thousand five hundred one")
        self.assertEqual(to_words(8511),
                                "eight thousand five hundred eleven")
        self.assertEqual(to_words(7641),
                                "seven thousand six hundred forty-one")
        self.assertEqual(to_words(8600), "eight thousand six hundred")
        self.assertEqual(to_words(10000), "ten thousand")
        self.assertEqual(to_words(100000), "one hundred thousand")
        self.assertEqual(to_words(1000000), "one million")
        self.assertEqual(to_words(2000000), "two million")
        self.assertEqual(to_words(2000100), "two million one hundred")
        self.assertEqual(to_words(2000111),
                                    "two million one hundred eleven")
        self.assertEqual(to_words(2000102),
                                    "two million one hundred two")
        self.assertEqual(to_words(10000111),
                                    "ten million one hundred eleven")
        self.assertEqual(to_words(10000118),
                                    "ten million one hundred eighteen")
        self.assertEqual(to_words(100000111),
                            "one hundred million one hundred eleven")
        self.assertEqual(to_words(100010111),
                "one hundred million ten thousand one hundred eleven")

        names = ['inch', 'inches']
        self.assertEqual(to_words(1, unit_names=names), "one inch")
        self.assertEqual(to_words(2, unit_names=names), "two inches")
        self.assertEqual(to_words(100, unit_names=names),
                                                "one hundred inches")
        self.assertEqual(to_words(101, unit_names=names),
                                        "one hundred one inches")
        self.assertEqual(to_words(2002, unit_names=names),
                                        "two thousand two inches")
        self.assertEqual(to_words(1000009, unit_names=names),
                                        "one million nine inches")

    def testToWordsAsMoney(self):
        names = ['dollar', 'dollars', 'cent', 'cents']
        self.assertEqual(to_words_as_money(1, names), "one dollar")
        self.assertEqual(to_words_as_money(0.01, names), "one cent")
        self.assertEqual(to_words_as_money(0.25, names),
                                            "twenty-five cents")
        self.assertEqual(to_words_as_money(100.02, names),
                                "one hundred dollars and two cents")
        self.assertEqual(to_words_as_money(100.20, names),
                                "one hundred dollars and twenty cents")
        self.assertEqual(to_words_as_money(100.31, names),
                            "one hundred dollars and thirty-one cents")
        self.assertEqual(to_words_as_money(100.01, names),
                                    "one hundred dollars and one cent")
        self.assertEqual(to_words_as_money(100.91, names),
                            "one hundred dollars and ninety-one cents")

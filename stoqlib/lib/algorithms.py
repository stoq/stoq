# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##


# http://en.wikipedia.org/wiki/Luhn algorithm
# Also known as mod 10
def luhn(value):
    if not isinstance(value, basestring):
        raise TypeError("value must be a string, not %s" % (
            value, ))
    total = 0
    try:
        values = map(int, reversed(value))
    except ValueError:
        return None
    for i, v in enumerate(values):
        if not i % 2:
            v *= 2
        if v > 10:
            v -= 9
        total += v
    return str(10 - total % 10)


# FIXME: These are used for boleto generation code and should
#        be replaced and/or merged

def modulo10(num):
    soma = 0
    peso = 2
    for i in range(len(num) - 1, -1, -1):
        parcial = int(num[i]) * peso
        if parcial > 9:
            s = "%d" % parcial
            parcial = int(s[0]) + int(s[1])
        soma += parcial
        if peso == 2:
            peso = 1
        else:
            peso = 2

    resto10 = soma % 10
    if resto10 == 0:
        valor = 0
    else:
        valor = 10 - resto10

    return valor


def modulo11(num, base=9, r=0):
    soma = 0
    fator = 2
    for i in range(len(str(num))).__reversed__():
        parcial10 = int(num[i]) * fator
        soma += parcial10
        if fator == base:
            fator = 1
        fator += 1
    if r == 0:
        soma = soma * 10
        digito = soma % 11
        if digito == 10:
            digito = 0
        return digito
    if r == 1:
        resto = soma % 11
        return resto


# From http://tinyurl.com/lu88m7g
def calculaDuploDigito(seisPrimeirosCamposConcatenados):
    def sum11(s, lmin, lmax):
        soma = 0
        peso = lmin
        for c in reversed(s):
            soma += peso * int(c)
            peso += 1
            if peso > lmax:
                peso = lmin
        return soma
    primeiroDV = modulo10(seisPrimeirosCamposConcatenados)
    somaMod11 = sum11(
        seisPrimeirosCamposConcatenados + str(primeiroDV), 2, 7)
    restoMod11 = calculeRestoMod11(somaMod11)
    while restoMod11 == 1:
        primeiroDV = encontreValorValidoParaPrimeiroDV(primeiroDV)
        somaMod11 = sum11(
            seisPrimeirosCamposConcatenados + str(primeiroDV), 2, 7)
        restoMod11 = calculeRestoMod11(somaMod11)
    segundoDV = calculeSegundoDV(restoMod11)
    return str(primeiroDV) + str(segundoDV)


def calculeSegundoDV(restoMod11):
    if restoMod11 == 0:
        return restoMod11
    else:
        return 11 - restoMod11


def calculePrimeiroDV(restoMod10):
    if restoMod10 == 0:
        return 0
    else:
        return 10 - restoMod10


def calculeRestoMod10(somaMod10):
    if somaMod10 < 10:
        return somaMod10
    else:
        return somaMod10 % 10


def encontreValorValidoParaPrimeiroDV(primeiroDV):
    if primeiroDV == 9:
        return 0
    else:
        return primeiroDV + 1


def calculeRestoMod11(somaMod11):
    if somaMod11 < 11:
        return somaMod11
    else:
        return somaMod11 % 11


if __name__ == '__main__':  # pragma nocover
    assert luhn('810907487') == '5'

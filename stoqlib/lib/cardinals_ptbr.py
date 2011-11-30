# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2003-2007 Async Open Source <http://www.async.com.br>
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
##


def to_words(num, feminine=False, unit_names=None):
    """Retorna uma string representando o valor inteiro passado, por extenso
    @param num: um inteiro
    @type: int
    @param feminine: indica se devemos usar o gênero feminino do
    número, falso por padrão
    @type: boolean
    @param unit_names: lista de nomes de uma unidade
    Exemplo:
    unit_names = ['grama', 'gramas']
    @type: list
    """

    if isinstance(num, float):
        raise TypeError(
            "Números decimais ainda não suportados, envie patches!")
    if not isinstance(num, int):
        raise TypeError("Valor deve ser inteiro")
    if num > 10 ** 9:
        raise ValueError("Valor deve ser menor que 10^9")
    if num > 1 and unit_names:
        return _do_ints(str(num), feminine) + " " + unit_names[1]
    elif unit_names:
        return _do_ints(str(num), feminine) + " " + unit_names[0]
    return _do_ints(str(num), feminine)


def to_words_as_money(num, currency_names):
    """
    Retorna uma string representando a quantia passada, por extenso.
    @param num: a quantia
    @type: int ou float
    @param currency: uma lista com os nomes da moeda a ser utilizada
    Exemplo:
    currency_names = ['real', 'reais', 'centavo', 'centavos']
    @type: list
    """

    # "centavos" e "reais" são sempre masculinos

    ints = int(num)
    decimals = num - int(num)

    intret = _do_ints(str(ints))

    decret = ""
    if decimals:
        decstr = "%.02f" % decimals
        decstr = decstr.split(".")[1]
        decret = _do_ints(decstr)

        # singular
        if decret == "um":
            decret = decret + " " + currency_names[2]
        # plural
        else:
            decret = decret + " " + currency_names[3]

        if intret != "zero":
            decret = " e " + decret

    # apenas centavos
    if intret == "zero" and decret:
        return decret
    # singular
    elif intret == "zero" or intret == "um":
        return intret + " " + currency_names[0] + decret
    # plural
    else:
        return intret + " " + currency_names[1] + decret

#
# Funções que de fato processam os inteiros
#


def _do_ints(ints, feminine=False):
    intlen = len(ints)
    intret = ""

    # Quebro o inteiro em grupos de até 3 dígitos, e vou guardando numa
    # lista
    groups = []
    group = []
    for i in range(intlen):
        group.insert(0, ints[-i - 1])
        if len(group) == 3:
            groups.insert(0, "".join(group))
            group = []

    # Se sobrou algum grupo (que tem menos de 3 elementos), anexo-o
    if group:
        groups.insert(0, "".join(group))

    for i in range(len(groups)):
        group = groups[i]
        level = len(groups) - i - 1

        # Só os números abaixo de 1000 (no nível 0) devem ser femininos
        if level == 0:
            do_fem = feminine
        else:
            do_fem = False

        out = _do_int_group(group, do_fem)

        if not intret:
            intret = out
        elif out:
            # Se temos algo no nível atual, fazer a ligação entre este e
            # o superior, usando 'e' e ','
            if level > 0:
                # Adicionar vírgulas ao invés de 'e's quando nos milhões
                # e bilhões - XXX: correto?
                if " " in out:
                    intret = intret + " " + out
                else:
                    intret = intret + ", " + out
            else:
                if " " in out:
                    intret = intret + " " + out
                else:
                    intret = intret + " e " + out

        if out and mults[level]:
            # Pode-se garantir que nunca teremos "uma" aqui porque
            # não há mults para o nível zero
            assert out != "uma"
            plural = (out != "um")
            suffix = mults[level][plural]
            intret = intret + " " + suffix

    return intret


def _do_int_group(numstr, feminine=False):
    out = []
    levels = len(numstr)
    for i in range(levels):
        num = int(numstr[i])
        level = levels - i - 1
        if num == 0:
            # XXX: levels, quando processando o segundo grupo de 1000,
            # vem como 3 (porque é um string de tamanho 3). Isso é sorte
            # nossa, e deveriamos aqui ser mais estritos para checar se
            # deve retornar zero ou não.
            if levels == 1 and level == 0:
                return "zero"
            # zeros não tem representação
            continue
        if num == 1:
            # Quando o número é um, dois casos especiais ocorrem:
            # - A dezena entre 9 e 20 tem nomes especiais (veja o dict
            #   tens)
            # - Se é na posição da centena, e seguem apenas zeros, é
            #   cem; senão, é cento.
            if level == 1:
                nextnum = int(numstr[i + 1])
                out.append(tens[nextnum])
                break
            if level == 2:
                nextnum = int(numstr[i + 1])
                nextnextnum = int(numstr[i + 2])
                if nextnum == 0 and nextnextnum == 0:
                    out.append("cem")
                    break
                out.append("cento")
                continue
        if feminine:
            w = feminine_words[level][num]
        else:
            w = words[level][num]
        assert w is not None
        out.append(w)

    return " e ".join(out)

#
# Os dicts que guardam a maior parte das strings para conversão seguem
#

words = {}

words[0] = {
    0: None,
    1: 'um',
    2: 'dois',
    3: u'três',
    4: 'quatro',
    5: 'cinco',
    6: 'seis',
    7: 'sete',
    8: 'oito',
    9: 'nove'
}

words[1] = {
    0: None,
    1: None,
    2: 'vinte',
    3: 'trinta',
    4: 'quarenta',
    5: 'cinquenta',
    6: 'sessenta',
    7: 'setenta',
    8: 'oitenta',
    9: 'noventa'
}

words[2] = {
    0: None,
    1: None,
    2: 'duzentos',
    3: 'trezentos',
    4: 'quatrocentos',
    5: 'quinhentos',
    6: 'seiscentos',
    7: 'setecentos',
    8: 'oitocentos',
    9: 'novecentos'
}

# Português tem a maravilha dos números variarem conforme o gênero
feminine_words = {}
feminine_words[0] = words[0].copy()
feminine_words[0].update({1: 'uma', 2: 'duas'})
feminine_words[1] = words[1].copy()
feminine_words[2] = words[2].copy()
feminine_words[2].update({
    2: 'duzentas',
    3: 'trezentas',
    4: 'quatrocentas',
    5: 'quinhentas',
    6: 'seiscentas',
    7: 'setecentas',
    8: 'oitocentas',
    9: 'novecentas'
})

tens = {
    0: "dez",
    1: "onze",
    2: "doze",
    3: "treze",
    4: "quatorze",
    5: "quinze",
    6: "dezesseis",
    7: "dezessete",
    8: "dezoito",
    9: "dezenove"
}

mults = {
    0: None,
    1: ("mil", "mil"),
    2: (u"milhão", u"milhões"),
    3: (u"bilhão", u"bilhões"),
}

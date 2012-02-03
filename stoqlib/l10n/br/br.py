# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

from stoqlib.lib.validators import (validate_cpf,
                                    validate_cnpj)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# CNPJ - Cadastro Nacional da Pessoa Juridica
#
# http://www.receita.fazenda.gov.br/pessoajuridica/cnpj/consulsitcadastralcnpj.htm
# http://en.wikipedia.org/wiki/CNPJ
#


class CNPJ(object):
    label = 'CNPJ'
    entry_mask = '00.000.000/0000-00'

    def validate(self, value):
        return validate_cnpj(value)

company_document = CNPJ()


#
# CPF - Cadastro de Pessoas Físicas
# http://www.receita.fazenda.gov.br/aplicacoes/atcta/cpf/default.htm
# http://en.wikipedia.org/wiki/Cadastro_de_Pessoas_F%C3%ADsicas
#

class CPF(object):
    label = 'CPF'
    entry_mask = '000.000.000-00'

    def validate(self, value):
        return validate_cpf(value)

person_document = CPF()


#
# Federal Units / Estado
# http://en.wikipedia.org/wiki/States_of_Brazil
#

class State(object):
    label = _('State')

    state_list = ["AC",
                  "AL",
                  "AM",
                  "AP",
                  "BA",
                  "CE",
                  "DF",
                  "ES",
                  "GO",
                  "MA",
                  "MG",
                  "MS",
                  "MT",
                  "PB",
                  "PE",
                  "PI",
                  "PR",
                  "RJ",
                  "RO",
                  "RN",
                  "RR",
                  "PA",
                  "RS",
                  "SE",
                  "SC",
                  "SP",
                  "TO"]

    def validate(self, value):
        if value.upper() in self.state_list:
            return True
        return False

state = State()

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

from stoqlib.lib.validators import validate_cnpj

#
# CNPJ - Cadastro Nacion da Pessoa Juridica
#
# http://www.receita.fazenda.gov.br/pessoajuridica/cnpj/consulsitcadastralcnpj.htm
#


class CNPJ(object):
    label = 'CNPJ'
    entry_mask = '00.000.000/0000-00'

    def validate(self, value):
        return validate_cnpj(value)

company_document = CNPJ()

# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
stoqlib/reporting/printing.py:

    Implementação de classe base para configuração da página e desenho de
    elementos fixos de cada página.
"""

import datetime

from reportlab.lib.units import mm

# sibling imports
from stoqlib.reporting.template import BaseReportTemplate
from stoqlib.reporting.default_style import (HIGHLIGHT_COLOR, SPACING,
                                             TEXT_COLOR)

SMALL_FONT = ("Helvetica", 12)

class ReportTemplate(BaseReportTemplate):
    """ 
    Classe responsável pela configuração da página e desenho de elementos
    fixos de cada página. 
    """
    header_height = 10 * mm
    footer_height = 7 * mm
    def __init__(self, filename, report_name, timestamp=0, do_header=1, 
                 do_footer=1, **kwargs):
        """
        Classe responsável pela configuração/desenho básico de cada página.
        Seus parâmetros são:

            - filename: o nome do arquivo onde o relatório deve ser
            desenhado. Esse nome de arquivo é passado como primeiro
            parâmetro para a classe do usuário através da função
            build_report().
            - report_name: o nome do relatório, utilizado, basicamente, na
            construção do rodapé da página.
            - timestamp: define se a hora de criação do relatório deve ser
            especificada no rodapé.
            - do_header: se definido como True, chama o método draw_header()
            da classe do usuário para o desenho do cabeçalho do relatório.
            Esse método é chamado para cada página criada.
            - do_footer: se definido como True, insere um rodapé em cada
            página criada.
        """
        self.timestamp = timestamp
        BaseReportTemplate.__init__(self, filename, report_name,
                                    do_header=do_header, do_footer=do_footer,
                                    **kwargs)

    def draw_header(self, canvas):
        """
        Definido para fins de compatibilidade. Quando o usuário especificar um
        argumento True para o parâmetro do_header, o método draw_header() da
        classe do usuário é chamado. Se este método não existir, o método
        desta classe é chamado para evitar o levantamento de excessão.
        """
        return
       
    def draw_footer(self, canvas):
        """
        Método chamado para o desenho do rodapé de páginas. Esse método é
        chamado para cada página criada se o parâmetro 'do_footer' da classe  
        esteja definido como TRUE (valor padrão assumido caso o usuário não o
        especifique). O rodapé é constituído basicamente do nome do relatório
        (parâmetro report_class da classe), a data de geração, a hora (caso o
        parâmetro time_stamp da classe seja definido como TRUE) e o número da
        página atual.
        """
        if not self.do_footer:
            return

        ts = datetime.datetime.now()
        if self.timestamp:
            date_string = ts.strftime('%d/%m/%Y   %H:%M:%S')
        else:
            date_string = ts.strftime('%d/%m/%Y')

        page_number = "Página: % 2d" % self.get_page_number()

        # Let's start drawing
        
        canvas.setFillColor(HIGHLIGHT_COLOR)
        canvas.rect(self.leftMargin, self.bottomMargin, self.width,
                    self.footer_height, stroke=0, fill=1)
        text_y = self.bottomMargin + 0.5 * SPACING
        canvas.setFillColor(TEXT_COLOR)
        canvas.setFont(*SMALL_FONT)
        canvas.drawString(self.leftMargin + 0.5 * SPACING, text_y,
                          self.report_name)
        canvas.drawRightString(self._rightMargin - 75, text_y, date_string)
        canvas.drawRightString(self._rightMargin - 0.5 * SPACING, text_y,
                               page_number)


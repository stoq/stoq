# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2005 Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

"""
Este módulo implementa a classe BaseReportTemplate, onde todos os métodos para
inserção de elementos no relatório estão definidos e, parcialmente,
implementados.
"""

from reportlab.lib import pagesizes
from reportlab import platypus

from stoqlib.reporting import tables, flowables
from stoqlib.reporting.default_style import (DOC_DEFAULTS, SPACING,
                                             STYLE_SHEET, TABLE_STYLE,
                                             DEFAULT_MARGIN, TABLE_LINE)

class BaseReportTemplate(platypus.BaseDocTemplate):
    """ 
    Classe responsável pela implementação dos métodos para inserção de
    elementos no relatório.
    """
    header_height = 0
    footer_height = 0
    def __init__(self, filename, report_name, pagesize=pagesizes.A4,
                 landscape=0, do_header=0, do_footer=0, **kwargs):
        """
        Classe responsável pela implementação dos métodos para inserção de
        elementos no relatório. Os parâmetros para esta classe, que podem (e
        devem) ser passados à classe ReportTemplate (a qual sua classe deve
        herdar), são:

            - filename: o nome do arquivo onde o relatório deve ser
            construído; esse nome de arquivo é passado por build_report à 
            classe do usuário e é obrigatório.
            - report_name: o nome do relatório, parâmetro obrigatório; o nome
            do relatório é utilizado, basicamente, para a construção do rodapé
            do relatório.
            - pagesize: o tamanho da página; os tamanhos disponíveis podem ser
            encontrados em reportlab.lib.pagesizes.
            - landscape: define se o relatório deve ser gerado no formato
            paisagem; o padrão é o formato "retrato" (landscape=0).
            - do_footer: define se o rodapé deve ser desenhado.
        """
        self.do_header = do_header
        self.do_footer = do_footer
        self.report_name = report_name

        doc_kwargs = DOC_DEFAULTS.copy()
        doc_kwargs.update(kwargs)

        if landscape:
            pagesize = pagesizes.landscape(pagesize)

        platypus.BaseDocTemplate.__init__(self, filename, pagesize=pagesize,
                                          title=report_name, **doc_kwargs)
        self.flowables = []
        self.grouping = 0
        # Group of flowables wich shouldn't be separated on different pages
        self._together_flowables = []
        # Number of flowables to include in the current group.
        self._together_count = 0

    #
    # External API
    #
    
    def save(self):
        """ 
        Construção e salvamento do relatório. Método chamado internamente.
        """
        self.build()

    def build(self):
        """
        Método chamado internamente para construção do relatório. Inicializa
        as páginas do relatório e constrói os elementos.
        """
        # Adds forgotten flowables
        self.end_group()
        
        # If page size has changed, we try to make ReportLab work
        self._calc()

        self.setup_page_templates()
        platypus.BaseDocTemplate.build(self, self.flowables)

    #
    # Doc structure
    #

    def setup_page_templates(self):
        """ 
        Inicialização das páginas do relatório. Temos, basicamente, neste
        método a definição do espaço vertical disponível para desenho,
        baseado no tamanho do rodapé e cabeçalho do relatório.
        """
        frame_y = self.bottomMargin
        height = self.height

        if self.do_header:
            height -= self.header_height

        if self.do_footer:
            height -= self.footer_height
            frame_y += self.footer_height

        main_frame = platypus.Frame(self.leftMargin, frame_y,
                                    self.width, height,
                                    bottomPadding=SPACING,
                                    topPadding=SPACING)

        template = platypus.PageTemplate(id='Normal', frames=main_frame,
                                         pagesize=self.pagesize,
                                         onPage=self.paint_page_canvas)
        self.addPageTemplates([template])

    #
    # Internal API
    #
    
    def add(self, flowable):
        """ 
        Método chamado para inserção de elementos no relatório. Cada elemento
        criado, tal como um parágrafo, uma tabela, um titulo ou uma assinatura
        deve ser inserido no "relatório" atráves deste método para que ele
        possa ser desenhado quando uma chamada ao método build for feita. Esse
        método pertence à API interna e não deve ser chamado na maioria dos
        casos (a menos que você esteja criando um novo tipo de flowable :)
        """
        if self.grouping:
            self._together_flowables.append(flowable)
            self.end_group(self._together_count - 1)
        else:
            self.flowables.append(flowable)

    def start_group(self):
        """ 
        Utilizado para agrupar elementos, como por exemplo, é necessário no
        caso do método para inserção de títulos no relatório; se uma nota de
        título for provida, ela deve ser agrupada junto com o título, pois 
        tanto ela quanto o título são, basicamente, um único elemento: um
        título. 
        """
        self.grouping = 1

    def end_group(self, min_flowables=0):
        """
        Termina o agrupamento de elementos, isto é, todos os elementos que
        deviam ser agrupados já o foram. 
        """
        # Updating _together_count
        if min_flowables >= 0:
            self._together_count = min_flowables
        # If there is not more flowables, close the group and add it.
        if not min_flowables:
            self.grouping = 0
            if self._together_flowables:
                self.add(platypus.KeepTogether(self._together_flowables))
            self._together_flowables = []

    def get_usable_width(self):
        """
        Retorna o espaço horizontal ainda disponível para inserção/desenho de
        elementos 
        """
        return self._rightMargin - self.leftMargin 

    def get_usable_height(self):
        """
        Retorna o espaço vertical ainda disponível para inserção/desenho de
        elementos 
        """
        return self._topMargin - self.bottomMargin

    def set_page_number(self, number):
        """ Define o número da página atual """
        self.add(flowables.PageNumberChanger(number))

    def get_page_number(self):
        """ 
        Retorna o número da página atual, isto é, a página que está sendo
        construída. 
        """
        return self.page
        
    #
    # Features
    #
        
    def add_page_break(self):
        """ Adiciona uma simples quebra de página. """
        self.add(platypus.PageBreak())

    def add_document_break(self):
        """
        Basicamente insere uma quebra de página e inicia um novo documento. É 
        como se tivessemos dois documentos no mesmo relatório.
        """
        self.set_page_number(0)
        self.add_page_break()
        
    def add_blank_space(self, height=10, width=-1):
        """ 
        Adiciona um espaço branco na posição atual. Parametros:

           - height: o tamanho do espaço a ser inserido
           - width: o comprimento do espaço

        Através dos parametros height e width podemos definir o tipo de 
        espacamento que queremos, ou seja, se queremos um espaçamento vertical,
        neste caso definimos height=-1 e width=X (X=tamanho do espacamento) ou
        se queremos um espaçamento horizontal, neste caso, height=X e with=-1;
        espaçamento vertical é o padrão. 
        """
        self.add(platypus.Spacer(width, height))

    def add_signatures(self, labels, *args, **kwargs):
        """
        Adiciona uma assinatura no relatório. Parâmetros:

            - labels: Uma lista de strings de assinatura, cada item da lista
            será uma assinatura e será inserida no relatório lado a lado;
            dependendo do tamanho da página e do parametro landscape, são
            permitidos de 2 a 4 assinaturas na mesma linha.
            - align: define o alinhamento do elemento, deve-se utilizar as
            constantes LEFT, CENTER ou RIGHT definidas neste módulo.
            - line_width: comprimento da linha de assinatura.
            - height: espaço vertical disponibilizado acima da linha.
            - text_align: alinhamento do texto de assinatura.
            - style_data: permite utilizar estilos de parágrafos para o texto
            de assinatura, caso não seja especificado o padrão (definido no
            módulo default_style) será utilizado.
        """
        self.add(flowables.Signature(labels, *args, **kwargs))

    def add_preformatted_text(self, text, style='Raw', *args, **kwargs):
        """
        Adiciona um texto pré-formatado ao relatório. Parâmetros:

            - text: o texto a ser inserido
            - style: define o estilo a ser utilizado. Como padrão o estilo
            'Raw' (consulte o módulo default_style para mais detalhes) é
            utilizado.

        Você pode utilizar esse método para inserção de textos com
        espaçamento.

        Note que parâmetros extras podem ser passados para essa
        função, nesse caso eles serão repassados diretamente para a
        classe Preformatted do ReportLab. 
        """
        style = STYLE_SHEET[style]
        self.add(platypus.flowables.Preformatted(text, style, *args, **kwargs))

    def add_paragraph(self, text, style='Normal', **kwargs):
        """ 
        Adiciona um parágrafo. Parametros:

            - text: o texto a ser inserido no relatório.
            - style: define o estilo a ser utilizado; vários deles estão
            definidos no módulo default_style.
        """
        style = STYLE_SHEET[style]
        self.add(platypus.Paragraph(text, style, **kwargs))

    def add_report_table(self, data, header=None, style=TABLE_STYLE,
                         margins=DEFAULT_MARGIN, align=flowables.CENTER,
                         extra_row=None, table_line=TABLE_LINE,
                         highlight=tables.HIGHLIGHT_ODD, *args, **kwargs):
        """
        Insercão de uma tabela relatório na lista de elementos. Os
        parâmetros para este tipo de tabela, são:

            - data: uma lista de listas contendo as linhas da tabela, cada
            lista interna representa uma linha, enquanto seus elementos
            representam as colunas desta linha.
            - header: uma lista que, se especificada, será utilizada como
            cabeçalho da tabela; o tamanho desta lista deve ser o mesmo
            das listas internas especificadas no parâmetro data.
            - style: permite a especificação de estilos (TableStyle)
            próprios para uso na tabela.
            - margins: margens verticais antes e aoós tabela.
            - align: alinhamento da tabela; você pode encontrar as
            constantes para alinhamento no módulo flowables.
            - extra_row: uma lista com a linha extra à ser inserida. Assim 
            como o parâmetro header, a lista especificada como argumento
            deve possuir o mesmo tamanho das listas internas especificadas
            ao parâmetro data.
            - table_line: define o tipo de linha a ser utilizada na tabela.
            Stoqlib Reporting fornece os tipos TABLE_LINE (linhas simples) e
            TABLE_LINE_BLANK (sem linhas).
            - highlight: habilita (constante HIGHLIGHT_ODD) ou desabilita
            (HIGHLIGHT_NEVER) o uso do estilo zebrado nas linhas da tabela.
            O padrão é habilitado (HIGHLIGHT_ODD).
        """
        self.add_blank_space(margins)
        table_builder = tables.ReportTableBuilder(data, style, header,
                                                  table_line,
                                                  extra_row=extra_row)
        kwargs["align"] = align
        table_builder.set_highlight(highlight)
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)
    
    def add_column_table(self, data, columns, style=TABLE_STYLE,
                         margins=DEFAULT_MARGIN, align=flowables.CENTER,
                         extra_row=None, table_line=TABLE_LINE, do_header=1,
                         highlight=tables.HIGHLIGHT_ODD, *args, **kwargs):
        """
        Inserção de uma tabela coluna na lista de elementos. Os parâmetros
        para este tipo de tabela, são:

            - data: uma lista de listas, onde cada lista internO ideal seria ter a opcao de definir o comportamento: truncar os caracteres OU
rolar para linha abaixo.a representa
            uma lista e cada elemento representa o valor à ser inserido em
            uma coluna.
            - columns: uma lista de instâncias TableColumn representando as
            colunas da tabela.
            - style: estilo de tabela a ser utilizado, permite a
            especificação de estilos (TableStyle) próprios para uso na
            tabela.
            - margins: margens verticais antes e após a tabela.
            - align: alinhamento da tabela; você pode encontrar as
            constantes para alinhamento no módulo flowables.
            - extra_row: uma lista com a linha extra à ser inserida. A lista
            especificada como argumento deve possuir o mesmo tamanho das
            listas internas especificadas ao parâmetro data.
            - table_line: define o tipo de linha a ser utilizado na tabela.
            Stoqlib Reporting fornece os tipos TABLE_LINE (linhas simples)
            e TABLE_LINE_BLANK (sem linhas). O tipo TABLE_LINE é o padrão.
            - do_header: se definido como True, o cabeçalho da tabela será
            desenhado. O nome de cada coluna é obtida através do atributo
            'name' de cada instância especificada lista do argumento
            columns.
            - highlight: habilita (constante HIGHLIGHT_ODD) ou desabilita
            (HIGHLIGHT_NEVER) o uso do estilo zebrado nas linhas da
            tabela. O padrão é habilitado (HIGHLIGHT_ODD).
        """
        self.add_blank_space(margins)
        table_builder = tables.ColumnTableBuilder(data, columns, style=style, 
                                                  table_line=table_line,
                                                  do_header=do_header,
                                                  extra_row=extra_row)
        kwargs["align"] = align
        table_builder.set_highlight(highlight)
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)

    def add_object_table(self, objs, cols, expand=0, width=0, 
                         style=TABLE_STYLE, margins=DEFAULT_MARGIN,
                         extra_row=None, align=flowables.CENTER, 
                         table_line=TABLE_LINE, highlight=tables.HIGHLIGHT_ODD,
                         *args, **kwargs):
        """
        Inserção de uma tabela objeto na lista de elementos. Os parâmetros
        para este tipo de tabela, são:

            - objs: uma lista de objetos na qual a lista de linhas será
            construída.
            - cols: uma lista de colunas ObjectTableColumn.
            - expand:
            - width: utilizado para permitir ao usuário especificar o
              tamanho da tabela.
            - style: parâmetro opcional, permite ao usuário definir um
              estilo de tabela (TableStyle) próprio.
            - margins: margens verticais antes e após a tabela.
            - extra_row: uma lista de valores representado uma linha extra.
              Nem todos os elementos precisam estar preenchidos, mas é
              necessário que eles existam, isto é, é necessário que o
              tamanho desta lista seja o mesmo das listas internas do
              parâmetro data.
            - align: alinhamento da tabela; você pode encontrar as
              constantes para alinhamento no módulo flowables.
            - table_line: define o tipo de linha a ser utilizado na tabela.
              Stoqlib Reporting fornece os tipos TABLE_LINE (linhas simples)
              e TABLE_LINE_BLANK (sem linhas).
            - highlight: habilita (constante HIGHLIGHT_ODD) ou desabilita
              (HIGHLIGHT_NEVER) o uso do estilo zebrado nas linhas da
              tabela. O padrão é habilitado (HIGHLIGHT_ODD).
            
        """
        assert not (expand and width), \
            'Use only expand _OR_ only width at once'
        if expand:
            width = self.get_usable_width()

        self.add_blank_space(margins)
        table_builder = tables.ObjectTableBuilder(objs, cols, style,
                                                  width=width,
                                                  extra_row=extra_row,
                                                  table_line=table_line)
        kwargs["align"] = align
        table_builder.set_highlight(highlight)
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)

    def add_grouping_table(self, objs, column_groups, column_widths,
                           header=None, style=TABLE_STYLE,
                           margins=DEFAULT_MARGIN, align=flowables.CENTER,
                           extra_row=None, *args, **kwargs):
        # """We need to set the table header directly for GroupingTableBuilder
        # because the Columns used with it does not have a name. Note that we
        # have one header for each column width defined and you can use a false
        # value (None, '', 0) to make the previous header span over it."""
        self.add_blank_space(margins)
        table_builder = tables.GroupingTableBuilder(objs, column_groups,
                                                    column_widths,
                                                    style=style,
                                                    header=header, 
                                                    extra_row=extra_row)
        kwargs["align"] = align
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)
    
    def add_data_table(self, data, style=TABLE_STYLE, margins=DEFAULT_MARGIN, 
                       align=flowables.LEFT, *args, **kwargs):
        """ 
        Inserção de uma tabela simples. Os parametros são:

            - data: uma lista de listas, onde cada lista interna representa uma
            linha da tabela, e cada item desta lista as colunas.
            - style: define o estilo que a tabela deve seguir, mais estilos 
            você pode encontrar em stoqlib.reporting.default_style
            - margins: margens verticais antes e depois da tabela.
            - align: alinhamento da tabela
        """
            
        self.add_blank_space(margins)
        table_builder = tables.DataTableBuilder(data, style)
        kwargs["align"] = align
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)
    
    def add_line(self, *args, **kwargs):
        """ Adiciona uma simples linha na posição atual """
        line = flowables.ReportLine(*args, **kwargs)
        self.add(line)

    def add_title(self, title, note=None, space_before=SPACING,
                  style='Title', note_style='Title-Note'):
        """
        Adiciona um título na posição atual. Parâmetros:

            - title: o texto que será o título
            - note: se especificado, será inserido como uma nota ao título
            - space_before: define o tamanho do espaçamento a ser inserido
            após o título
            - style: define o estilo a ser utilizado para o parágrafo 'title';
            não é recomendado sua alteração, uma vez que isto quebra o padrão
            utilizado em todo o documento (a não ser que um novo padrão seja
            especificado em um atributo da classe)
            - note_style: define o estilo a ser utilizado para o parágrafo
            'note'
        """
        self.add_blank_space(space_before)
        self.start_group()
        self.add_line(v_margins=1)
        self.add_paragraph(title, style=style)
        if note:
            self.add_paragraph(note, style=note_style)
        self.add_line(v_margins=1)
        self.end_group(1)

    #
    # Handlers
    #

    def paint_page_canvas(self, canvas, doc):
        """
        Método chamado quando uma nova página é criada; basicamente o
        processamento feito aqui é a inserção do rodapé e cabeçalho. 
        """
        if self.do_header:
            self.draw_header(canvas)
        if self.do_footer:
            self.draw_footer(canvas)
            
    def draw_header(self, canvas):
        raise NotImplementedError

    def draw_footer(self, canvas):
        raise NotImplementedError


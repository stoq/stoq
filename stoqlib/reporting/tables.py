# -*- coding: iso-8859-1 -*-
"""
Este módulo implementa as classes para inserção de todos os tipos de tabelas
disponiblizados pelo Stoqlib Reporting. 
"""
import operator
from types import StringType

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import TableStyle, Paragraph, Table as RTable

# All UPPERCASE constants (except LEFT, CENTER and RIGHT) are from here:
from default_style import *
from flowables import LEFT, CENTER, RIGHT

# Highlight rules:
HIGHLIGHT_ODD = 1
HIGHLIGHT_EVEN = 2
HIGHLIGHT_ALWAYS = 3
HIGHLIGHT_NEVER = 4

class Table(RTable):
    """ Sobrescreve alguns métodos da classe Table de ReportLab. """
    def __init__(self, data, *args, **kwargs):
        """
        Sobrescreve alguns métodos de Table do ReportLab. Isso é feito para,
        essencialmente, reforçar algumas checagens, como, por exemplo, a 
        verificação do tamanho horizontal ocupado pela tabela e fornecer um
        maior feedback ao usuário no caso de algum problema.
        """
        # Reportlab's Table class doesn't provide a better API to set
        # alignment, so we need to handle this specially. We need to be
        # specially careful here because Tables are instantiated by
        # reportlab behind our backs (when splitting tables into pages):
        # we are required to keep the exact same interface as table.
        # This has impact on *Template's create_table, where they stuff
        # align into kwargs -- it used to be a third argument to Table's
        # constructor, and it didn't work!
        if kwargs.has_key("align"):
            align = kwargs["align"]
            del kwargs["align"]
        else:
            align = CENTER
        RTable.__init__(self, data, *args, **kwargs)
        self.hAlign = align

    def wrap(self, avail_width, avail_height):
        """
        Método utilizado para checar o tamanho horizontal ocupado pela tabela,
        informando ao usuário, em caso de erro, o número de pontos
        ultrapassados.
        """
        # If Reportlab doesn't try to calculate the table width before drawning
        # it out of the sheet, we do it for Reportlab.
        total_width = reduce(operator.add, [w or 0 for w in self._colWidths])
        if  total_width > avail_width:
            # We don't use %r on the error message because reportlab dumps all
            # table data instead of the representation. %s the same.
            msg = 'Width of table with columns %s exceeded canvas available ' \
                  'width in %.2f points.'
            raise RuntimeError, msg % (self._colWidths, total_width - avail_width)
        return RTable.wrap(self, avail_width, avail_height)

    def identity(self):
        """
        Chamado quando uma representação da instância é necessária. Retorna a 
        representação da instância através do método __repr__()
        """
        return self.__repr__()

    def __repr__(self):
        """
        Retorna uma representação da instância, requisitada, por exemplo, 
        através de print(). 
        """
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

#
# Table builders
#

class AbstractTableBuilder:
    """ Classe abstrata para criação de um elemento tabela. """
    def __init__(self, data, style=None, extra_row=None):
        """ 
        Classe abstrata para criação de um elemento tabela. Todas as classes 
        dos vários tipos de tabelas fornecidos pelo Stoqlib Reporting herdam 
        desta classe. 
        """
        self.style = TableStyle(parent=style)
        self.data = data
        self.extra_rows = []
        if extra_row:
            self.add_row(extra_row)

    def create_table(self, *args, **kwargs):
        """
        Método responsável pela criação do elemento tabela. Esse método faz
        uma chamada ao método update_style() da classe filha para que
        múltiplos tipos de tabelas diferentes possam usar uma mesma classe
        base e aplicar os estilos próprios de cada um. Retorna uma
        instância/elemento Table.

        Este método é geral e, nem sempre, as classes filhas precisam dele. Em
        algumas situações, temos a classe filha implementando seu próprio
        método, necessário caso processamento extra seja necessário.
        """
        self.update_style()
        return Table(self.get_data(), style=self.style, *args, **kwargs)

    def add_row(self, row_data):
        """ 
        Adiciona as linhas extras à lista de linhas passada para a classe, de
        forma a termos somente uma lista de linhas.
        """
        self.extra_rows.append(row_data)

    def get_data(self):
        """ 
        Método utilizado quando uma classe filha não o implementa. Agrupa as
        linhas passadas ao callsite (classe filha) e as linhas extras em uma
        única lista.
        """
        return self.data + self.extra_rows

    def update_style(self):
        """
        Definido apenas para evitar o levantamento de excessão caso a classe
        filha não implemente o método update_style()
        """
        pass

class DataTableBuilder(AbstractTableBuilder):
    """ Classe que cria um elemento tabela simples. """
    def __init__(self, data, style=None):
        """
        Classe que cria um elemento tabela simples. É chamada internamente
        pelo método add_data_table() e é responsável, basicamente, pela
        definição de estilos à serem utilizados na tabela.
        """
        AbstractTableBuilder.__init__(self, data, style)

    def update_style(self):
        """ Esse método é chamado antes da criação da tabela para definir os
        estilos à serem utilizados em linhas e colunas. 
        """
        style = self.style
        columns = max(map(len, self.data))
        for i in range(columns):
            # Formatting header columns. Last column can not be a header
            if not i % 2 and i < columns - 1:
                style.add('FONTNAME', (i,0), (i,-1), TABLE_HEADER_FONT)
                style.add('FONTSIZE', (i,0), (i,-1), TABLE_HEADER_FONT_SIZE)
                style.add('ALIGN', (i,0), (i,-1), RIGHT)
                # First column don't need the separator
                if i:
                    style.add('LINEBEFORE', (i,0), (i,-1), 0.5, SOFT_LINE_COLOR)
                    style.add('LEFTPADDING', (i,0), (i,-1), 10)
                    style.add('RIGHTPADDING', (i-1,0), (i-1,-1), 10)

    def get_data(self):
        """ Retorna os dados, isto é, a lista de linhas da tabela. """
        return self.data

class ReportTableBuilder(AbstractTableBuilder):
    """ Classe que cria um elemento tabela relatório. """
    highlight = HIGHLIGHT_ODD
    def __init__(self, data, style=None, header=None, table_line=TABLE_LINE,
                 extra_row=None):
        """ 
        Classe que cria um elemento tabela relatório. A instânciação desta
        classe é feita internamente pelo método add_report_table().
        É de responsabilidade desta classe aplicar os estilos da tabela, assim
        como criar uma única lista de linhas considerando cabeçalho, linhas e
        linha extra como somente uma lista de linhas.
        """
        self.header = header
        self.table_line = table_line
        AbstractTableBuilder.__init__(self, data, style=style, 
                                      extra_row=extra_row)

    def set_highlight(self, highlight):
        """ Habilita o estilo zebrado nas linhas da tabela. """
        self.highlight = highlight

    def update_style(self):
        """ 
        Método utilizado para aplicar os estilos à serem utilizados nas linhas
        da tabela.
        """
        style = self.style
        border_reach = len(self.data)
        if self.header:
            style.add('LINEBELOW', (0,0), (-1,0), *self.table_line)
            style.add('FONTNAME', (0,0), (-1,0), TABLE_HEADER_FONT)
            style.add('FONTSIZE', (0,0), (-1,0), TABLE_HEADER_FONT_SIZE)
            style.add('TEXTCOLOR', (0,0), (-1,0), TABLE_HEADER_TEXT_COLOR)
            style.add('BACKGROUND', (0,0), (-1,0), TABLE_HEADER_BACKGROUND)
        else:
            border_reach -= 1
 
        if self.highlight != HIGHLIGHT_NEVER:
            for i in range(0, len(self.data), 2):
                if self.header:
                    i += 1
                style.add('BACKGROUND', (0,i), (-1,i), HIGHLIGHT_COLOR)

        style.add('BOX', (0,0), (-1, border_reach), *self.table_line)

    def create_table(self, *args, **kwargs):
        """
        Aplica os estilos da tabela fazendo uma chamada ao método 
        update_style(), obtêm as linhas da tabela através de get_rows() e
        retorna uma instância do elemento Table.
        """
        if self.header:
            kwargs['repeatRows'] = 1
        self.update_style()
        data = self.get_data()
        return Table(data, style=self.style, *args, **kwargs)

    def get_data(self):
        """
        Retorna uma lista de linhas, considerando linha extra e cabeçalho como
        linhas normais.
        """
        if self.header:
            self.data.insert(0, self.header)
        return AbstractTableBuilder.get_data(self)

class ColumnTableBuilder(ReportTableBuilder):
    """ Classe que cria um elemento tabela coluna. """
    # Note that extra_row needs to be formatted according to the column
    # specification provided.
    def __init__(self, data, columns, style=None, progress_handler=None,
                 table_line=TABLE_LINE, do_header=1, extra_row=None):
        """
        Classe que cria um elemento tabela coluna. Os parâmetros são:

            - data: uma lista de listas, onde cada lista interna representa
            uma lista e cada elemento representa o valor à ser inserido em
            uma coluna.
            - columns: uma lista de instâncias TableColumn representando as
            colunas da tabela.
            - style: estilo de tabela a ser utilizado.
            - table_line: define o tipo de linha da tabela. Em Stoqlib
            Reporting, definimos dois tipos: TABLE_LINE e TABLE_LINE_BLANK
            que representam uma tabela com linhas simples e uma tabela sem
            linhas.
            - do_header: definido como True se a tabela deve possuir um
            cabeçalho.
            - extra_row: uma lista de colunas representando uma linha extra.
            Nem todos os elementos precisam estar preenchidos, mas é 
            necessário que eles existam, isto é, é necessário que o tamanho
            desta lista seja o mesmo das listas internas do parâmetro 'data'
        """
        self.columns = columns
        self.progress_handler = progress_handler
        if do_header:
            header = self._get_header()
        else:
            header = None
        if extra_row:
            extra_row = self.get_row_data(extra_row)
        ReportTableBuilder.__init__(self, self.build_data(data), style, 
                                    header, table_line, extra_row)

    def create_table(self, *args, **kwargs):
        """ 
        Método responsável pela criação da tabela. Cria uma lista com os
        tamanhos de cada coluna e faz uma chamada ao método create_table() de
        ReportTableBuilder para a criação da tabela em si.
        """
        col_widths = [col.width for col in self.columns]
        return ReportTableBuilder.create_table(self, colWidths=col_widths)

    def update_style(self):
        """ 
        Aplica os estilos da tabela e percorre as colunas aplicando seus
        respectivos estilos. 
        """
        ReportTableBuilder.update_style(self)
        col_idx = 0
        for col in self.columns:
            col.update_style(self.style, col_idx)
            col_idx += 1

    def build_data(self, data):
        """
        Cria a lista de linhas, formatando cada coluna de cada lista interna.
        """
        prepared = []
        row_idx = 0
        list_len = len(data)
        step = int(list_len / 50) or 1
        for value in data:
            row_idx += 1
            data = self.get_row_data(value)
            prepared.append(data)
            if self.progress_handler is not None and not row_idx % step:
                self.progress_handler(row_idx, list_len)
        return prepared

    def get_row_data(self, value):
        """ Retorna, formatadas, as colunas de uma linha. """
        # In TableColumns, value is actually a list or tuple; we iterate
        # through that tuple and return the corresponding string_data
        ret = []
        for i in range(len(value)):
            item = value[i]
            ret.append(self.columns[i].get_string_data(item))
        return ret

    def _get_header(self):
        """
        Retorna uma lista com o nome das colunas, baseado nas instâncias
        passada à classe pela lista de colunas TableColumn.
        """
        headers = []
        for col in self.columns:
            if col.name is None:
                raise RuntimeError, 'Column name can not be None for ' \
                                    'ColumnTableBuilder instance' 
            headers.append(col.name)
        return headers

class ObjectTableBuilder(ColumnTableBuilder):
    """ Classe que cria um elemento tabela objeto. """
    def __init__(self, objs, columns, style=None, width=None,
                 progress_handler=None, table_line=TABLE_LINE,
                 extra_row=None):
        """ 
        Classe que cria um elemento tabela objeto. A instânciação desta classe
        e a inserção na lista de elementos é feita pelo método
        add_object_table(). Parâmetros:

            - objs: uma lista de objetos na qual a lista de linhas será
              construída.
            - columns: uma lista de colunas ObjectTableColumn.
            - style: parâmetro opcional, permite ao usuário definir um estilo
              de tabela próprio.
            - width: tamanho da tabela.
            - table_line: permite ao usuário definir o estilo das linhas da
              tabela. Stoqlib Reporting fornece os estilos TABLE_LINE e
              TABLE_LINE_BLANK, que seriam tabelas com linhas simples e
              tabelas sem linhas.
            - extra_row: uma lista de colunas representando uma linha extra.
              Nem todos os elementos precisam estar preenchidos, mas é
              necessário que eles existam, isto é, é necessário que o tamanho
              desta lista seja o mesmo das listas internas do parâmetro
              'data'.
        """
        self._expand_cols(columns, width)
        ColumnTableBuilder.__init__(self, objs, columns, 
                                    style=style,
                                    progress_handler=progress_handler, 
                                    table_line=table_line,
                                    extra_row=extra_row)

    def _get_header(self):
        """
        Obtêm os nomes das colunas para a montagem do cabeçalho e os retorna
        em uma lista. Se alguma coluna estiver definida como virtual e um
        cabeçalho não for provido, a criação do relatório irá falhar aqui.
        """
        header = [col.name for col in self.columns]
        # Avoid passing a list of all empty headers
        if reduce(lambda h1, h2: h1 or h2, header):
            return header

        # If we set a virtual column in a table without header, the first line
        # (the supposed header) will have spanned cells
        if 1 in [c.virtual for c in self.columns]:
            raise RuntimeError, 'Virtual columns in a table (%r) without' \
                                ' headers is not implemented' % self
        return None

    def get_row_data(self, value):
        """
        Cria a lista de linhas, formatando suas respectivas colunas caso
        necessário.
        """
        ret = []
        for col in self.columns:
            ret.append(col.get_string_data(value))
        return ret

    def _expand_cols(self, cols, width):
        """
        Método utilizado para a expansão de colunas baseado em seus
        respectivos fatores.
        """
        col_widths = [col.width for col in cols]
        
        total_expand = reduce(operator.add,
                              [col.expand_factor for col in cols])

        if total_expand and None in col_widths:
            msg = 'You cannot use auto-sized (%r) and expandable ' \
                  ' columns on the same table (%r)'
            raise ValueError, msg % (cols[col_widths.index(None)], self)
        
        if width and not total_expand:
            raise ValueError, 'Setting table width without expanded' \
                              ' col(s) doesn\'t make sense.'

        if total_expand and not width:
            raise ValueError, 'Expandable cols can only be used with ' \
                              'fixed width table.'

        total_width = reduce(operator.add, [w or 0 for w in col_widths])

        if width and total_width > width:
            msg = 'Columns width sum (%.2f) can\'t exceed table width (%.2f).'
            raise RuntimeError, msg % (total_width, width)

        if total_expand:
            extra_width = width - total_width - COL_PADDING * len(cols)
            for col in cols:
                expand_width = extra_width * col.expand_factor / total_expand
                col.width += expand_width

class GroupingTableBuilder(AbstractTableBuilder):
    def __init__(self, objs, column_groups, column_widths, style=None,
                 header=None, extra_row=None):
        self.objs = objs
        self.header = header
        self.column_groups = column_groups
        self.column_widths = column_widths

        self._setup_groups()
        self._setup_columns()

        AbstractTableBuilder.__init__(self, data=objs, style=style,
                                      extra_row=extra_row)

    def create_table(self, *args, **kwargs):
        kwargs['colWidths'] = self.column_widths
        if self.header:
            kwargs['repeatRows'] = 1
        return AbstractTableBuilder.create_table(self, *args, **kwargs)

    def get_data(self):
        data = []
        if self.header:
            data.append(self.header)
        obj_idx = 0
        for obj in self.objs:
            obj_data = []
            obj_idx += 1
            for col_group in self.column_groups:
                row_data = []
                for col in col_group.columns:
                    row_data.append(col.get_string_data(obj))
                    # We need to fill spanned cells with something to make
                    # reportlab happy.
                    row_data.extend([''] * (col.colspan - 1))
                obj_data.append(row_data)
            data.extend(obj_data)
        return data

    def update_style(self):
        style = self.style
        len_objs = len(self.objs)
        header = self.header

        if header:
            line_offset = 1
            self.update_header_style()
        else:
            line_offset = 0

        for group in self.column_groups:
            for obj_idx in range(len_objs):
                group.update_style(self.style, obj_idx, line_offset)
        
        style.add('LINEBEFORE', (0,0), (0,-1), *TABLE_LINE)
        style.add('LINEABOVE', (0,0), (-1,0), *TABLE_LINE)
        style.add('LINEBELOW', (0,0), (-1,-1), *TABLE_LINE)

    def update_header_style(self):
        style = self.style
        header = self.header
        style.add('LINEBELOW', (0,0), (-1,0), *TABLE_LINE)
        style.add('FONTNAME', (0,0), (-1,0), TABLE_HEADER_FONT)
        style.add('FONTSIZE', (0,0), (-1,0), TABLE_HEADER_FONT_SIZE)
        style.add('TEXTCOLOR', (0,0), (-1,0), TABLE_HEADER_TEXT_COLOR)
        style.add('BACKGROUND', (0,0), (-1,0), TABLE_HEADER_BACKGROUND)
        header_span = 0
        for i in range(len(header) - 1, -1, -1):
            if not header[i]:
                header_span += 1
                continue
            style.add('LINEAFTER', (i + header_span, 0),
                      (i + header_span, 0), *TABLE_LINE)
            if header_span:
                style.add('SPAN', (i, 0), (i + header_span, 0))
                header_span = 0
                    
    def _setup_columns(self):
        for group in self.column_groups:
            col_idx = 0
            for col in group.columns:
                widths = self.column_widths[col_idx:col_idx+col.colspan]
                col.width = reduce(operator.add, widths)
                col_idx += col.colspan

    def _setup_groups(self):
        for group in self.column_groups:
            group.setup_group(self.column_groups)


class TableColumn:
    """ Classe para criação de colunas para o elemento tabela coluna. """
    def __init__(self, name=None, width=None, format_string=None,
                 format_func=None, truncate=0, use_paragraph=0, align=LEFT,
                 *args, **kwargs):
        """
        Classe para criação de colunas para o elemento tabela coluna.
        Parâmetros:

            - name: nome da coluna, usado basicamente na construção do
            cabeçalho da tabela.
            - width: tamanho da coluna; se não especificado, o tamanho da
            coluna será expandido.
            - format_string: define uma string pré-formatada para preencher a
            coluna; a string deve incluir um caractere de controle que será
            completado com o valor atribuído à coluna.
            - format_func: especifica a função chamada para formatação do
            valor à ser inserido na coluna. O valor é passado para a função
            como primeiro parâmetro.
            - truncate: se definido como True, formata o valor à ser inserido
            na tabela para ocupar somente o espaço definido para uso; isso é
            útil para campos texto.
            - use_paragraph: define se o texto resultante deve ser encapsulado
            dentro de um parágrafo (Paragraph).
            - align: define o alinhamento da coluna; as constantes para
            alinhamento estão definidas no módulo flowables.
        """

        self.name = name
        self.width = width
        self.format_string = format_string
        self.format_func = format_func
        self.truncate = truncate
        self.use_paragraph = use_paragraph
        self.align = align
        self.args = args
        self.kwargs = kwargs
        assert not (truncate and use_paragraph), \
            'What do you want for %s? Use paragraph or truncate?' % self

    def truncate_string(self, data):
        """
        Se o parâmetro truncate foi definido como True, esse é método chamado
        para formatação da string de uma coluna, fazendo com que ela preencha
        somente o espaço destinado à ela.
        """
        if not self.truncate or not len(data):
            return data
        if self.truncate and not self.width:
            msg = '%s can\'t truncate without a fixed width.' % self
            raise AssertionError, msg
        # XXX This piece of code is *ugly*, but works pretty well with
        # default font and padding.
        string_width = stringWidth(data, DEFAULT_FONTNAME,
                                   DEFAULT_FONTSIZE) or self.width
        # We remove four extra chars to keep the cell padding
        max = int(len(data) / (string_width / self.width)) - 4
        data = '\n'.join([l[:max] for l in data.split('\n')])
        return data

    def get_string_data(self, value):
        """
        Método responsável pela formatação de uma coluna, aplicando o estilo e
        formatando o valor caso necessário.
        """
        if self.format_func:
            value = self.format_func(value)

        if self.format_string:
            value = self.format_string % value

        value = self.truncate_string(value)

        if self.use_paragraph:
            value = Paragraph(value)
        return value

    def update_style(self, style, idx):
        """ Aplica o estilo da tabela. """
        if self.align:
            style.add('ALIGN', (idx,0), (idx,-1), self.align)
        else:
            style.add('LINEBEFORE', (idx,0), (idx,-1), *TABLE_LINE)

    def __repr__(self):
        """ Retorna a representação da classe. """
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

class ObjectTableColumn(TableColumn):
    """ Classe para criação de colunas para o elemento tabela objeto. """
    def __init__(self, name, data_source, expand_factor=0, align=LEFT,
                 virtual=0, truncate=0, *args, **kwargs):
        """ Classe para criação de colunas para o elemento tabela objeto. 
        Parâmetros:
            - name: o nome da coluna;
            - data_source: o nome do atributo que ocupará tal coluna;
            - expand_factor: fator de expansão. Se um valor True for 
            especificado para o parâmetro 'expand' do método add_object_table()
            (ObjecTableBuilder), esse fator de expansão será considerado e 
            quanto maior for em relação à outras colunas, maior será o 
            comprimento desta coluna.
            - align: alinhamento da tabela;
            - virtual: se verdadeiro, a coluna omite seu separador com a 
            coluna anterior e seu cabeçalho será extendido com o cabeçalho da
            coluna anterior.
            - truncate: se definido como True, o valor inserido na coluna será
            truncado caso possua tamanho maior que o comprimento da coluna.
        """
        self.data_source = data_source
        self.expand_factor = expand_factor
        self.virtual = virtual
        TableColumn.__init__(self, name, truncate=truncate, align=align, 
                             *args, **kwargs)

    def get_string_data(self, value):
        """
        Este método é responsável pela formatação apropriada do valor inserido
        em uma coluna,  chamando rotinas específicas de formatação caso seja o
        requisitado.
        """
        if self.data_source is None:
            return ''
        if type(self.data_source) is StringType:
            locals().update(self.kwargs)
            # XXX Dangerous function = eval.
            data = eval(self.data_source)
            if callable(data):
                data = data(*self.args, **self.kwargs)
        elif callable(self.data_source):
            data = self.data_source(value, *self.args, **self.kwargs)
        return TableColumn.get_string_data(self, data)

    def update_style(self, style, idx):
        """ Este método aplica estilos para cada coluna. """
        assert idx or not self.virtual, \
            'The first column can\'t be a virtual column'
        if self.align:
            style.add('ALIGN', (idx,0), (idx,-1), self.align)
        if self.virtual:
            style.add('SPAN', (idx-1, 0), (idx, 0))
        else:
            style.add('LINEBEFORE', (idx,0), (idx,-1), *TABLE_LINE)

    def __repr__(self):
        """
        Método utilizado para gerar uma representação "texto" da instância.
        """
        return '<ObjectTableColumn name: %s at 0x%x>' % (self.name, id(self))

class GroupingTableColumn(ObjectTableColumn):
    """ 
    Essa coluna de tabela trabalha como ObjectTableColumn, mas não implementa
    expansão e colunas virtuais. Essa classe deveria ser usada para objetos
    que precisam de mais de uma linha para representar seus dados; isso
    implementa uma extensão de coluna. Você deveria usar colunas
    GroupingTableColum em um TableColumnGroup.
    """
    def __init__(self, data_source, colspan=1, align=LEFT, truncate=0,
                 *args, **kwargs):
        self.colspan = colspan
        # We don't have a name atribute for this class. So, we just use None
        # for that.
        ObjectTableColumn.__init__(self, None, data_source, truncate=truncate,
                                   align=align, *args, **kwargs)

    def update_style(self, style, idx):
        if self.align:
            style.add('ALIGN', (idx,0), (idx,-1), self.align)

class TableColumnGroup:
    """ Essa classe agrupa coluns do tipo GroupTableColumns. """
    def __init__(self, columns, highlight=HIGHLIGHT_ODD):
        self.columns = columns
        self.highlight = highlight

    def setup_group(self, groups):
        self.total_columns = len(groups)
        self.group_idx = groups.index(self)

    def update_style(self, style, obj_idx, line_offset=0):
        hl = self.highlight
        odd = not obj_idx % 2
        # line_idx is the calculated index of table lines
        line_idx = line_offset + self.group_idx + obj_idx * self.total_columns 

        if hl == HIGHLIGHT_ALWAYS or (hl == HIGHLIGHT_ODD and odd) or \
                                     (hl == HIGHLIGHT_EVEN and not odd):

            style.add('BACKGROUND', (0, line_idx), (-1, line_idx),
                      HIGHLIGHT_COLOR)

        # span_offset is used to remember last spans
        span_offset = 0
        for col_idx in range(len(self)):
            colspan = self.columns[col_idx].colspan
            span = colspan - 1
            # x0. x1 are the begin / end of the spanned range
            x0 = col_idx + span_offset
            x1 = x0 + span
            if span:
                style.add('SPAN', (x0, line_idx), (x1, line_idx))
            # We add a vertical line after every spanned cells end.
            style.add('LINEAFTER', (x1, line_idx), (x1, line_idx), *TABLE_LINE)
            span_offset += span
            self.columns[col_idx].update_style(style, x0)

    def __len__(self):
        return len(self.columns)


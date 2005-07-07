# -*- coding: iso-8859-1 -*-
""" Este módulo disponibiliza estilos de parágrafos e define estilos padrões
à serem utilizados em páginas, tabelas e textos. Os estilos de parágrafos 
definidos aqui tem como objetivo básico extender os estilos fornecidos pelo
ReportLab. É possível também criar seus próprios estilos seguindo o padrão 
utilizado neste módulo, ou seja, simplesmente crie uma instância de
ParagraphStyle e adicione-a à STYLE_SHEET, um exemplo de como é possível 
fazer isso é disponibilizado junto à distribuição e é incluído no diretório
"examples/", com o nome "contract_example.py".

Os estilos de parágrafo disponibilizados são:

    - Normal: Fonte Helvetica, tamanho 10, alinhamento à esquerda
    - Normal-Bold: Fonte Helvetia-Bold, tamanho 10, alinhamento à esquerda
    - Normal-AlignRight: Fonte Helvetica, tamanho 10, alinhamento à esquerda
    - Title: Fonte Helvetica-Bold, tamanho 12, alinhamento à esquerda
    - Title-Note: Fonte Helvetica-Bold, tamanho 8, alinhamento à esquerda
    - Title-AlignCenter: Fonte Helvetica-Bold; tamanho 14, 
      alinhamento ao centro
    - Title-AlignRight: Fonte Helvetica-Bold, tamamho 12, 
      alinhamento à direita
"""
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import TableStyle

STYLE_SHEET = StyleSheet1()
STYLE_SHEET.add(ParagraphStyle(
    'Normal',
    fontName='Helvetica',
    fontSize=10,
    leftIndent=8,
    rightIndent=8,
    spaceAfter=3,
    spaceBefore=3,
    leading=12))

STYLE_SHEET.add(ParagraphStyle(
    'Normal-Bold',
    parent=STYLE_SHEET['Normal'],
    fontName='Helvetica-Bold'))

STYLE_SHEET.add(ParagraphStyle(
    'Normal-AlignRight',
    parent=STYLE_SHEET['Normal'],
    alignment=TA_RIGHT))

STYLE_SHEET.add(ParagraphStyle(
    'Title',
    parent=STYLE_SHEET['Normal'],
    fontName='Helvetica-Bold',
    leading=12,
    fontSize=12))

STYLE_SHEET.add(ParagraphStyle(
    'Title-Note',
    parent=STYLE_SHEET['Normal'],
    leading=10,
    fontSize=8))

STYLE_SHEET.add(ParagraphStyle(
    'Title-AlignCenter',
    parent=STYLE_SHEET['Title'],
    fontSize=14,
    alignment=TA_CENTER))

STYLE_SHEET.add(ParagraphStyle(
    'Title-AlignRight',
    parent=STYLE_SHEET['Title'],
    alignment=TA_RIGHT))

# This is a total padding preview used to calculate the expanded width for the
# columns:
COL_PADDING = 4

DOC_DEFAULTS = {'topMargin': 10 * mm,
                'leftMargin': 10 * mm,
                'rightMarging': 10 * mm,
                'bottomMargin': 20 * mm}

HIGHLIGHT_COLOR = colors.Color(0.9, 0.9, 0.9)
SOFT_LINE_COLOR = colors.gray
TEXT_COLOR = colors.black

SPACING = 4 * mm
DEFAULT_MARGIN = 5

SIGNATURE_FONT = ('Helvetica', 8)

DEFAULT_FONTNAME = 'Times-Roman'
DEFAULT_FONTSIZE = 10

default_table_cmds = (
    ('FONTNAME', (0,0), (-1,-1), DEFAULT_FONTNAME),
    ('FONTSIZE', (0,0), (-1,-1), DEFAULT_FONTSIZE),
    ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
    ('LEADING', (0,0), (-1,-1), 10),
    ('LEFTPADDING', (0,0), (-1,-1), 6),
    ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3))

TABLE_LINE = (1, colors.black)
# Define bordas limpas(brancas) para as tabelas.
# XXX: Hack para que possamos definir uma tabela sem bordas.
TABLE_LINE_BLANK = (1, colors.white)
TABLE_STYLE = TableStyle(default_table_cmds)
TABLE_HEADER_FONT = 'Helvetica-Bold'
TABLE_HEADER_FONT_SIZE = 10
TABLE_HEADER_TEXT_COLOR = colors.black
TABLE_HEADER_BACKGROUND = colors.white


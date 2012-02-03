# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
""" Constants related to flowable styles, like paragraphs, pages, tables and
    texts.
"""

import os

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from kiwi.environ import environ

fonts_dir = environ.get_resource_paths("fonts")[0]

pdfmetrics.registerFont(TTFont("Vera",
                               os.path.join(fonts_dir, "Vera.ttf")))
pdfmetrics.registerFont(TTFont("Vera-B",
                               os.path.join(fonts_dir, "VeraBd.ttf")))
pdfmetrics.registerFont(TTFont("Vera-I",
                               os.path.join(fonts_dir, "VeraIt.ttf")))
pdfmetrics.registerFont(TTFont("Vera-BI",
                               os.path.join(fonts_dir, "VeraBI.ttf")))

# FIXME: Add support for TTF fonts
STYLE_SHEET = StyleSheet1()

STYLE_SHEET.add(ParagraphStyle(
    'Normal',
    fontName='Vera',
    fontSize=10,
    leftIndent=8,
    rightIndent=8,
    spaceAfter=3,
    spaceBefore=3,
    leading=12))

STYLE_SHEET.add(ParagraphStyle(
    'Raw',
    fontName='Vera'))

STYLE_SHEET.add(ParagraphStyle(
    'Normal-Notes',
    parent=STYLE_SHEET['Normal'],
    fontName='Vera',
    alignment=TA_LEFT,
    leftIndent=18))

STYLE_SHEET.add(ParagraphStyle(
    'Normal-Bold',
    parent=STYLE_SHEET['Normal'],
    fontName='Vera-B'))

STYLE_SHEET.add(ParagraphStyle(
    'Normal-AlignRight',
    parent=STYLE_SHEET['Normal'],
    alignment=TA_RIGHT))

STYLE_SHEET.add(ParagraphStyle(
    'Title',
    parent=STYLE_SHEET['Normal'],
    fontName='Vera-B',
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
    fontSize=13,
    alignment=TA_CENTER))

STYLE_SHEET.add(ParagraphStyle(
    'Title-AlignRight',
    parent=STYLE_SHEET['Title'],
    alignment=TA_RIGHT))

STYLE_SHEET.add(ParagraphStyle(
    "TableCell",
    parent=STYLE_SHEET["Normal"],
    alignment=TA_LEFT,
    leftIndent=0,
    rightIndent=0))

STYLE_SHEET.add(ParagraphStyle(
    "TableHeader",
    parent=STYLE_SHEET["TableCell"],
    fontName="Vera-B",
    leading=13))

# This is a total padding preview used to calculate the expanded width for the
# columns:
COL_PADDING = 4

DOC_DEFAULTS = {'topMargin': 10 * mm,
                'leftMargin': 10 * mm,
                'rightMargin': 10 * mm,
                'bottomMargin': 10 * mm}

HIGHLIGHT_COLOR = colors.Color(0.9, 0.9, 0.9)
SOFT_LINE_COLOR = colors.gray
TEXT_COLOR = colors.black

SPACING = 4 * mm
DEFAULT_MARGIN = 5

SIGNATURE_FONT = ('Vera', 8)

default_table_cmds = (
    ('LEADING', (0, 0), (-1, -1), 10),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3))

TABLE_LINE = (1, colors.black)

# XXX: Hack to have table without borders
TABLE_LINE_BLANK = (1, colors.white)
TABLE_STYLE = TableStyle(default_table_cmds)
TABLE_HEADER_FONT = 'Vera'
TABLE_HEADER_FONT_SIZE = 10
TABLE_HEADER_TEXT_COLOR = colors.black
TABLE_HEADER_BACKGROUND = colors.white

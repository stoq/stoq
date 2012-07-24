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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

# This is mostly lifted from
# http://code.google.com/p/pyboleto licensed under MIT

import datetime
import decimal
import operator
import sys
import traceback

from kiwi.currency import currency
from kiwi.datatypes import converter, ValidationError
from kiwi.python import Settable
from reportlab.lib import colors, pagesizes, utils
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from stoqlib.exceptions import ReportError
from stoqlib.lib.crashreport import collect_traceback
from stoqlib.lib.formatters import format_phone_number
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _BookletPDF(object):

    BOOKLETS_PER_PAGE = 4
    DRAWER_WIDTH = 140 * mm
    DRAWEE_WIDTH = 60 * mm
    LINE_HEIGHT = 6.5 * mm
    SPACE = 2
    FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'
    TITLE_FONT_SIZE = 6
    VALUE_FONT_SIZE = 9
    TITLE_DELTA = LINE_HEIGHT - (TITLE_FONT_SIZE + 1)

    def __init__(self, filename):
        self._pagesize = pagesizes.portrait(pagesizes.A4)

        self.pdf_canvas = canvas.Canvas(filename, pagesize=self._pagesize)
        self.pdf_canvas.setStrokeColor(colors.black)

        self._booklets = []

    #
    #  Public API
    #

    def save(self):
        self.pdf_canvas.save()

    def render(self):
        pages = []
        for i in range(0, len(self._booklets), self.BOOKLETS_PER_PAGE):
            page = [self._booklets[i]]
            for j in range(1, self.BOOKLETS_PER_PAGE, 1):
                try:
                    page.append(self._booklets[i + j])
                except IndexError:
                    pass

            pages.append(page)

        for page in pages:
            page_y = self._pagesize[1]
            for i, booklet in zip(range(len(page)), page):
                y = page_y - ((i + 1) * (page_y / self.BOOKLETS_PER_PAGE))
                d = self._draw_booklet(booklet, y)
                # Do not draw horizontal line at the end of the page
                if i < len(page) - 1:
                    self._draw_horizontal_cut_line(2 * mm, y, d[0])

            self._next_page()

    def add_booklet(self, data):
        self._booklets.append(data)

    #
    #  Private
    #

    def _draw_booklet(self, data, y):
        increment = 2 * mm

        x = increment
        d = self._draw_drawee_receipt(data, x, y)
        x += d[0] + increment
        self._draw_vertical_cut_line(x, y + increment, d[1])
        x += increment
        d = self._draw_drawer_receipt(data, x, y)

        return x + d[0], d[1]

    def _draw_drawee_receipt(self, data, x, y):
        self.pdf_canvas.saveState()
        self.pdf_canvas.translate(x, y)

        y = 7.5 * self.LINE_HEIGHT
        right_x = self.DRAWEE_WIDTH / 2

        def draw_line(y, list_):
            self.pdf_canvas.setLineWidth(1)
            self._draw_horizontal_line(0, y, self.DRAWEE_WIDTH)

            for x, title, value in list_:
                if x > 0:
                    self._draw_vertical_line(x, y, self.LINE_HEIGHT)

                x_ = x + self.SPACE
                y_ = y + self.TITLE_DELTA
                self.pdf_canvas.setFont(self.FONT, self.TITLE_FONT_SIZE)
                self.pdf_canvas.drawString(x_, y_, title)

                y_ = y + self.SPACE
                self.pdf_canvas.setFont(self.FONT, self.VALUE_FONT_SIZE)
                self.pdf_canvas.drawString(x_, y_, value)

        # Third line
        if data.sale_id:
            sale_payment_title = '%s / %s' % (_("Sale #"), _("Payment #"))
            sale_payment_value = '%s / %s' % (data.sale_id, data.payment_id)
        else:
            # Support non-sale booklets
            sale_payment_title = _("Payment #")
            sale_payment_value = data.payment_id

        draw_line(y, [
            (0, sale_payment_title, sale_payment_value),
            (right_x, _("Value"), data.value),
            ])

        # Second line
        y += self.LINE_HEIGHT
        draw_line(y, [
            (0, _("Installment"), data.installment),
            (right_x, _("Due date"), data.due_date),
            ])

        # First line
        y += self.LINE_HEIGHT
        draw_line(y, [
            (0, _("Drawee"), data.drawee[:50]),
            ])

        # Header
        y += self.LINE_HEIGHT
        self.pdf_canvas.setLineWidth(2)
        self._draw_horizontal_line(0, y, self.DRAWEE_WIDTH)
        self.pdf_canvas.setFont(self.BOLD_FONT, self.VALUE_FONT_SIZE)
        self.pdf_canvas.drawString(
            self.SPACE, y + self.SPACE,
            data.drawer[:50])

        # Footer
        self.pdf_canvas.setLineWidth(2)
        self._draw_horizontal_line(0, 3 * mm, self.DRAWEE_WIDTH)
        self.pdf_canvas.setFont(self.BOLD_FONT, self.TITLE_FONT_SIZE)
        self.pdf_canvas.drawRightString(self.DRAWEE_WIDTH, 4 * mm,
                                        _("Drawee's Receipt"))

        self.pdf_canvas.restoreState()
        return self.DRAWEE_WIDTH, y

    def _draw_drawer_receipt(self, data, x, y):
        self.pdf_canvas.saveState()
        self.pdf_canvas.translate(x, y)

        y = 1.5 * self.LINE_HEIGHT
        right_fields_width = 35 * mm
        right_fields_x = self.DRAWER_WIDTH - right_fields_width

        def draw_line(y, list_):
            self.pdf_canvas.setLineWidth(1)
            self._draw_horizontal_line(0, y, self.DRAWER_WIDTH)

            for x, title, value in list_:
                if x > 0:
                    self._draw_vertical_line(x, y, self.LINE_HEIGHT)

                x_ = x + self.SPACE
                y_ = y + self.TITLE_DELTA
                self.pdf_canvas.setFont(self.FONT, self.TITLE_FONT_SIZE)
                self.pdf_canvas.drawString(x_, y_, title)

                y_ = y + self.SPACE
                self.pdf_canvas.setFont(self.FONT, self.VALUE_FONT_SIZE)
                self.pdf_canvas.drawString(x_, y_, value)

        def draw_right_field(y, title, value=''):
            self.pdf_canvas.setLineWidth(1)
            self._draw_horizontal_line(right_fields_x, y, right_fields_width)
            self._draw_vertical_line(right_fields_x, y, self.LINE_HEIGHT)

            x_ = right_fields_x + self.SPACE
            y_ = y + self.TITLE_DELTA
            self.pdf_canvas.setFont(self.FONT, self.TITLE_FONT_SIZE)
            self.pdf_canvas.drawString(x_, y_, title)

            x_ = self.DRAWER_WIDTH - 2 * self.SPACE
            y_ = y + self.SPACE
            self.pdf_canvas.setFont(self.FONT, self.VALUE_FONT_SIZE)
            self.pdf_canvas.drawRightString(x_, y_, value)

        # Right fields
        y += self.LINE_HEIGHT
        for title in reversed([
            '(+) %s' % _("Penalty"),
            '(+) %s' % _("Interest"),
            '(-) %s' % _("Discount"),
            '(=) %s' % _("Total value"),
            ]):
            y += self.LINE_HEIGHT
            draw_right_field(y, title)

        # Instructions and demonstrative
        if data.instructions:
            self.pdf_canvas.setFont(self.FONT, self.TITLE_FONT_SIZE)
            self.pdf_canvas.drawString(
                self.SPACE, y + self.TITLE_DELTA,
                _("Instructions"))
            instructions = data.instructions[:4]
            self.pdf_canvas.setFont(self.FONT, self.VALUE_FONT_SIZE)
            for i in range(len(instructions)):
                parts = utils.simpleSplit(instructions[i], self.FONT,
                                          self.VALUE_FONT_SIZE,
                                          right_fields_x)
                y_ = y - (i * self.VALUE_FONT_SIZE)
                self.pdf_canvas.drawString(2 * self.SPACE, y_,
                                           parts[0] if parts else '')
        else:
            i = None

        if data.demonstrative:
            self.pdf_canvas.setFont(self.FONT, self.TITLE_FONT_SIZE)
            if i is not None:
                y_ = (y + self.TITLE_DELTA - self.LINE_HEIGHT -
                      (i + 0.5) * self.VALUE_FONT_SIZE)
            else:
                y_ = y + self.TITLE_DELTA
            self.pdf_canvas.drawString(self.SPACE, y_,
                                       _("Demonstrative"))
            demonstrative = data.demonstrative
            self.pdf_canvas.setFont(self.FONT, self.VALUE_FONT_SIZE)
            for j in range(len(demonstrative)):
                parts = utils.simpleSplit(demonstrative[j], self.FONT,
                                          self.VALUE_FONT_SIZE,
                                          right_fields_x)
                if i is not None:
                    y_ = (y - ((j + i + 0.5) * (self.VALUE_FONT_SIZE)) -
                          self.LINE_HEIGHT)
                else:
                    y_ = y - (j * self.VALUE_FONT_SIZE)

                if y_ - 2 * self.VALUE_FONT_SIZE < 0:
                    # Avoid printing more than fits on booklet
                    self.pdf_canvas.drawString(2 * self.SPACE, y_,
                                               '...')
                    break
                self.pdf_canvas.drawString(2 * self.SPACE, y_,
                                           parts[0] if parts else '')

        # Third line
        y += self.LINE_HEIGHT
        draw_line(y, [
            (0 * mm, _("Emission date"), data.emission_date),
            (30 * mm, _("Sale #"), data.sale_id),
            (50 * mm, _("Payment #"), data.payment_id),
            (70 * mm, _("Installments total"), data.total_value),
            ])
        draw_right_field(y, '(=) %s' % _("Document value"), data.value)

        # Second line
        y += self.LINE_HEIGHT
        draw_line(y, [
            (0 * mm, _("Drawee's document"), data.drawee_document),
            (50 * mm, _("Drawee's phone number"), data.drawee_phone_number),
            ])
        draw_right_field(y, _("Installment"), data.installment)

        # First line
        y += self.LINE_HEIGHT
        draw_line(y, [
            (0 * mm, _("Drawee"), data.drawee),
            ])
        draw_right_field(y, _("Due date"), data.due_date)

        # Header
        y += self.LINE_HEIGHT
        self.pdf_canvas.setLineWidth(2)
        self._draw_horizontal_line(0, y, self.DRAWER_WIDTH)

        self.pdf_canvas.setFont(self.BOLD_FONT, self.VALUE_FONT_SIZE)
        self.pdf_canvas.drawString(
            self.SPACE, y + self.SPACE,
            data.drawer)
        self.pdf_canvas.drawRightString(
            self.DRAWER_WIDTH - 2 * self.SPACE, y + self.SPACE,
            data.drawer_document)

        # Footer
        self.pdf_canvas.setLineWidth(2)
        self._draw_horizontal_line(0, 3 * mm, self.DRAWER_WIDTH)

        self.pdf_canvas.restoreState()
        return self.DRAWER_WIDTH, (y + self.LINE_HEIGHT)

    def _draw_horizontal_cut_line(self, x, y, width):
        self.pdf_canvas.saveState()
        self.pdf_canvas.translate(x, y)

        self.pdf_canvas.setLineWidth(1)
        self.pdf_canvas.setDash(1, 2)
        self._draw_horizontal_line(0, 0, width)

        self.pdf_canvas.restoreState()

    def _draw_vertical_cut_line(self, x, y, height):
        self.pdf_canvas.saveState()
        self.pdf_canvas.translate(x, y)

        self.pdf_canvas.setLineWidth(1)
        self.pdf_canvas.setDash(1, 2)
        self._draw_vertical_line(0, 0, height)

        self.pdf_canvas.restoreState()

    def _draw_horizontal_line(self, x, y, width):
        self.pdf_canvas.line(x, y, x + width, y)

    def _draw_vertical_line(self, x, y, width):
        self.pdf_canvas.line(x, y, x, y + width)

    def _next_page(self):
        self.pdf_canvas.showPage()


class BookletReport(object):
    title = _("Booklet")

    def __init__(self, filename, payments):
        self._payments_added = False
        self._payments = payments
        self._filename = filename
        self._pdf = _BookletPDF(self._filename)

    #
    #  Public API
    #

    def save(self):
        self._add_payments()

        try:
            self._pdf.render()
        except ValueError:
            exc = sys.exc_info()
            tb_str = ''.join(traceback.format_exception(*exc))
            collect_traceback(exc, submit=True)
            raise ReportError(tb_str)

        self._pdf.save()

    #
    #  Private
    #

    def _add_payments(self):
        if self._payments_added:
            return

        payments = sorted(self._payments, key=operator.attrgetter('due_date'))
        len_payments = len(payments)

        for i, payment in zip(range(len_payments), payments):
            if payment.method.method_name != 'store_credit':
                continue

            group = payment.group
            sale = group.sale
            drawer_company = self._get_drawer(payment)
            drawer_person = drawer_company.person
            drawee_person = group.payer

            if sale:
                sale_id = sale.get_order_number_str()
                total_value = self._format_currency(sale.get_total_sale_amount())
            else:
                # Support non-sale booklets
                sale_id = ''
                total_value = ''

            self._pdf.add_booklet(Settable(**dict(
                sale_id=sale_id,
                payment_id=payment.get_payment_number_str(),
                installment=self._format_installment(i + 1, len_payments),
                emission_date=self._format_date(datetime.date.today()),
                due_date=self._format_date(payment.due_date),
                value=self._format_currency(payment.value),
                total_value=total_value,
                drawer=drawer_company.get_description(),
                drawee=drawee_person.name,
                drawer_document=self._get_person_document(drawer_person),
                drawee_document=self._get_person_document(drawee_person),
                drawee_phone_number=self._get_person_phone(drawee_person),
                instructions=self._get_instructions(payment),
                demonstrative=self._get_demonstrative(payment),
                )))

        self._payments_added = True

    def _get_instructions(self, payment):
        conn = payment.get_connection()
        instructions = sysparam(conn).BOOKLET_INSTRUCTIONS
        return instructions.split('\n')

    def _get_demonstrative(self, payment):
        demonstrative = []
        sale = payment.group.sale
        if sale:
            items = sale.get_items()
            has_decimal = any([item.quantity - int(item.quantity) != 0
                               for item in items])
            for item in items:
                quantity = item.quantity if has_decimal else int(item.quantity)
                demonstrative.append('%s x %s' % (quantity,
                                                  item.get_description()))

        return demonstrative

    def _get_drawer(self, payment):
        sale = payment.group.sale
        if sale and sale.branch:
            return sale.branch

        return sysparam(payment.get_connection()).MAIN_COMPANY

    def _get_person_document(self, person):
        if person.individual:
            return person.individual.cpf
        if person.company:
            return person.company.cnpj

        return ''

    def _get_person_phone(self, person):
        phone_number = format_phone_number(person.phone_number)
        mobile_number = format_phone_number(person.mobile_number)
        if phone_number and mobile_number:
            return '%s | %s' % (phone_number, mobile_number)

        return phone_number or mobile_number

    def _format_installment(self, installment, total_installments):
        return _("%s of %s") % (installment, total_installments)

    def _format_currency(self, value):
        if isinstance(value, (int, float)):
            value = decimal.Decimal(value)
        try:
            return converter.as_string(currency, value)
        except ValidationError:
            return ''

    def _format_date(self, date):
        if isinstance(date, datetime.datetime):
            date = date.date()
        try:
            return converter.as_string(datetime.date, date)
        except ValidationError:
            return ''

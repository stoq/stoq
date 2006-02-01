#!/usr/bin/env python
from sys import path
path.insert(0, '..')

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

from stoqlib.reporting import  build_report, print_preview
from stoqlib.reporting.printing import ReportTemplate
from stoqlib.reporting.default_style import STYLE_SHEET

class ContractExample(ReportTemplate):
    def __init__(self, filename):
        ReportTemplate.__init__(self, filename, "", do_footer=0, topMargin=0,
                                bottomMargin=0)
        self.add_title("Termo de Compromisso de Estágio")
        self.add_info_table()
        self.add_blank_space(10)
        self.add_contract_body()

    def create_extra_styles(self):
        styles = [ParagraphStyle("JustifyParagraph",
                                 fontName="Helvetica",
                                 fontSize=10,
                                 leading=11,
                                 alignment=TA_JUSTIFY,
                                 spaceAfter=6)]
        for style in styles:
            STYLE_SHEET.add(style)
    
    def add_info_table(self):
        rows = [["Concedente:", ""],
                ["Endereço:", ""],
                ["Estagiário:", ""],
                ["Instituição de Ensino:", ""],
                ["Endereço:", ""],
                ["Nível:", ""],
                ["Curso:", ""]]
        self.add_data_table(rows)

    def add_contract_body(self):
        contract_body = [
            ("As Partes acima justificadas assinam o presente Termo de "
             "Compromisso regido pelas condições estabelecidas no "
             "Instrumento Jurídico celebrado com a Instituição de Ensino e "
             "mediante as seguintes condições:"),
            ("1- O propósito do presente estágio é propiciar ao estagiário(a) "
             "treinamento prático, aperfeiçoamento técnico, cultural, "
             "científico e de relacionamento humano, como complementação do "
             "ensino ou aprendizagem a serem planejadas de conformidade com "
             "os programas e calendários escolares."),
            ("2 - A jornada de atividade do(a) estagiário(a), compatíveis "
             "com o seu horário escolar e com o horário da CONCEDENTE, Terá "
             "uma carga de _______ horas semanais. O termo de compromisso "
             "terá início em ____________________ e término em "
             "____________________, podendo ser interrompido a qualquer "
             "momento, unilateralmente, mediante comunicação escrita. Nos "
             "períodos de férias escolares, a jornada de estágio será "
             "estabelecida de comum acordo entre o(a) estagiário(a) e a "
             "CONCEDENTE, com o conhecimento da Instituição de Ensino "
             "envolvida."),
            ("3 - Fica estabelecida a Bolsa de Estágio de R$ ________,00 por "
             "mês."),
            ("4 - O presente estágio não cria vínculo empregatício de qualquer "
             "natureza nos termos de legislação aplicável em vigor. Na "
             "vigência deste compromisso, o(a) estagiário(a) compromete-se a "
             "observar as normas de segurança bem como as instruções "
             "aplicáveis a terceiros."),
            ("A CONCEDENTE incluirá o(a) estagiário(a), em uma apólice de "
             "seguros de acidentes pessoais. Se solicitado pela Instituição de "
             "Ensino do(a) estagiário(a), a CONCEDENTE expedirá uma Declaração"
             "de Estágio."),
            ("5 - O(a) estagiário(a) deverá informar de imediato e por "
             "escrito à CONCEDENTE, qualquer fato que interrompa, suspenda ou "
             "cancele sua matrícula na Instituição de Ensino interveniente, "
             "ficando ele responsável de quaisquer despesas causadas pela "
             "ausência dessa informação."),
            ("6 - E por estarem de comum acordo com as condições acima, "
             "firmam o presente compromisso em três vias de igual teor.")]

        self.create_extra_styles()
        map(lambda t: self.add_paragraph(t, style="JustifyParagraph"),
            contract_body)
        self.add_blank_space(20)
        self.add_paragraph("Data:", style="JustifyParagraph")
        self.add_blank_space(10)
        self.add_paragraph("Testemunhas:", style="JustifyParagraph")

        self.add_signatures(["Assinatura do(a) Estagiário(a)",
                             "Responsável Legal"], height=20)
        self.add_signatures(["Responsável Legal", "Instituição de Ensino"])

filename = build_report(ContractExample)
print_preview(filename)


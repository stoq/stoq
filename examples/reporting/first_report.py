#!/usr/bin/env python

from sys import path
path.insert(0, '..')

from stoqlib.reporting.utils import print_preview, build_report
from stoqlib.reporting.printing import ReportTemplate

# Classe utilizada como "container", simplesmente utilizada para
# guardar/unificar dados.
class Client:
    def __init__(self, name, email, tel, birth_date, genre,
                 address, city, state, notes):
        self.name = name
        self.email = email
        self.tel = tel
        self.birth_date = birth_date
        self.genre = genre
        self.address = address
        self.city = city
        self.state = state
        self.notes = notes

class ClientDetailsReport(ReportTemplate):
    report_name = "Informação sobre Cliente"
    def __init__(self, filename, client):
        ReportTemplate.__init__(self, filename, self.report_name)
        self.add_title(self.report_name)
        self.add_data_table(self.get_rows(client))
        self.add_blank_space()
        self.add_paragraph("<b>Notas:</b> %s" % client.notes)

    def get_rows(self, client):
        rows = [["Nome:", client.name, "Email:", client.email],
                ["Nascimento:", client.birth_date,
                 "Sexo:", client.genre],
                ["Endereço:", client.address,
                 "Cidade/Estado:", "%s/%s" % (client.city, client.state)]]
        return rows

    
    def add_basic_information_table(self, client):
        row = [["Data do Cadastro:", client.date],
               ["Endereço: ", client.address],
               ["",""],
               ["Notas:", client.notes]]
        self.add_data_table(row)

client = Client(name="Oziel Fernandes da Silva",
                email="ozfesi@yahoo.com.br",
                tel="3376-2309",
                birth_date="25/03/1976",
                genre="Masculino",
                address="Rua Alvares de Azevedo, N. 1283 Jd. Ipiranga",
                city="São Paulo",
                state="SP",
                notes="Sem notas")

report_filename = build_report(ClientDetailsReport, client)
print_preview(report_filename)


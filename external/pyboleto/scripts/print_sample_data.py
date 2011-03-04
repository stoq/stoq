# -*- coding: utf-8 -*-
from pyboleto.bank.real import BoletoReal
from pyboleto.bank.bradesco import BoletoBradesco
from pyboleto.bank.caixa import BoletoCaixa
from pyboleto.bank.bancodobrasil import BoletoBB
from pyboleto.pdf import BoletoPDF
import datetime

def print_bb():
    listaDados = []
    for i in range(2):
        d = BoletoBB(7,2)
        d.nosso_numero = '87654'
        d.numero_documento = '27.030195.10'
        d.convenio = '7777777'
        d.especie_documento = 'DM'

        d.carteira = '18'
        d.cedente = 'Empresa Empresa Empresa Empresa Empresa LTDA'
        d.agencia = '9999'
        d.conta = '99999'

        d.data_vencimento = datetime.date(2010, 3, 27)
        d.data_documento = datetime.date(2010, 02, 12)
        d.data_processamento = datetime.date(2010, 02, 12)

        d.instrucoes = [
            "- Linha 1",
            "- Sr Caixa, cobrar multa de 2% após o vencimento",
            "- Receber até 10 dias após o vencimento",
            ]
        d.demonstrativo = [
            "- Serviço Teste R$ 5,00",
            "- Total R$ 5,00",
            ]
        d.valor_documento = 255.00

        d.sacado = [
            "Cliente Teste %d" % (i+1),
            "Rua Desconhecida, 00/0000 - Não Sei - Cidade - Cep. 00000-000",
            ""
            ]
        listaDados.append( d )

    print "Normal"
    boleto = BoletoPDF( 'boleto-bb-formato-normal-teste.pdf' )
    for i in range(len(listaDados)):
        print i
        boleto.drawBoleto(listaDados[i])
        boleto.nextPage()
    boleto.save()



def print_test():
    listaDadosReal = []
    for i in range(2):
        d = BoletoReal()
        d.carteira = '57'  # Contrato firmado com o Banco Real
        d.cedente = 'Empresa Empresa Empresa Empresa Empresa LTDA'
        d.agencia = '0531'
        d.conta = '5705853'

        d.data_vencimento = datetime.date(2010, 3, 27)
        d.data_documento = datetime.date(2010, 02, 12)
        d.data_processamento = datetime.date(2010, 02, 12)

        d.instrucoes = [
            "- Linha 1",
            "- Sr Caixa, cobrar multa de 2% após o vencimento",
            "- Receber até 10 dias após o vencimento",
            ]
        d.demonstrativo = [
            "- Serviço Teste R$ 5,00",
            "- Total R$ 5,00",
            ]
        d.valor_documento = 5.00

        d.nosso_numero = "%d" % (i+2)
        d.numero_documento = "%d" % (i+2)
        d.sacado = [
            "Cliente Teste %d" % (i+1),
            "Rua Desconhecida, 00/0000 - Não Sei - Cidade - Cep. 00000-000",
            ""
            ]
        listaDadosReal.append( d )

    listaDadosBradesco = []
    for i in range(2):
        d = BoletoBradesco()
        d.carteira = '57'  # Contrato firmado com o Banco Bradesco
        d.cedente = 'Empresa Empresa Empresa Empresa Empresa LTDA'
        d.agencia = '0531-3'
        d.conta = '5705853-2'

        d.data_vencimento = datetime.date(2010, 3, 27)
        d.data_documento = datetime.date(2010, 02, 12)
        d.data_processamento = datetime.date(2010, 02, 12)

        d.instrucoes = [
            "- Linha 1",
            "- Sr Caixa, cobrar multa de 2% após o vencimento",
            "- Receber até 10 dias após o vencimento",
            ]
        d.demonstrativo = [
            "- Serviço Teste R$ 5,00",
            "- Total R$ 5,00",
            ]
        d.valor_documento = 5.00

        d.nosso_numero = "%d" % (i+2)
        d.numero_documento = "%d" % (i+2)
        d.sacado = [
            "Cliente Teste %d" % (i+1),
            "Rua Desconhecida, 00/0000 - Não Sei - Cidade - Cep. 00000-000",
            ""
            ]
        listaDadosBradesco.append( d )

    listaDadosCaixa = []
    for i in range(2):
        d = BoletoCaixa()
        d.carteira = 'SR'  # Contrato firmado com o Banco Bradesco
        d.cedente = 'Empresa Empresa Empresa Empresa Empresa LTDA'
        d.agencia = '1565'
        d.conta = '414-3'

        d.data_vencimento = datetime.date(2010, 3, 27)
        d.data_documento = datetime.date(2010, 02, 12)
        d.data_processamento = datetime.date(2010, 02, 12)

        d.instrucoes = [
            "- Linha 1",
            "- Sr Caixa, cobrar multa de 2% após o vencimento",
            "- Receber até 10 dias após o vencimento",
            ]
        d.demonstrativo = [
            "- Serviço Teste R$ 5,00",
            "- Total R$ 5,00",
            ]
        d.valor_documento = 255.00

        d.nosso_numero = "%d" % (i+2)
        d.numero_documento = "%d" % (i+2)
        d.sacado = [
            "Cliente Teste %d" % (i+1),
            "Rua Desconhecida, 00/0000 - Não Sei - Cidade - Cep. 00000-000",
            ""
            ]
        listaDadosCaixa.append( d )


    # Bradesco Formato carne - duas paginas por folha A4
    print "Carne"
    boleto = BoletoPDF( 'boleto-bradesco-formato-carne-teste.pdf', True )
    for i in range(0,len(listaDadosBradesco),2):
        print i, i+1
        boleto.drawBoletoCarneDuplo(
            listaDadosBradesco[i],
            listaDadosBradesco[i+1]
        )
        boleto.nextPage()
    boleto.save()

    # Bradesco Formato normal - uma pagina por folha A4
    print "Normal"
    boleto = BoletoPDF( 'boleto-bradesco-formato-normal-teste.pdf' )
    for i in range(len(listaDadosBradesco)):
        print i
        boleto.drawBoleto(listaDadosBradesco[i])
        boleto.nextPage()
    boleto.save()

    # Real Formato normal - uma pagina por folha A4
    print "Normal"
    boleto = BoletoPDF( 'boleto-real-formato-normal-teste.pdf' )
    for i in range(len(listaDadosReal)):
        print i
        boleto.drawBoleto(listaDadosReal[i])
        boleto.nextPage()
    boleto.save()

    # Caixa Formato normal - uma pagina por folha A4
    print "Carne"
    boleto = BoletoPDF( 'boleto-caixa-formato-carne-teste.pdf', True )
    for i in range(0,len(listaDadosCaixa),2):
        print i, i+1
        boleto.drawBoletoCarneDuplo(
            listaDadosCaixa[i],
            listaDadosCaixa[i+1]
        )
        boleto.nextPage()
    boleto.save()

    # Caixa Formato normal - uma pagina por folha A4
    print "Normal"
    boleto = BoletoPDF( 'boleto-caixa-formato-normal-teste.pdf' )
    for i in range(len(listaDadosCaixa)):
        print i
        boleto.drawBoleto(listaDadosCaixa[i])
        boleto.nextPage()
    boleto.save()

    print "Ok"

if __name__ == "__main__":
    print_test()
    print_bb()

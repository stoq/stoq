# -*- coding: utf-8 -*-
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.common import I2of5
from reportlab.lib.units import mm
from reportlab.lib import colors, pagesizes, utils

class BoletoPDF:

    (FORMAT_BOLETO,
     FORMAT_CARNE) = range(2)

    def __init__(self, file_descr, format=FORMAT_BOLETO):
        self.file_descr = file_descr
        self.width = 190*mm
        self.widthCanhoto = 70*mm
        self.heightLine = 6.5*mm
        self.space = 2
        self.fontSizeTitle = 6
        self.fontSizeValue = 9
        self.deltaTitle = self.heightLine - (self.fontSizeTitle + 1)
        self.deltaFont = self.fontSizeValue + 1;
        self.format = format

        pagesize = pagesizes.A4
        if format == self.FORMAT_CARNE:
            pagesize = pagesizes.landscape(pagesize)

        self.pdfCanvas = canvas.Canvas(self.file_descr, pagesize=pagesize)
        self.pdfCanvas.setStrokeColor(colors.black)


        self.boletos = []

    def drawReciboSacadoCanhoto(self, boletoDados, x, y ):
        self.pdfCanvas.saveState();
        self.pdfCanvas.translate( x*mm, y*mm );

        linhaInicial = 12

        # Horizontal Lines
        self.pdfCanvas.setLineWidth(2)
        self.__horizontalLine( 0, 0, self.widthCanhoto )

        self.pdfCanvas.setLineWidth(1)
        self.__horizontalLine( 0, (linhaInicial + 0)*self.heightLine,
            self.widthCanhoto )
        self.__horizontalLine( 0, (linhaInicial + 1)*self.heightLine,
            self.widthCanhoto )

        self.pdfCanvas.setLineWidth(2)
        self.__horizontalLine( 0, (linhaInicial + 2)*self.heightLine,
            self.widthCanhoto )

        # Vertical Lines
        self.pdfCanvas.setLineWidth(1)
        self.__verticalLine( self.widthCanhoto - (35*mm),
            (linhaInicial + 0) * self.heightLine, self.heightLine )
        self.__verticalLine( self.widthCanhoto - (35*mm),
            (linhaInicial + 1) * self.heightLine, self.heightLine )

        self.pdfCanvas.setFont( 'Helvetica-Bold', 6 )
        self.pdfCanvas.drawRightString( self.widthCanhoto,
            0 * self.heightLine + 3,
            'Recibo do Sacado'
        )

        # Titles
        self.pdfCanvas.setFont('Helvetica', 6 )
        self.deltaTitle = self.heightLine - (6 + 1)

        self.pdfCanvas.drawString(
            self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.deltaTitle,
            'Nosso Número'
        )
        self.pdfCanvas.drawString(
            self.widthCanhoto - (35*mm) + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.deltaTitle,
            'Vencimento'
        )
        self.pdfCanvas.drawString(
            self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.deltaTitle,
            'Agência/Código Cedente'
        )
        self.pdfCanvas.drawString(
            self.widthCanhoto - (35*mm) + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.deltaTitle,
            'Valor Documento'
        )


        # Values
        self.pdfCanvas.setFont('Helvetica', 9 )
        heighFont = 9 + 1;

        valorDocumento = self._formataValorParaExibir(
            boletoDados.valor_documento
        )

        self.pdfCanvas.drawString(
            self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.space,
            boletoDados.format_nosso_numero()
        )
        self.pdfCanvas.drawString(
            self.widthCanhoto - (35*mm) + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.space,
            boletoDados.data_vencimento.strftime('%d/%m/%Y')
        )
        self.pdfCanvas.drawString(
            self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.space,
            boletoDados.agencia_conta
        )
        self.pdfCanvas.drawString(
            self.widthCanhoto - (35*mm) + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.space,
            valorDocumento
        )

        demonstrativo = boletoDados.demonstrativo[0:12]
        for i in range(len(demonstrativo)):
            parts = utils.simpleSplit(demonstrativo[i], 'Helvetica', 9,
                                      self.widthCanhoto)
            self.pdfCanvas.drawString(
                2*self.space,
                (((linhaInicial - 1)*self.heightLine)) - (i * heighFont),
                parts[0]
            )

        self.pdfCanvas.restoreState();

        return ( self.widthCanhoto/mm,
            ((linhaInicial+2)*self.heightLine)/mm )

    def drawReciboSacado(self, boletoDados, x, y ):
        self.pdfCanvas.saveState();
        self.pdfCanvas.translate( x*mm, y*mm );

        linhaInicial = 16

        # Horizontal Lines
        self.pdfCanvas.setLineWidth(1)
        self.__horizontalLine( 0,
            linhaInicial * self.heightLine, self.width )
        self.__horizontalLine( 0,
            (linhaInicial + 1) * self.heightLine, self.width )

        self.pdfCanvas.setLineWidth(2)
        self.__horizontalLine( 0,
            (linhaInicial + 2) * self.heightLine, self.width )

        # Vertical Lines
        self.pdfCanvas.setLineWidth(1)
        self.__verticalLine(
            self.width - (35*mm),
            (linhaInicial + 0) * self.heightLine,
            2 * self.heightLine
        )
        self.__verticalLine(
            self.width - (35*mm) - (30*mm),
            (linhaInicial + 0) * self.heightLine,
            2 * self.heightLine
        )
        self.__verticalLine(
            self.width - (35*mm) - (30*mm) - (40*mm),
            (linhaInicial + 0) * self.heightLine,
            2 * self.heightLine
        )

        # Head
        self.pdfCanvas.setLineWidth(2)
        self.__verticalLine( 40*mm,
            (linhaInicial + 2) * self.heightLine, self.heightLine )
        self.__verticalLine( 60*mm,
            (linhaInicial + 2) * self.heightLine, self.heightLine )

        if boletoDados.logo_image_path:
            self.pdfCanvas.drawImage(
                boletoDados.logo_image_path,
                0, (linhaInicial + 2) * self.heightLine + 3,
                40*mm,
                self.heightLine,
                preserveAspectRatio=True,
                anchor='sw'
            )
        self.pdfCanvas.setFont( 'Helvetica-Bold', 18 )
        self.pdfCanvas.drawCentredString(
            50*mm,
            (linhaInicial + 2) * self.heightLine + 3,
            boletoDados.codigo_dv_banco
        )
        self.pdfCanvas.setFont( 'Helvetica-Bold', 10 )
        self.pdfCanvas.drawRightString(
            self.width,
            (linhaInicial + 2) * self.heightLine + 3,
            'Recibo do Sacado'
        )

        # Titles
        self.pdfCanvas.setFont('Helvetica', 6 )
        self.deltaTitle = self.heightLine - (6 + 1)

        self.pdfCanvas.drawRightString(
            self.width,
            self.heightLine,
            'Autenticação Mecânica'
        )

        self.pdfCanvas.drawString(
            0,
            (((linhaInicial + 1)*self.heightLine)) + self.deltaTitle,
            'Cedente'
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) - (30*mm) - (40*mm) + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.deltaTitle,
            'Agência/Código Cedente'
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) - (30*mm) + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.deltaTitle,
            'Data Documento'
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.deltaTitle,
            'Vencimento'
        )

        self.pdfCanvas.drawString(
            0,
            (((linhaInicial + 0)*self.heightLine)) + self.deltaTitle,
            'Sacado'
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) - (30*mm) - (40*mm) + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.deltaTitle,
            'Nosso Número'
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) - (30*mm) + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.deltaTitle,
            'N. do documento'
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.deltaTitle,
            'Valor Documento'
        )

        self.pdfCanvas.drawString(
            0,
            (((linhaInicial - 1)*self.heightLine)) + self.deltaTitle,
            'Demonstrativo'
        )

        # Values
        self.pdfCanvas.setFont('Helvetica', 9 )
        heighFont = 9 + 1;

        self.pdfCanvas.drawString(
            0 + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.space,
            boletoDados.cedente
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) - (30*mm) - (40*mm) + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.space,
            boletoDados.agencia_conta
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) - (30*mm) + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.space,
            boletoDados.data_documento.strftime('%d/%m/%Y')
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) + self.space,
            (((linhaInicial + 1)*self.heightLine)) + self.space,
            boletoDados.data_vencimento.strftime('%d/%m/%Y')
        )

        valorDocumento = self._formataValorParaExibir(
            boletoDados.valor_documento
        )

        self.pdfCanvas.drawString(
            0 + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.space,
            boletoDados.sacado[0]
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) - (30*mm) - (40*mm) + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.space,
            boletoDados.format_nosso_numero()
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) - (30*mm) + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.space,
            boletoDados.numero_documento
        )
        self.pdfCanvas.drawString(
            self.width - (35*mm) + self.space,
            (((linhaInicial + 0)*self.heightLine)) + self.space,
            valorDocumento
        )

        demonstrativo = boletoDados.demonstrativo[0:25]
        for i in range(len(demonstrativo)):
            self.pdfCanvas.drawString(
                2*self.space,
                (((linhaInicial - 1)*self.heightLine)) - (i * heighFont),
                demonstrativo[i]
            )

        self.pdfCanvas.restoreState();

        return (self.width/mm, ((linhaInicial+2)*self.heightLine)/mm);

    def drawHorizontalCorteLine(self, x, y, width ):
        self.pdfCanvas.saveState();
        self.pdfCanvas.translate( x*mm, y*mm );

        self.pdfCanvas.setLineWidth(1)
        self.pdfCanvas.setDash(1,2)
        self.__horizontalLine(0, 0, width*mm)

        self.pdfCanvas.restoreState();

    def drawVerticalCorteLine(self, x, y, height ):
        self.pdfCanvas.saveState();
        self.pdfCanvas.translate( x*mm, y*mm );

        self.pdfCanvas.setLineWidth(1)
        self.pdfCanvas.setDash(1,2)
        self.__verticalLine(0, 0, height*mm)

        self.pdfCanvas.restoreState();

    def drawReciboCaixa(self, boletoDados, x, y ):
        self.pdfCanvas.saveState();

        self.pdfCanvas.translate( x*mm, y*mm );

        # De baixo para cima posicao 0,0 esta no canto inferior esquerdo
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle )

        y = 1.5*self.heightLine;
        self.pdfCanvas.drawRightString(
            self.width,
            (1.5*self.heightLine)+self.deltaTitle-1,
            'Autenticação Mecânica / Ficha de Compensação'
        )


        # Primeira linha depois do codigo de barra
        y += self.heightLine;
        self.pdfCanvas.setLineWidth(2)
        self.__horizontalLine( 0, y, self.width )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y+self.space, 'Código de baixa'
        )
        self.pdfCanvas.drawString(0, y + self.space, 'Sacador / Avalista' )

        y += self.heightLine
        self.pdfCanvas.drawString(0, y + self.deltaTitle, 'Sacado' )
        sacado = boletoDados.sacado


        # Linha grossa dividindo o Sacado
        y += self.heightLine
        self.pdfCanvas.setLineWidth(2)
        self.__horizontalLine( 0, y, self.width )
        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue )
        for i in range(len(sacado)):
            self.pdfCanvas.drawString(
                15*mm,
                (y - 10) - (i * self.deltaFont),
                sacado[i]
            )
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle )


        # Linha vertical limitando todos os campos da direita
        self.pdfCanvas.setLineWidth(1)
        self.__verticalLine( self.width - (45*mm), y, 9 * self.heightLine )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            '(=) Valor cobrado'
        )


        # Campos da direita
        y += self.heightLine
        self.__horizontalLine( self.width - (45*mm), y, 45*mm )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            '(+) Outros acréscimos'
        )

        y += self.heightLine
        self.__horizontalLine( self.width - (45*mm), y, 45*mm )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            '(+) Mora/Multa'
        )

        y += self.heightLine
        self.__horizontalLine( self.width - (45*mm), y, 45*mm )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            '(-) Outras deduções'
        )

        y += self.heightLine
        self.__horizontalLine( self.width - (45*mm), y, 45*mm )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            '(-) Descontos/Abatimentos'
        )
        self.pdfCanvas.drawString(
            0,
            y + self.deltaTitle,
            'Instruções'
        )

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue )
        instrucoes = boletoDados.instrucoes[:7]
        for i in range(len(instrucoes)):
            parts = utils.simpleSplit(instrucoes[i], 'Helvetica', 9,
                                      self.width - 45*mm )
            self.pdfCanvas.drawString(
                2*self.space,
                y - (i * self.deltaFont),
                parts[0]
            )
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle )


        # Linha horizontal com primeiro campo Uso do Banco
        y += self.heightLine
        self.__horizontalLine( 0, y, self.width )
        self.pdfCanvas.drawString(0, y + self.deltaTitle, 'Uso do banco' )

        self.__verticalLine((30)*mm, y, 2*self.heightLine)
        self.pdfCanvas.drawString(
            (30*mm)+self.space,
            y + self.deltaTitle,
            'Carteira'
        )

        self.__verticalLine((30+20)*mm, y, self.heightLine)
        self.pdfCanvas.drawString(
            ((30+20)*mm)+self.space,
            y + self.deltaTitle,
            'Espécie'
        )

        self.__verticalLine(
            (30+20+20)*mm,
            y,
            2*self.heightLine
        )
        self.pdfCanvas.drawString(
            ((30+40)*mm)+self.space,
            y + self.deltaTitle,
            'Quantidade'
        )

        self.__verticalLine(
            (30+20+20+20+20)*mm, y, 2*self.heightLine)
        self.pdfCanvas.drawString(
            ((30+40+40)*mm)+self.space, y + self.deltaTitle, 'Valor' )

        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            '(=) Valor documento'
        )

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue )
        self.pdfCanvas.drawString(
            (30*mm)+self.space,
            y + self.space,
            boletoDados.carteira
        )
        self.pdfCanvas.drawString(
            ((30+20)*mm)+self.space,
            y + self.space,
            boletoDados.especie
        )
        self.pdfCanvas.drawString(
            ((30+20+20)*mm)+self.space,
            y + self.space,
            boletoDados.quantidade
        )
        valor = self._formataValorParaExibir(boletoDados.valor)
        self.pdfCanvas.drawString(
            ((30+20+20+20+20)*mm)+self.space,
            y + self.space,
            valor
        )
        valorDocumento = self._formataValorParaExibir(
            boletoDados.valor_documento
        )
        self.pdfCanvas.drawRightString(
            self.width - 2*self.space,
            y + self.space,
            valorDocumento
        )
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle )


        # Linha horizontal com primeiro campo Data documento
        y += self.heightLine
        self.__horizontalLine( 0, y, self.width )
        self.pdfCanvas.drawString(
            0,
            y + self.deltaTitle,
            'Data do documento'
        )
        self.pdfCanvas.drawString(
            (30*mm)+self.space,
            y + self.deltaTitle,
            'N. do documento'
        )
        self.pdfCanvas.drawString(
            ((30+40)*mm)+self.space,
            y + self.deltaTitle,
            'Espécie doc'
        )
        self.__verticalLine(
            (30+20+20+20)*mm,
            y,
            self.heightLine
        )
        self.pdfCanvas.drawString(
            ((30+40+20)*mm)+self.space,
            y + self.deltaTitle,
            'Aceite'
        )
        self.pdfCanvas.drawString(
            ((30+40+40)*mm)+self.space,
            y + self.deltaTitle,
            'Data processamento'
        )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            'Nosso número'
        )

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue )
        self.pdfCanvas.drawString(
            0,
            y + self.space,
            boletoDados.data_documento.strftime('%d/%m/%Y')
        )
        self.pdfCanvas.drawString(
            (30*mm)+self.space,
            y + self.space,
            boletoDados.numero_documento
        )
        self.pdfCanvas.drawString(
            ((30+40)*mm)+self.space,
            y + self.space,
            boletoDados.especie_documento
        )
        self.pdfCanvas.drawString(
            ((30+40+20)*mm)+self.space,
            y + self.space,
            boletoDados.aceite
        )
        self.pdfCanvas.drawString(
            ((30+40+40)*mm)+self.space,
            y + self.space,
            boletoDados.data_processamento.strftime('%d/%m/%Y')
        )
        self.pdfCanvas.drawRightString(
            self.width - 2*self.space,
            y + self.space,
            boletoDados.format_nosso_numero()
        )
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle )


        # Linha horizontal com primeiro campo Cedente
        y += self.heightLine
        self.__horizontalLine( 0, y, self.width )
        self.pdfCanvas.drawString(0, y + self.deltaTitle, 'Cedente' )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            'Agência/Código cedente'
        )

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue )
        self.pdfCanvas.drawString(0, y + self.space, boletoDados.cedente )
        self.pdfCanvas.drawRightString(
            self.width - 2*self.space,
            y + self.space,
            boletoDados.agencia_conta
        )
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle )


        # Linha horizontal com primeiro campo Local de Pagamento
        y += self.heightLine
        self.__horizontalLine( 0, y, self.width )
        self.pdfCanvas.drawString(
            0,
            y + self.deltaTitle,
            'Local de pagamento'
        )
        self.pdfCanvas.drawString(
            self.width - (45*mm) + self.space,
            y + self.deltaTitle,
            'Vencimento'
        )

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue )
        self.pdfCanvas.drawString(
            0,
            y + self.space,
            boletoDados.local_pagamento
        )
        self.pdfCanvas.drawRightString(
            self.width - 2*self.space,
            y + self.space,
            boletoDados.data_vencimento.strftime('%d/%m/%Y')
        )
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle )


        # Linha grossa com primeiro campo logo tipo do banco
        self.pdfCanvas.setLineWidth(3)
        y += self.heightLine
        self.__horizontalLine( 0, y, self.width )
        self.pdfCanvas.setLineWidth(2)
        self.__verticalLine(40*mm, y, self.heightLine) # Logo Tipo
        self.__verticalLine(60*mm, y, self.heightLine) # Numero do Banco

        if boletoDados.logo_image_path:
            self.pdfCanvas.drawImage(
                boletoDados.logo_image_path,
                0,
                y + self.space + 1,
                40*mm,
                self.heightLine,
                preserveAspectRatio=True,
                anchor='sw'
            )
        self.pdfCanvas.setFont('Helvetica-Bold', 18 )
        self.pdfCanvas.drawCentredString(
            50*mm,
            y + 2*self.space,
            boletoDados.codigo_dv_banco
        )
        self.pdfCanvas.setFont('Helvetica-Bold', 10 )
        self.pdfCanvas.drawRightString(
            self.width,
            y + 2*self.space,
            boletoDados.linha_digitavel
        )


        # Codigo de barras
        self._codigoBarraI25(boletoDados.barcode, 2*self.space, 0)


        self.pdfCanvas.restoreState();

        return (self.width, (y+self.heightLine)/mm )

    def drawBoletoCarneDuplo(self, boletoDados1, boletoDados2 ):
        y = 5
        d = self.drawBoletoCarne(boletoDados1, y)
        y += d[1] + 6
        #self.drawHorizontalCorteLine(0, y, d[0])
        y += 7
        if( boletoDados2):
            self.drawBoletoCarne(boletoDados2, y)

    def drawBoletoCarne(self, boletoDados, y ):
        x = 15
        d = self.drawReciboSacadoCanhoto(boletoDados, x, y)
        x += d[0] + 8
        self.drawVerticalCorteLine(x, y, d[1])
        x += 8
        d = self.drawReciboCaixa(boletoDados, x, y)
        x += d[0]
        return (x,d[1])

    def drawBoleto(self, boletoDados ):
        x = 10
        y = 40
        self.drawHorizontalCorteLine(x, y, self.width/mm)
        y += 5
        d = self.drawReciboCaixa(boletoDados, x, y)
        y += d[1] + 10
        self.drawHorizontalCorteLine(x, y, self.width/mm)
        y += 10
        d = self.drawReciboSacado(boletoDados, x, y)
        return (self.width,y)

    def nextPage(self):
        self.pdfCanvas.showPage()

    def save(self):
        self.pdfCanvas.save()

    def add_data(self, data):
        self.boletos.append(data)

    def render(self):
        if self.format == self.FORMAT_BOLETO:
            for b in self.boletos:
                self.drawBoleto(b)
                self.nextPage()
        elif self.format == self.FORMAT_CARNE:
            for i in range(0, len(self.boletos), 2):
                args = [self.boletos[i], None]
                if i+1 < len(self.boletos):
                    args[1] = self.boletos[i+1]
                self.drawBoletoCarneDuplo(*args)
                self.nextPage()


    #
    #   Private API
    #

    def __horizontalLine( self, x, y, width ):
        self.pdfCanvas.line( x, y, x+width, y )

    def __verticalLine( self, x, y, width ):
        self.pdfCanvas.line( x, y, x, y+width )

    def __centreText(self, x, y, text ):
        self.pdfCanvas.drawCentredString( self.refX+x, self.refY+y, text )

    def __rightText(self, x, y, text ):
        self.pdfCanvas.drawRightString( self.refX+x, self.refY+y, text )

    def _formataValorParaExibir(self, nfloat):
        if nfloat:
            txt = nfloat
            txt = txt.replace( '.', ',' )
        else:
            txt = ""
        return txt

    def _codigoBarraI25(self, num, x, y ):
        # http://en.wikipedia.org/wiki/Interleaved_2_of_5

        altura  = 13 * mm
        comprimento = 103 * mm

        tracoFino = 0.254320987654 * mm #Tamanho correto aproximado

        bc = I2of5(num,
            barWidth = tracoFino,
            ratio = 3,
            barHeight = altura,
            bearers = 0,
            quiet = 0,
            checksum = 0
        )

        # Recalcula o tamanho do tracoFino para que o cod de barras tenha o
        # comprimento correto
        tracoFino = (tracoFino * comprimento)/bc.width
        bc.__init__(num,
            barWidth = tracoFino
        )

        bc.drawOn(self.pdfCanvas, x, y)

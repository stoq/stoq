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

""" Stoqlib Reporting é um pacote criado para facilitar a construção de 
relatórios com o ReportLab. O maior destaque do pacote está em suas rotinas 
para geração de tabelas, que fornecem suporte para criação do mais simples 
tipo de tabela, onde dispomos informações alinhadas, até tabelas objeto, que 
permitem a criação de relatórios tendo somente uma lista de instâncias (que 
pode ser obtida através de, por exemplo, uma pesquisa em uma base de dados). 

"""

import os
import tempfile

__name__ = "Stoqlib Reporting"
__version__ = "0.1"
__author__ = "Async Open Source"
__email__ = "async@async.com.br"
__license__ = "GNU LGPL 2.1"

# Editores padrões à serem utilizados para visualização de documentos
PROGRAMS = [('gv', '-media', 'automatic'), 'xpdf', 'ggv']

def build_report(report_class, *args):
    """ Função responsável pela construção do relatório.
    Parâmetros:

        - report_class: a classe utilizada para a construção do relatório,
          isto é, a classe criada pelo usuário (uma subclasse de
          ReportTemplate) que define os elementos à serem inseridos no 
          relatório e como eles podem ser construídos.
        - args: argumentos extras que podem ser passados à classe 
          especificada no parâmetro report_class.
    """
    filename = tempfile.mktemp()
    report = report_class(filename, *args)
    report.save()
    return filename

def print_file(filename, printer=None, extra_opts=[]):
    """ Função utilizada para impressão de arquivos. Geralmente utilizada para
    impressão do arquivo criado por uma chamada prévia à função build_report.
    Parâmetros:

        - filename: o nome do arquivo a ser impresso.
        - printer: nome da impressora à ser utilizada; se não especificado, a
          impressora padrão será utilizada.
        - extra_opts: parâmetros *opcionais* que precisam ser passados ao 
          comando de impressão do documento.
    """
    if not os.path.exists(filename):
        raise ValueError, "File %s not found" % filename
    options = " ".join(extra_opts)
    if printer:
        options += " -P%s" % printer
    ret = os.system("lpr %s %s" % (options, filename))
    os.remove(filename)
    return ret

def print_preview(filename, keep_file=0):
    """ Função utilizada para visualização de arquivos pdf e ps, geralmente
    criados por build_report. Alguns editores (e suas devidas opções) estão
    definidos na variável PROGRAMS; o primeiro editor encontrado no sistema
    será utilizado. Parametros:

        - filename: o nome do arquivo à visualizar.
        - keep_file: TRUE, caso o arquivo deva ser salvo no disco após sua
          visualização.
    """
    if not os.path.exists(filename):
        raise OSError, "the file does not exist"

    path = os.environ['PATH'].split(':')

    for program in PROGRAMS:
        args = []
        if isinstance(program, tuple):
            # grab args and program from tuple
            args.extend(program[1:])
            program = program[0]
        elif not isinstance(program, str):
            raise AssertionError
        args.append(filename)
        for part in path:
            full = os.path.join(part, program)
            if not os.access(full, os.R_OK|os.X_OK):
                continue
            if not os.fork():
                args = " ".join(args)
                os.system("%s %s" % (full, args))
                if not keep_file:
                    os.remove(filename)
                # See http://www.gtk.org/faq/#AEN505 -- _exit()
                # keeps file descriptors open, which avoids X async
                # errors after we close the child window.
                os._exit(-1)
            return
    print "Could not find a pdf viewer, aborting"


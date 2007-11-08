# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Johan Dahlin    <jdahlin@async.com.br>
##

# This module implements the ABICOMP codec for python

TABLE = {
    u'À': '\xa1',
    u'Á': '\xa2',
    u'Â': '\xa3',
    u'Ã': '\xa4',
    u'Ä': '\xa5',
    u'Ç': '\xa6',
    u'È': '\xa7',
    u'É': '\xa8',
    u'Ê': '\xa9',
    u'Ë': '\xaa',
    u'Ì': '\xab',
    u'Í': '\xac',
    u'Î': '\xad',
    u'Ï': '\xae',
    u'Ñ': '\xaf',

    u'Ò': '\xb0',
    u'Ó': '\xb1',
    u'Ô': '\xb2',
    u'Õ': '\xb3',
    u'Ö': '\xb4',
    u'Œ': '\xb5',
    u'Ù': '\xb6',
    u'Ú': '\xb7',
    u'Û': '\xb8',
    u'Ü': '\xb9',
    u'Ÿ': '\xba',
    u'˝': '\xbb',
    u'£': '\xbc',
    u'ʻ': '\xbd',
    u'°': '\xbe',

    u'¡': '\xc0',
    u'à': '\xc1',
    u'á': '\xc2',
    u'â': '\xc3',
    u'ã': '\xc4',
    u'ä': '\xc5',
    u'ç': '\xc6',
    u'è': '\xc7',
    u'é': '\xc8',
    u'ê': '\xc9',
    u'ë': '\xca',
    u'ì': '\xcb',
    u'í': '\xcc',
    u'î': '\xcd',
    u'ï': '\xce',
    u'ñ': '\xcf',

    u'ò': '\xd0',
    u'ó': '\xd1',
    u'ô': '\xd2',
    u'õ': '\xd3',
    u'ö': '\xd4',
    u'œ': '\xd5',
    u'ù': '\xd6',
    u'ú': '\xd7',
    u'û': '\xd8',
    u'ü': '\xd9',
    u'ÿ': '\xda',
    u'ß': '\xdb',
    u'ª': '\xdc',
    u'º': '\xdd',
    u'¿': '\xde',
    u'±': '\xdf',
}
RTABLE = dict([(v, k) for k, v in TABLE.items()])

def encode(input):
    """
    Convert unicode to string.
    @param input: text to encode
    @type input: unicode
    @returns: encoded text
    @rtype: str
    """
    return [TABLE.get(c) or str(c) for c in input]

def decode(input):
    """
    Convert string in unicode.
    @param input: text to decode
    @type input: str
    @returns: decoded text
    @rtype: unicode
    """
    return [RTABLE.get(c) or unicode(c) for c in input]

def register_codec():
    import codecs

    class Codec(codecs.Codec):
        def encode(self, input, errors='strict'):
            if not input:
                return "", 0
            output = encode(input)
            return "".join(output), len(output)

        def decode(self, input, errors='strict'):
            if not input:
                return u"", 0
            output = decode(input)
            return u"".join(output), len(output)

    class StreamWriter(Codec, codecs.StreamWriter):
        pass

    class StreamReader(Codec, codecs.StreamReader):
        pass

    def getregentry(encoding):
        if encoding != 'abicomp':
            return None
        return (Codec().encode,
                Codec().decode,
                StreamReader,
                StreamWriter)

    codecs.register(getregentry)

def test():
    register_codec()
    all = u''.join(TABLE.keys())
    assert all == unicode(all.encode('abicomp'), 'abicomp')

    mixed = u'não dîz'
    assert mixed == unicode(mixed.encode('abicomp'), 'abicomp')

if __name__ == '__main__':
    test()

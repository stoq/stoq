# encoding: utf-8
# This module implements the ABICOMP codec for python

import codecs

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

### Codec APIs

class Codec(codecs.Codec):
    def encode(self, input, errors='strict'):
        if not input:
            return "", 0
        output = []
        for c in input:
            if c in TABLE:
                c = TABLE[c]
            else:
                c = str(c)
            output.append(c)
        return "".join(output), len(output)

    def decode(self, input, errors='strict'):
        if not input:
            return u"", 0
        output = []
        for c in input:
            if c in RTABLE:
                c = RTABLE[c]
            else:
                c = unicode(c)
            output.append(c)
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
    all = u''.join(TABLE.keys())
    assert all == unicode(all.encode('abicomp'), 'abicomp')

if __name__ == '__main__':
    test()

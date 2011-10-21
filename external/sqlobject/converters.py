import array

try:
    import mx.DateTime.ISO
    origISOStr = mx.DateTime.ISO.strGMT
    from mx.DateTime import DateTimeType, DateTimeDeltaType
except ImportError:
    try:
        import DateTime.ISO
        origISOStr = DateTime.ISO.strGMT
        from DateTime import DateTimeType, DateTimeDeltaType
    except ImportError:
        origISOStr = None
        DateTimeType = None
        DateTimeDeltaType = None

import time
try:
    import datetime
except ImportError:
    datetime = None

try:
    import Sybase
    NumericType=Sybase.NumericType
except ImportError:
    NumericType = None

if type(1==1) == type(1):
    class BOOL(object):
        def __init__(self, value):
            self.value = not not value
        def __nonzero__(self):
            return self.value
        def __repr__(self):
            if self:
                return 'TRUE'
            else:
                return 'FALSE'
    TRUE = BOOL(1)
    FALSE = BOOL(0)
else:
    TRUE = 1==1
    FALSE = 0==1

from types import InstanceType, ClassType, TypeType

try:
    from decimal import Decimal
except ImportError:
    Decimal = None

########################################
## Quoting
########################################

# FIXME: This sould be left to the library to escape.
sqlStringReplace = [
    ('\\', '\\\\'),
    ("'", "''"),
    ('\000', '\\0'),
    ('\b', '\\b'),
    ('\n', '\\n'),
    ('\r', '\\r'),
    ('\t', '\\t'),
    ]

def isoStr(val):
    """
    Gets rid of time zone information
    (@@: should we convert to GMT?)
    """
    val = origISOStr(val)
    if val.find('+') == -1:
        return val
    else:
        return val[:val.find('+')]

class ConverterRegistry:

    def __init__(self):
        self.basic = {}
        self.klass = {}

    def registerConverter(self, typ, func):
        if type(typ) is ClassType:
            self.klass[typ] = func
        else:
            self.basic[typ] = func

    def lookupConverter(self, value, default=None):
        if type(value) == InstanceType:
            # lookup on klasses dict
            return self.klass.get(value.__class__, default)
        return self.basic.get(type(value), default)

converters = ConverterRegistry()
registerConverter = converters.registerConverter
lookupConverter = converters.lookupConverter

array_type = type(array.array('c', '')) # In Python 2.2 array.array and buffer
buffer_type = type(buffer('')) # are functions, not classes

def StringLikeConverter(value, db):
    if isinstance(value, array_type):
        try:
            value = value.tounicode()
        except ValueError:
            value = value.tostring()
    elif isinstance(value, buffer_type):
        value = str(value)

    if db in ('mysql', 'postgres'):
        for orig, repl in sqlStringReplace:
            value = value.replace(orig, repl)
    elif db in ('sqlite', 'firebird', 'sybase', 'maxdb', 'mssql'):
        value = value.replace("'", "''")
    else:
        assert 0, "Database %s unknown" % db
    return "'%s'" % value

registerConverter(type(""), StringLikeConverter)
registerConverter(type(u""), StringLikeConverter)
registerConverter(array_type, StringLikeConverter)
registerConverter(buffer_type, StringLikeConverter)

def IntConverter(value, db):
    return repr(int(value))

registerConverter(type(1), IntConverter)

def LongConverter(value, db):
    return str(value)

registerConverter(type(0L), LongConverter)

if NumericType:
    registerConverter(NumericType, IntConverter)

def BoolConverter(value, db):
    if db in ('postgres',):
        if value:
            return "'t'"
        else:
            return "'f'"
    else:
        if value:
            return '1'
        else:
            return '0'

if type(TRUE) == InstanceType:
    # Python 2.2 compatibility:
    registerConverter(BOOL, BoolConverter)
else:
    registerConverter(type(TRUE), BoolConverter)

def FloatConverter(value, db):
    return repr(value)

registerConverter(type(1.0), FloatConverter)

if DateTimeType:
    def DateTimeConverter(value, db):
        return "'%s'" % isoStr(value)

    registerConverter(DateTimeType, DateTimeConverter)

    def TimeConverter(value, db):
        return "'%s'" % value.strftime("%T")

    registerConverter(DateTimeDeltaType, TimeConverter)

def NoneConverter(value, db):
    return "NULL"

registerConverter(type(None), NoneConverter)

def SequenceConverter(value, db):
    return "(%s)" % ", ".join([sqlrepr(v, db) for v in value])

registerConverter(type(()), SequenceConverter)
registerConverter(type([]), SequenceConverter)

if hasattr(time, 'struct_time'):
    def StructTimeConverter(value, db):
        return time.strftime("'%Y-%m-%d %H:%M:%S'", value)

    registerConverter(time.struct_time, StructTimeConverter)

if datetime:
    def DateTimeConverter(value, db):
        if db ==  "sqlite":
            return "'%4d-%02d-%02d'" % (
                value.year, value.month, value.day)
            return "'%4d-%02d-%02d %02d:%02d:%02d'" % (
                value.year, value.month, value.day,
                value.hour, value.minute, value.second)
        else:
            return "'%s'" % value.isoformat('T')

    registerConverter(datetime.datetime, DateTimeConverter)

    def DateConverter(value, db):
        return "'%4d-%02d-%02d'" % (value.year, value.month, value.day)

    registerConverter(datetime.date, DateConverter)

    def TimeConverter(value, db):
        return "'%02d:%02d:%02d'" % (value.hour, value.minute, value.second)

    registerConverter(datetime.time, TimeConverter)

if Decimal:
    def DecimalConverter(value, db):
        return value.to_eng_string()

    registerConverter(Decimal, DecimalConverter)

def sqlrepr(obj, db=None):
    try:
        reprFunc = obj.__sqlrepr__
    except AttributeError:
        converter = lookupConverter(obj)
        if converter is None:
            raise ValueError, "Unknown SQL builtin type: %s for %s" % \
                  (type(obj), repr(obj))
        return converter(obj, db)
    else:
        return reprFunc(db)

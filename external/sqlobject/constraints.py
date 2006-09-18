"""
Constraints
"""

True, False = (1==1), (0==1)

class BadValue(ValueError):

    def __init__(self, desc, obj, col, value, *args):
        self.desc = desc
        self.col = col

        # I want these objects to be garbage-collectable, so
        # I just keep their repr:
        self.obj = repr(obj)
        self.value = repr(value)
        fullDesc = "%s.%s %s (you gave: %s)" \
                   % (obj, col.name, desc, value)
        ValueError.__init__(self, fullDesc, *args)

def isString(obj, col, value):
    if type(value) is not type(""):
        raise BadValue("only allows strings", obj, col, value)

def notNull(obj, col, value):
    if value is None:
        raise BadValue("is defined NOT NULL", obj, col, value)

def isInt(obj, col, value):
    if type(value) not in (type(1), type(1L)):
        raise BadValue("only allows integers", obj, col, value)

def isFloat(obj, col, value):
    if type(value) not in (type(1), type(1L), type(1.1)):
        raise BadValue("only allows floating point numbers", obj, col, value)

def isBool(obj, col, value):
    if type(value) not in (type(True),):
        raise BadValue("only allows booleans", obj, col, value)

class InList:

    def __init__(self, l):
        self.list = l

    def __call__(self, obj, col, value):
        if value not in self.list:
            raise BadValue("accepts only values in %s" % repr(self.list),
                           obj, col, value)

class MaxLength:

    def __init__(self, length):
        self.length = length

    def __call__(self, obj, col, value):
        try:
            length = len(value)
        except TypeError:
            raise BadValue("object does not have a length",
                           obj, col, value)
        if length > self.length:
            raise BadValue("must be shorter in length than %s"
                           % self.length,
                           obj, col, value)

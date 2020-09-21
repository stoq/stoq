class ClassInittableMetaType(type):
    def __init__(self, name, bases, namespace):
        type.__init__(self, name, bases, namespace)
        self.__class_init__(namespace)


class ClassInittableObject(metaclass=ClassInittableMetaType):
    """
    I am an object which will call a classmethod called
    __class_init__ when I am created.
    Subclasses of me will also have __class_init__ called.
    Note that __class_init__ is called when the class is created,
    eg when the file is imported at the first time.
    It's called after the class is created, but before it is put
    in the namespace of the module where it is defined.
    """

    @classmethod
    def __class_init__(cls, namespace):
        """
        Called when the class is created
        :param cls:       class
        :param namespace: namespace for newly created
        :type  namespace: dict
        """


class Settable:
    """
    A mixin class for syntactic sugar.  Lets you assign attributes by
    calling with keyword arguments; for example, C{x(a=b,c=d,y=z)} is the
    same as C{x.a=b;x.c=d;x.y=z}.  The most useful place for this is
    where you don't want to name a variable, but you do want to set
    some attributes; for example, C{X()(y=z,a=b)}.
    """
    def __init__(self, **kw):
        self._attrs = sorted(kw.keys())
        for k, v in kw.items():
            setattr(self, k, v)

    def getattributes(self):
        """
        Fetches the attributes used to create this object
        :returns: a dictionary with attributes
        """
        return self._attrs

    def __repr__(self):
        attrs = ', '.join(['%s=%r' % (attr, getattr(self, attr)) for attr in self._attrs])
        return '<%s %s>' % (self.__class__.__name__, attrs)


def cmp(a, b):
    """Compare function that behaves like cmp in python2."""
    return (a > b) - (a < b)


class enum(int, metaclass=ClassInittableMetaType):
    """
    enum is an enumered type implementation in python.
    To use it, define an enum subclass like this:

    >>> class Status(enum):
    ...     OPEN, CLOSE = range(2)
    >>> Status.OPEN
    <Status value OPEN>

    All the integers defined in the class are assumed to be enums and
    values cannot be duplicated
    """

    @classmethod
    def __class_init__(cls, ns):
        cls.names = {}  # name -> enum
        cls.values = {}  # value -> enum

        for key, value in ns.items():
            if isinstance(value, int):
                cls(value, key)

    @classmethod
    def get(cls, value):
        """
        Lookup an enum by value
        :param value: the value
        """
        if value not in cls.values:
            raise ValueError("There is no enum for value %d" % (value,))
        return cls.values[value]

    def __new__(cls, value, name):
        """
        Create a new Enum.
        :param value: value of the enum
        :param name: name of the enum
        """
        if value in cls.values:
            msg = "Error while creating enum %s of type %s, it has already been created as %s"
            raise ValueError(msg % (value, cls.__name__, cls.values[value]))

        self = super(enum, cls).__new__(cls, value)
        self.name = name

        cls.values[value] = self
        cls.names[name] = self
        setattr(cls, name, self)

        return self

    def __str__(self):
        return '<%s value %s>' % (self.__class__.__name__, self.name)
    __repr__ = __str__

## FormEncode, a  Form processor
## Copyright (C) 2003, Ian Bicking <ianb@colorstudy.com>
##
## This library is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public
## License as published by the Free Software Foundation; either
## version 2.1 of the License, or (at your option) any later version.
##
## This library is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public
## License along with this library; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##
## NOTE: In the context of the Python environment, I interpret "dynamic
## linking" as importing -- thus the LGPL applies to the contents of
## the modules, but make no requirements on code importing these
## modules.
"""
Validator/Converters for use with FormEncode.
"""

import re
import cgi
DateTime = None
mxlookup = None
httplib = None
urlparse = None
from interfaces import *
from api import *
from declarative import Declarative, DeclarativeMeta

True, False = (1==1), (0==1)

############################################################
## Wrapper Validators
############################################################

datetime_module = None
mxDateTime_module = None

def import_datetime(module_type):
    global datetime_module, mxDateTime_module
    if module_type is None:
        try:
            if datetime_module is None:
                import datetime as datetime_module
            return datetime_module
        except ImportError:
            if mxDateTime_module is None:
                from mx import DateTime as mxDateTime_module
            return mxDateTime_module

    module_type = module_type.lower()
    assert module_type in ('datetime', 'mxdatetime')
    if module_type == 'datetime':
        if datetime_module is None:
            import datetime as datetime_module
        return datetime_module
    else:
        if mxDateTime_module is None:
            from mx import DateTime as mxDateTime_module
        return mxDateTime_module

def datetime_now(module):
    if module.__name__ == 'datetime':
        return module.datetime.now()
    else:
        return module.now()

def datetime_makedate(module, year, month, day):
    if module.__name__ == 'datetime':
        return module.date(year, month, day)
    else:
        try:
            return module.DateTime(year, month, day)
        except module.RangeError, e:
            raise ValueError(str(e))

class ConfirmType(FancyValidator):

    """
    Confirms that the input/output is of the proper type, using:

    subclass:
        The class or a tuple of classes; the item must be an instance
        of the class or a subclass.
    type:
        A type or tuple of types (or classes); the item must be of
        the exact class or type.  Subclasses are not allowed.

    Examples::

        >>> cint = ConfirmType(subclass=int)
        >>> cint.to_python(True)
        True
        >>> cint.to_python('1')
        Traceback (most recent call last):
            ...
        Invalid: '1' is not a subclass of <type 'int'>
        >>> cintfloat = ConfirmType(subclass=(float, int))
        >>> cintfloat.to_python(1.0), cintfloat.from_python(1.0)
        (1.0, 1.0)
        >>> cintfloat.to_python(1), cintfloat.from_python(1)
        (1, 1)
        >>> cintfloat.to_python(None)
        Traceback (most recent call last):
            ...
        Invalid: None is not a subclass of one of the types <type 'float'>, <type 'int'>
        >>> cint2 = ConfirmType(type=int)
        >>> cint2.from_python(True)
        Traceback (most recent call last):
            ...
        Invalid: True must be of the type <type 'int'>
    """

    subclass = None
    type = None

    messages = {
        'subclass': "%(object)r is not a subclass of %(subclass)s",
        'inSubclass': "%(object)r is not a subclass of one of the types %(subclassList)s",
        'inType': "%(object)r must be one of the types %(typeList)s",
        'type': "%(object)r must be of the type %(type)s",
        }

    def __init__(self, *args, **kw):
        FancyValidator.__init__(self, *args, **kw)
        if self.subclass:
            if isinstance(self.subclass, list):
                self.subclass = tuple(self.subclass)
            elif not isinstance(self.subclass, tuple):
                self.subclass = (self.subclass,)
            self.validate_python = self.confirm_subclass
        if self.type:
            if isinstance(self.type, list):
                self.type = tuple(self.type)
            elif not isinstance(self.subclass, tuple):
                self.type = (self.type,)
            self.validate_python = self.confirm_type

    def confirm_subclass(self, value, state):
        if not isinstance(value, self.subclass):
            if len(self.subclass) == 1:
                msg = self.message('subclass', state, object=value,
                                   subclass=self.subclass[0])
            else:
                subclass_list = ', '.join(map(str, self.subclass))
                msg = self.message('inSubclass', state, object=value,
                                   subclassList=subclass_list)
            raise Invalid(msg, value, state)

    def confirm_type(self, value, state):
        for t in self.type:
            if type(value) is t:
                break
        else:
            if len(self.type) == 1:
                msg = self.message('type', state, object=value,
                                   type=self.type[0])
            else:
                msg = self.message('inType', state, object=value,
                                   typeList=', '.join(map(str, self.type)))
            raise Invalid(msg, value, state)
        return value

class Wrapper(FancyValidator):

    """
    Used to convert functions to validator/converters.  You can give a
    simple function for `to_python`, `from_python`, `validate_python` or
    `validate_other`.  If that function raises an exception, the value
    is considered invalid.  Whatever value the function returns is
    considered the converted value.

    Unlike validators, the `state` argument is not used.  Functions
    like `int` can be used here, that take a single argument.

    Examples::

        >>> def downcase(v):
        ...     return v.lower()
        >>> wrap = Wrapper(to_python=downcase)
        >>> wrap.to_python('This')
        'this'
        >>> wrap.from_python('This')
        'This'
        >>> wrap2 = Wrapper(from_python=downcase)
        >>> wrap2.from_python('This')
        'this'
        >>> wrap2.from_python(1)
        Traceback (most recent call last):
          ...
        Invalid: 'int' object has no attribute 'lower'
        >>> wrap3 = Wrapper(validate_python=int)
        >>> wrap3.to_python('1')
        '1'
        >>> wrap3.to_python('a')
        Traceback (most recent call last):
          ...
        Invalid: invalid literal for int(): a
    """

    func_to_python = None
    func_from_python = None
    func_validate_python = None
    func_validate_other = None

    def __init__(self, *args, **kw):
        for n in ['to_python', 'from_python', 'validate_python',
                  'validate_other']:
            if kw.has_key(n):
                kw['func_%s' % n] = kw[n]
                del kw[n]
        FancyValidator.__init__(self, *args, **kw)
        self._to_python = self.wrap(self.func_to_python)
        self._from_python = self.wrap(self.func_from_python)
        self.validate_python = self.wrap(self.func_validate_python)
        self.validate_other = self.wrap(self.func_validate_other)

    def wrap(self, func):
        if not func:
            return None
        def result(value, state, func=func):
            try:
                return func(value)
            except Exception, e:
                raise Invalid(str(e), {}, value, state)
        return result

class Constant(FancyValidator):

    """
    This converter converts everything to the same thing.  I.e., you
    pass in the constant value when initializing, then all values get
    converted to that constant value.

    This is only really useful for funny situations, like:
      fromEmailValidator = ValidateAny(
                               ValidEmailAddress(),
                               Constant('unknown@localhost'))
    In this case, the if the email is not valid 'unknown@localhost' will
    be used instead.  Of course, you could use if_invalid instead.

    Examples::

        >>> Constant('X').to_python('y')
        'X'
    """

    __unpackargs__ = ('value',)

    def _to_python(self, value, state):
        return self.value

    _from_python = _to_python

############################################################
## Normal validators
############################################################

class MaxLength(FancyValidator):

    """
    Invalid if the value is longer than `maxLength`.  Uses len(),
    so it can work for strings, lists, or anything with length.

    Examples::

        >>> max5 = MaxLength(5)
        >>> max5.to_python('12345')
        '12345'
        >>> max5.from_python('12345')
        '12345'
        >>> max5.to_python('123456')
        Traceback (most recent call last):
          ...
        Invalid: Enter a value less than 5 characters long
        >>> max5.from_python('123456')
        Traceback (most recent call last):
          ...
        Invalid: Enter a value less than 5 characters long
        >>> max5.to_python([1, 2, 3])
        [1, 2, 3]
        >>> max5.to_python([1, 2, 3, 4, 5, 6])
        Traceback (most recent call last):
          ...
        Invalid: Enter a value less than 5 characters long
        >>> max5.to_python(5)
        Traceback (most recent call last):
          ...
        Invalid: Invalid value (value with length expected)
    """

    __unpackargs__ = ('maxLength',)
    messages = {
        'tooLong': "Enter a value less than %(maxLength)i characters long",
        'invalid': "Invalid value (value with length expected)",
        }

    def validate_python(self, value, state):
        try:
            if value and \
               len(value) > self.maxLength:
                raise Invalid(self.message('tooLong', state,
                                           maxLength=self.maxLength),
                              value, state)
            else:
                return None
        except TypeError:
            raise Invalid(self.message('invalid', state),
                          value, state)

class MinLength(FancyValidator):

    """
    Invalid if the value is shorter than `minlength`.  Uses len(),
    so it can work for strings, lists, or anything with length.

    Examples::

        >>> min5 = MinLength(5)
        >>> min5.to_python('12345')
        '12345'
        >>> min5.from_python('12345')
        '12345'
        >>> min5.to_python('1234')
        Traceback (most recent call last):
          ...
        Invalid: Enter a value more than 5 characters long
        >>> min5.from_python('1234')
        Traceback (most recent call last):
          ...
        Invalid: Enter a value more than 5 characters long
        >>> min5.to_python([1, 2, 3, 4, 5])
        [1, 2, 3, 4, 5]
        >>> min5.to_python([1, 2, 3])
        Traceback (most recent call last):
          ...
        Invalid: Enter a value more than 5 characters long
        >>> min5.to_python(5)
        Traceback (most recent call last):
          ...
        Invalid: Invalid value (value with length expected)

    """

    __unpackargs__ = ('minLength',)

    messages = {
        'tooShort': "Enter a value more than %(minLength)i characters long",
        'invalid': "Invalid value (value with length expected)",
        }

    def validate_python(self, value, state):
        try:
            if len(value) < self.minLength:
                raise Invalid(self.message('tooShort', state,
                                           minLength=self.minLength),
                              value, state)
        except TypeError:
            raise Invalid(self.message('invalid', state),
                          value, state)

class NotEmpty(FancyValidator):

    """
    Invalid if value is empty (empty string, empty list, etc).  Generally
    for objects that Python considers false, except zero which is not
    considered invalid.

    Examples::

        >>> ne = NotEmpty(messages={'empty': 'enter something'})
        >>> ne.to_python('')
        Traceback (most recent call last):
          ...
        Invalid: enter something
        >>> ne.to_python(0)
        0
    """

    messages = {
        'empty': "Please enter a value",
        }

    def validate_python(self, value, state):
        if value == 0:
            # This isn't "empty" for this definition.
            return value
        if not value:
            raise Invalid(self.message('empty', state),
                          value, state)

class Empty(FancyValidator):

    """
    Invalid unless the value is empty.  Use cleverly, if at all.

    Examples::

        >>> Empty.to_python(0)
        Traceback (most recent call last):
          ...
        Invalid: You cannot enter a value here
    """

    messages = {
        'notEmpty': "You cannot enter a value here",
        }

    def validate_python(self, value, state):
        if value or value == 0:
            raise Invalid(self.message('notEmpty', state),
                          value, state)

class Regex(FancyValidator):

    """
    Invalid if the value doesn't match the regular expression `regex`.
    The regular expression can be a compiled re object, or a string
    which will be compiled for you.

    Use strip=True if you want to strip the value before validation,
    and as a form of conversion (often useful).

    Examples::

        >>> cap = Regex(r'^[A-Z]+$')
        >>> cap.to_python('ABC')
        'ABC'
        >>> cap.from_python('abc')
        Traceback (most recent call last):
          ...
        Invalid: The input is not valid
        >>> cap.to_python(1)
        Traceback (most recent call last):
          ...
        Invalid: The input must be a string (not a <type 'int'>: 1)
        >>> Regex(r'^[A-Z]+$', strip=True).to_python('  ABC  ')
        'ABC'
        >>> Regex(r'this', regexOps=('I',)).to_python('THIS')
        'THIS'
    """

    regexOps = ()
    strip = False
    regex = None

    __unpackargs__ = ('regex',)

    messages = {
        'invalid': "The input is not valid",
        }

    def __init__(self, *args, **kw):
        FancyValidator.__init__(self, *args, **kw)
        if isinstance(self.regex, str):
            ops = 0
            assert not isinstance(self.regexOps, str), (
                "regexOps should be a list of options from the re module "
                "(names, or actual values)")
            for op in self.regexOps:
                if isinstance(op, str):
                    ops |= getattr(re, op)
                else:
                    ops |= op
            self.regex = re.compile(self.regex, ops)

    def validate_python(self, value, state):
        self.assert_string(value, state)
        if self.strip and (isinstance(value, str) or isinstance(value, unicode)):
            value = value.strip()
        if not self.regex.search(value):
            raise Invalid(self.message('invalid', state),
                          value, state)

    def _to_python(self, value, state):
        if self.strip and \
               (isinstance(value, str) or isinstance(value, unicode)):
            return value.strip()
        return value

class PlainText(Regex):

    """
    Test that the field contains only letters, numbers, underscore,
    and the hyphen.  Subclasses Regex.

    Examples::

        >>> PlainText.to_python('_this9_')
        '_this9_'
        >>> PlainText.from_python('  this  ')
        Traceback (most recent call last):
          ...
        Invalid: Enter only letters, numbers, or _ (underscore)
        >>> PlainText(strip=True).to_python('  this  ')
        'this'
        >>> PlainText(strip=True).from_python('  this  ')
        '  this  '
    """

    regex = r"^[a-zA-Z_\-0-9]*$"

    messages = {
        'invalid': 'Enter only letters, numbers, or _ (underscore)',
        }

class OneOf(FancyValidator):

    """
    Tests that the value is one of the members of a given list.  If
    testValueLists=True, then if the input value is a list or tuple,
    all the members of the sequence will be checked (i.e., the input
    must be a subset of the allowed values).

    Use hideList=True to keep the list of valid values out of the
    error message in exceptions.

    Examples::

        >>> oneof = OneOf([1, 2, 3])
        >>> oneof.to_python(1)
        1
        >>> oneof.to_python(4)
        Traceback (most recent call last):
          ...
        Invalid: Value must be one of: 1; 2; 3 (not 4)
        >>> oneof(testValueList=True).to_python([2, 3, [1, 2, 3]])
        [2, 3, [1, 2, 3]]
        >>> oneof.to_python([2, 3, [1, 2, 3]])
        Traceback (most recent call last):
          ...
        Invalid: Value must be one of: 1; 2; 3 (not [2, 3, [1, 2, 3]])
    """

    list = None
    testValueList = False
    hideList = False

    __unpackargs__ = ('list',)

    messages = {
        'invalid': "Invalid value",
        'notIn': "Value must be one of: %(items)s (not %(value)r)",
        }

    def validate_python(self, value, state):
        if self.testValueList and isinstance(value, (list, tuple)):
            for v in value:
                self.validate_python(v, state)
        else:
            if not value in self.list:
                if self.hideList:
                    raise Invalid(self.message('invalid', state),
                                  value, state)
                else:
                    items = '; '.join(map(str, self.list))
                    raise Invalid(self.message('notIn', state,
                                               items=items,
                                               value=value),
                                  value, state)

class DictConverter(FancyValidator):

    """
    Converts values based on a dictionary which has values as keys for
    the resultant values.  If allowNull is passed, it will not balk if
    a false value (e.g., '' or None) is given (it will return None in
    these cases).

    to_python takes keys and gives values, from_python takes values and
    gives keys.

    If you give hideDict=True, then the contents of the dictionary
    will not show up in error messages.

    Examples::

        >>> dc = DictConverter({1: 'one', 2: 'two'})
        >>> dc.to_python(1)
        'one'
        >>> dc.from_python('one')
        1
        >>> dc.to_python(3)
        Traceback (most recent call last):
        Invalid: Enter a value from: 1; 2
        >>> dc2 = dc(hideDict=True)
        >>> dc2.hideDict
        True
        >>> dc2.dict
        {1: 'one', 2: 'two'}
        >>> dc2.to_python(3)
        Traceback (most recent call last):
        Invalid: Choose something
        >>> dc.from_python('three')
        Traceback (most recent call last):
        Invalid: Nothing in my dictionary goes by the value 'three'.  Choose one of: 'one'; 'two'
    """

    dict = None
    hideDict = False

    __unpackargs__ = ('dict',)

    messages = {
        'keyNotFound': "Choose something",
        'chooseKey': "Enter a value from: %(items)s",
        'valueNotFound': "That value is not known",
        'chooseValue': "Nothing in my dictionary goes by the value %(value)s.  Choose one of: %(items)s",
        }

    def _to_python(self, value, state):
        try:
            return self.dict[value]
        except KeyError:
            if self.hideDict:
                raise Invalid(self.message('keyNotFound', state),
                              value, state)
            else:
                items = '; '.join(map(repr, self.dict.keys()))
                raise Invalid(self.message('chooseKey', state,
                                           items=items),
                              value, state)

    def _from_python(self, value, state):
        for k, v in self.dict.items():
            if value == v:
                return k
        if self.hideDict:
            raise Invalid(self.message('valueNotFound', state),
                          value, state)
        else:
            items = '; '.join(map(repr, self.dict.values()))
            raise Invalid(self.message('chooseValue', state,
                                       value=repr(value),
                                       items=items),
                          value, state)

class IndexListConverter(FancyValidator):

    """
    Converts a index (which may be a string like '2') to the value in
    the given list.

    Examples::

        >>> index = IndexListConverter(['zero', 'one', 'two'])
        >>> index.to_python(0)
        'zero'
        >>> index.from_python('zero')
        0
        >>> index.to_python('1')
        'one'
        >>> index.to_python(5)
        Traceback (most recent call last):
        Invalid: Index out of range
        >>> index.to_python(None)
        Traceback (most recent call last):
        Invalid: Must be an integer index
        >>> index.from_python('five')
        Traceback (most recent call last):
        Invalid: Item 'five' was not found in the list
    """

    list = None

    __unpackargs__ = ('list',)

    messages = {
        'integer': "Must be an integer index",
        'outOfRange': "Index out of range",
        'notFound': "Item %(value)s was not found in the list",
        }

    def _to_python(self, value, state):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise Invalid(self.message('integer', state),
                          value, state)
        try:
            return self.list[value]
        except IndexError:
            raise Invalid(self.message('outOfRange', state),
                          value, state)

    def _from_python(self, value, state):
        for i in range(len(self.list)):
            if self.list[i] == value:
                return i
        raise Invalid(self.message('notFound', state,
                                   value=repr(value)),
                      value, state)

class DateValidator(FancyValidator):

    """
    Validates that a date is within the given range.  Be sure to call
    DateConverter first if you aren't expecting mxDateTime input.

    earliest_date and latest_date may be functions; if so, they will
    be called each time before validating.
    """

    earliest_date = None
    latest_date = None
    after_now = False
    # Use 'datetime' to force the Python 2.3+ datetime module, or
    # 'mxDateTime' to force the mxDateTime module (None means use
    # datetime, or if not present mxDateTime)
    datetime_module = None

    messages = {
        'after': "Date must be after %(date)s",
        'before': "Date must be before %(date)s",
        # Double %'s, because this will be substituted twice:
        'date_format': "%%A, %%d %%B %%Y",
        'future': "The date must be sometime in the future",
        }

    def validate_python(self, value, state):
        if self.earliest_date:
            if callable(self.earliest_date):
                earliest_date = self.earliest_date()
            else:
                earliest_date = self.earliest_date
            if value < earliest_date:
                date_formatted = earliest_date.strftime(
                    self.message('date_format', state))
                raise Invalid(
                    self.message('after', state,
                                 date=date_formatted),
                    value, state)
        if self.latest_date:
            if callable(self.latest_date):
                latest_date = self.latest_date()
            else:
                latest_date = self.latest_date
            if value > latest_date:
                date_formatted = latest_date.strftime(
                    self.message('date_format', state))
                raise Invalid(
                    self.message('before', state,
                                 date=date_formatted),
                    value, state)
        if self.after_now:
            dt_mod = import_datetime(self.datetime_module)
            now = datetime_now(dt_mod)
            if value < now:
                date_formatted = now.strftime(
                    self.message('date_format', state))
                raise Invalid(
                    self.message('future', state,
                                 date=date_formatted),
                    value, state)

class Bool(FancyValidator):

    """
    Always Valid, returns True or False based on the value and the
    existance of the value.

    Examples::

        >>> Bool.to_python(0)
        False
        >>> Bool.to_python(1)
        True
        >>> Bool.to_python('')
        False
        >>> Bool.to_python(None)
        False
    """

    if_missing = False

    def _to_python(self, value, state):
        return bool(value)
    _from_python = _to_python

class Int(FancyValidator):

    """
    Convert a value to an integer.
    """

    messages = {
        'integer': "Please enter an integer value",
        }

    def _to_python(self, value, state):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise Invalid(self.message('integer', state),
                          value, state)

    _from_python = _to_python

class Number(FancyValidator):

    """
    Convert a value to a float or integer.  Tries to convert it to
    an integer if no information is lost.
    """

    messages = {
        'number': "Please enter a number",
        }

    def _to_python(self, value, state):
        try:
            value = float(value)
            if value == int(value):
                return int(value)
            return value
        except ValueError:
            raise Invalid(self.message('number', state),
                          value, state)

class String(FancyValidator):
    """
    Converts things to string, but treats empty things as the empty
    string.  Also takes a `max` and `min` argument, and the string
    length must fall in that range.
    """

    min = None
    max = None

    messages = {
        'tooLong': "Enter a value less than %(max)i characters long",
        'tooShort': "Enter a value %(min)i characters long or more",
        }

    def validate_python(self, value, state):
        if self.max is not None and len(value) > self.max:
            raise Invalid(self.message('tooLong', state,
                                       max=self.max),
                          value, state)
        if self.min is not None and len(value) < self.min:
            raise Invalid(self.message('tooShort', state,
                                       min=self.min),
                          value, state)

    def _from_python(self, value, state):
        if value:
            return str(value)
        if value == 0:
            return str(value)
        return ""

class Set(FancyValidator):

    """
    This is for when you think you may return multiple values for a
    certain field.  This way the result will always be a list, even if
    there's only one result.  It's equivalent to
    ForEach(convertToList=True).
    """

    def _to_python(self, value, state):
        if isinstance(value, (list, tuple)):
            return value
        elif value is None:
            return []
        else:
            return [value]

class Email(FancyValidator):
    """Validate an email address.  If you pass resolve_domain=True,
    then it will try to resolve the domain name to make sure it's valid.
    This takes longer, of course.  You must have the pyDNS modules
    installed <http://pydns.sf.net> to look up MX records.
    """

    resolve_domain = False

    usernameRE = re.compile(r"^[a-z0-9\_\-']+", re.I)
    domainRE = re.compile(r"^[a-z0-9\.\-]+\.[a-z]+$", re.I)

    messages = {
        'empty': 'Please enter an email address',
        'noAt': 'An email address must contain a single @',
        'badUsername': 'The username portion of the email address is invalid (the portion before the @: %(username)s)',
        'badDomain': 'The domain portion of the email address is invalid (the portion after the @: %(domain)s)',
        'domainDoesNotExist': 'The domain of the email address does not exist (the portion after the @: %(domain)s)',
        }

    def __init__(self, *args, **kw):
        global mxlookup
        FancyValidator.__init__(self, *args, **kw)
        if self.resolve_domain:
            if mxlookup is None:
                try:
                    from DNS.lazy import mxlookup
                except ImportError:
                    import warnings
                    warnings.warn(
                        "pyDNS <http://pydns.sf.net> is not installed on "
                        "your system (or the DNS package cannot be found).  "
                        "I cannot resolve domain names in addresses")
                    raise

    def validate_python(self, value, state):
        if not value:
            raise Invalid(
                self.message('empty', state),
                value, state)
        value = value.strip()
        splitted = value.split('@', 1)
        if not len(splitted) == 2:
            raise Invalid(
                self.message('noAt', state),
                value, state)
        if not self.usernameRE.search(splitted[0]):
            raise Invalid(
                self.message('badUsername', state,
                             username=splitted[0]),
                value, state)
        if not self.domainRE.search(splitted[1]):
            raise Invalid(
                self.message('badDomain', state,
                             domain=splitted[1]),
                value, state)
        if self.resolve_domain:
            domains = mxlookup(splitted[1])
            if not domains:
                raise Invalid(
                    self.message('domainDoesNotExist', state,
                                 domain=splitted[1]),
                    value, state)

    def _to_python(self, value, state):
        return value.strip()

class URL(FancyValidator):

    """
    Validate a URL, either http://... or https://.  If check_exists
    is true, then we'll actually make a request for the page.

    If add_http is true, then if no scheme is present we'll add
    http://
    """

    check_exists = False
    add_http = True

    url_re = re.compile(r'^(http|https)://[a-z\-\.]+\.[a-z]+(?:[0-9]+)?(?:/.*)?$', re.I)
    scheme_re = re.compile(r'^[a-zA-Z]+:')

    messages = {
        'noScheme': 'You must start your URL with http://, https://, etc',
        'badURL': 'That is not a valid URL',
        'httpError': 'An error occurred when trying to access the URL: %(error)s',
        'notFound': 'The server responded that the page could not be found',
        'status': 'The server responded with a bad status code (%(status)s)',
        }

    def _to_python(self, value, state):
        value = value.strip()
        if self.add_http:
            if not self.scheme_re.search(value):
                value = 'http://' + value
        match = self.scheme_re.search(value)
        if not match:
            raise Invalid(
                self.message('noScheme', state),
                value, state)
        value = match.group(0).lower() + value[len(match.group(0)):]
        if not self.url_re.search(value):
            raise Invalid(
                self.message('badURL', state),
                value, state)
        if self.check_exists and (value.startswith('http://')
                                  or value.startswith('https://')):
            self._check_url_exists(value, state)
        return value

    def _check_url_exists(self, url, state):
        global httplib, urlparse
        if httplib is None:
            import httplib
        if urlparse is None:
            import urlparse
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(
            url, 'http')
        if scheme == 'http':
            ConnClass = httplib.HTTPConnection
        else:
            ConnClass = httplib.HTTPSConnection
        try:
            conn = ConnClass(netloc)
            if params:
                path += ';' + params
            if query:
                path += '?' + query
            conn.request('HEAD', path)
            res = conn.getresponse()
        except httplib.HTTPException, e:
            raise Invalid(
                self.message('httpError', state, error=e),
                state, url)
        else:
            if res.status == 404:
                raise Invalid(
                    self.message('notFound', state),
                    state, url)
            if res.status != 200:
                raise Invalid(
                    self.message('status', state, status=res.status),
                    state, url)



class StateProvince(FancyValidator):

    """
    Valid state or province code (two-letter).  Well, for now I don't
    know the province codes, but it does state codes.  Give your own
    `states` list to validate other state-like codes; give
    `extraStates` to add values without losing the current state
    values.
    """

    states = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE',
               'FL', 'GA', 'HI', 'IA', 'ID', 'IN', 'IL', 'KS', 'KY',
               'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT',
               'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH',
               'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT',
               'VA', 'VT', 'WA', 'WI', 'WV', 'WY']

    extraStates = []

    __unpackargs__ = ('extraStates',)

    messages = {
        'empty': 'Please enter a state code',
        'wrongLength': 'Please enter a state code with TWO letters',
        'invalid': 'That is not a valid state code',
        }

    def validate_python(self, value, state):
        value = str(value).strip().upper()
        if not value:
            raise Invalid(
                self.message('empty', state),
                value, state)
        if len(value) != 2:
            raise Invalid(
                self.message('wrongLength', state),
                value, state)
        if value not in self.states \
           and not (self.extraStates and value in self.extraStates):
            raise Invalid(
                self.message('invalid', state),
                value, state)

    def _to_python(self, value, state):
        return str(value).strip().upper()

class PhoneNumber(FancyValidator):

    """
    Validates, and converts to ###-###-####, optionally with
    extension (as ext.##...)
    @@: should add international phone number support
    """

    _phoneRE = re.compile(r'^\s*(?:1-)?(\d\d\d)[\- \.]?(\d\d\d)[\- \.]?(\d\d\d\d)(?:\s*ext\.?\s*(\d+))?\s*$', re.I)

    messages = {
        'phoneFormat': 'Please enter a number, with area code, in the form ###-###-####, optionally with "ext.####"',
        }

    def _to_python(self, value, state):
        self.assert_string(value, state)
        match = self._phoneRE.search(value)
        if not match:
            raise Invalid(
                self.message('phoneFormat', state),
                value, state)
        return value

    def _from_python(self, value, state):
        self.assert_string(value, state)
        match = self._phoneRE.search(value)
        if not match:
            raise Invalid(self.message('phoneFormat', state),
                          value, state)
        result = '%s-%s-%s' % (match.group(1), match.group(2), match.group(3))
        if match.group(4):
            result = result + " ext.%s" % match.group(4)
        return result

class DateConverter(FancyValidator):

    """
    Validates and converts a textual date, like mm/yy, dd/mm/yy,
    dd-mm-yy, etc Always assumes month comes second value is the
    month.  Accepts English month names, also abbreviated.  Returns
    value as mx.DateTime object.  Two year dates are assumed to be
    within 1950-2020, with dates from 21-49 being ambiguous and
    signaling an error.

    Use accept_day=False if you just want a month/year (like for a
    credit card expiration date).
    """
    ## @@: accepts only US-style dates

    accept_day = True
    # also allowed: 'dd/mm/yyyy'
    month_style = 'mm/dd/yyyy'
    # Use 'datetime' to force the Python 2.3+ datetime module, or
    # 'mxDateTime' to force the mxDateTime module (None means use
    # datetime, or if not present mxDateTime)
    datetime_module = None

    _day_date_re = re.compile(r'^\s*(\d\d?)[\-\./\\](\d\d?|jan|january|feb|febuary|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)[\-\./\\](\d\d\d?\d?)\s*$', re.I)
    _month_date_re = re.compile(r'^\s*(\d\d?|jan|january|feb|febuary|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)[\-\./\\](\d\d\d?\d?)\s*$', re.I)

    _month_names = {
        'jan': 1, 'january': 1,
        'feb': 2, 'febuary': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
        }

    ## @@: Feb. should be leap-year aware (but mxDateTime does catch that)
    _monthDays = {
        1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31,
        9: 30, 10: 31, 11: 30, 12: 31}

    messages = {
        'badFormat': 'Please enter the date in the form %(format)s',
        'monthRange': 'Please enter a month from 1 to 12',
        'invalidDay': 'Please enter a valid day',
        'dayRange': 'That month only has %(days)i days',
        'invalidDate': 'That is not a valid day (%(exception)s)',
        'unknownMonthName': "Unknown month name: %(month)s",
        'invalidYear': 'Please enter a number for the year',
        'fourDigitYear': 'Please enter a four-digit year',
        'wrongFormat': 'Please enter the date in the form %(format)s',
        }

    def _to_python(self, value, state):
        if self.accept_day:
            return self.convert_day(value, state)
        else:
            return self.convert_month(value, state)

    def convert_day(self, value, state):
        self.assert_string(value, state)
        match = self._day_date_re.search(value)
        if not match:
            raise Invalid(self.message('badFormat', state,
                                       format=self.month_style),
                          value, state)
        day = int(match.group(1))
        try:
            month = int(match.group(2))
        except TypeError:
            month = self.make_month(match.group(2), state)
        else:
            if self.month_style == 'mm/dd/yyyy':
                month, day = day, month
        year = self.make_year(match.group(3), state)
        if month > 12 or month < 1:
            raise Invalid(self.message('monthRange', state),
                          value, state)
        if day < 1:
            raise Invalid(self.message('invalidDay', state),
                          value, state)
        if self._monthDays[month] < day:
            raise Invalid(self.message('dayRange', state,
                                       days=self._monthDays[month]),
                          value, state)
        dt_mod = import_datetime(self.datetime_module)
        try:
            return datetime_makedate(dt_mod, year, month, day)
        except ValueError, v:
            raise Invalid(self.message('invalidDate', state,
                                       exception=str(v)),
                          value, state)

    def make_month(self, value, state):
        try:
            return int(value)
        except ValueError:
            value = value.lower().strip()
            if self._month_names.has_key(value):
                return self._month_names[value]
            else:
                raise Invalid(self.message('unknownMonthName', state,
                                           month=value),
                              value, state)

    def make_year(self, year, state):
        try:
            year = int(year)
        except ValueError:
            raise Invalid(self.message('invalidYear', state),
                          year, state)
        if year <= 20:
            year = year + 2000
        if year >= 50 and year < 100:
            year = year + 1900
        if year > 20 and year < 50:
            raise Invalid(self.message('fourDigitYear', state),
                          year, state)
        return year

    def convert_month(self, value, state):
        match = self._month_date_re.search(value)
        if not match:
            raise Invalid(self.message('wrongFormat', state,
                                       format='mm/yyyy'),
                          value, state)
        month = self.make_month(match.group(1), state)
        year = self.make_year(match.group(2), state)
        if month > 12 or month < 1:
            raise Invalid(self.message('monthRange', state),
                          value, state)
        dt_mod = import_datetime(self.datetime_module)
        return datetime_makedate(dt_mod, year, month, 1)

    def _from_python(self, value, state):
        if self.accept_day:
            return self.unconvert_day(value, state)
        else:
            return self.unconvert_month(value, state)

    def unconvert_day(self, value, state):
        # @@ ib: double-check, improve
        return value.strftime("%m/%d/%Y")

    def unconvert_month(self, value, state):
        # @@ ib: double-check, improve
        return value.strftime("%m/%Y")

class TimeConverter(FancyValidator):

    """
    Converts times in the format HH:MM:SSampm to (h, m, s).
    Seconds are optional.

    For ampm, set use_ampm = True.  For seconds, use_seconds = True.
    Use 'optional' for either of these to make them optional.

    Examples::

        >>> tim = TimeConverter()
        >>> tim.to_python('8:30')
        (8, 30)
        >>> tim.to_python('20:30')
        (20, 30)
        >>> tim.to_python('30:00')
        Traceback (most recent call last):
            ...
        Invalid: You must enter an hour in the range 0-23
        >>> tim.to_python('13:00pm')
        Traceback (most recent call last):
            ...
        Invalid: You must enter an hour in the range 1-12
        >>> tim.to_python('12:-1')
        Traceback (most recent call last):
            ...
        Invalid: You must enter a minute in the range 0-59
        >>> tim.to_python('12:02pm')
        (12, 2)
        >>> tim.to_python('12:02am')
        (0, 2)
        >>> tim.to_python('1:00PM')
        (13, 0)
        >>> tim.from_python((13, 0))
        '13:00:00'
        >>> tim2 = tim(use_ampm=True, use_seconds=False)
        >>> tim2.from_python((13, 0))
        '1:00pm'
        >>> tim2.from_python((0, 0))
        '12:00am'
        >>> tim2.from_python((12, 0))
        '12:00pm'
    """

    use_ampm = 'optional'
    prefer_ampm = False
    use_seconds = 'optional'

    messages = {
        'noAMPM': 'You must indicate AM or PM',
        'tooManyColon': 'There are two many :\'s',
        'noSeconds': 'You may not enter seconds',
        'secondsRequired': 'You must enter seconds',
        'minutesRequired': 'You must enter minutes (after a :)',
        'badNumber': 'The %(part)s value you gave is not a number: %(number)r',
        'badHour': 'You must enter an hour in the range %(range)s',
        'badMinute': 'You must enter a minute in the range 0-59',
        'badSecond': 'You must enter a second in the range 0-59',
        }

    def _to_python(self, value, state):
        time = value.strip()
        explicit_ampm = False
        if self.use_ampm:
            last_two = time[-2:].lower()
            if last_two not in ('am', 'pm'):
                if self.use_ampm != 'optional':
                    raise Invalid(
                        self.message('noAMPM', state),
                        value, state)
                else:
                    offset = 0
            else:
                explicit_ampm = True
                if last_two == 'pm':
                    offset = 12
                else:
                    offset = 0
                time = time[:-2]
        else:
            offset = 0
        parts = time.split(':')
        if len(parts) > 3:
            raise Invalid(
                self.message('tooManyColon', state),
                value, state)
        if len(parts) == 3 and not self.use_seconds:
            raise Invalid(
                self.message('noSeconds', state),
                value, state)
        if (len(parts) == 2
            and self.use_seconds
            and self.use_seconds != 'optional'):
            raise Invalid(
                self.message('secondsRequired', state),
                value, state)
        if len(parts) == 1:
            raise Invalid(
                self.message('minutesRequired', state),
                value, state)
        try:
            hour = int(parts[0])
        except ValueError:
            raise Invalid(
                self.message('badNumber', state, number=parts[0], part='hour'),
                value, state)
        if explicit_ampm:
            if hour > 12 or hour < 1:
                raise Invalid(
                    self.message('badHour', state, number=hour, range='1-12'),
                    value, state)
            if hour == 12 and offset == 12:
                # 12pm == 12
                pass
            elif hour == 12 and offset == 0:
                # 12am == 0
                hour = 0
            else:
                hour += offset
        else:
            if hour > 23 or hour < 0:
                raise Invalid(
                    self.message('badHour', state,
                                 number=hour, range='0-23'),
                    value, state)
        try:
            minute = int(parts[1])
        except ValueError:
            raise Invalid(
                self.message('badNumber', state,
                             number=parts[1], part='minute'),
                value, state)
        if minute > 59 or minute < 0:
            raise Invalid(
                self.message('badMinute', state, number=minute),
                value, state)
        if len(parts) == 3:
            try:
                second = int(parts[2])
            except ValueError:
                raise Invalid(
                    self.message('badNumber', state,
                                 number=parts[2], part='second'))
            if second > 59 or second < 0:
                raise Invalid(
                    self.message('badSecond', state, number=second),
                    value, state)
        else:
            second = None
        if second is None:
            return (hour, minute)
        else:
            return (hour, minute, second)

    def _from_python(self, value, state):
        if isinstance(value, (str, unicode)):
            return value
        if hasattr(value, 'hour'):
            hour, minute = value.hour, value.minute
        elif len(value) == 3:
            hour, minute, second = value
        elif len(value) == 2:
            hour, minute = value
            second = 0
        ampm = ''
        if ((self.use_ampm == 'optional' and self.prefer_ampm)
            or (self.use_ampm and self.use_ampm != 'optional')):
            ampm = 'am'
            if hour > 12:
                hour -= 12
                ampm = 'pm'
            elif hour == 12:
                ampm = 'pm'
            elif hour == 0:
                hour = 12
        if self.use_seconds:
            return '%i:%02i:%02i%s' % (hour, minute, second, ampm)
        else:
            return '%i:%02i%s' % (hour, minute, ampm)


class PostalCode(Regex):

    """
    US Postal codes (aka Zip Codes).
    """

    regex = r'^\d\d\d\d\d(?:-\d\d\d\d)?$'
    strip = True

    messages = {
        'invalid': 'Please enter a zip code (5 digits)',
        }

class StripField(FancyValidator):

    """
    Take a field from a dictionary, removing the key from the
    dictionary.  ``name`` is the key.  The field value and a new copy
    of the dictionary with that field removed are returned.
    """

    __unpackargs__ = ('name',)

    messages = {
        'missing': 'The name %(name)s is missing',
        }

    def _to_python(self, valueDict, state):
        v = valueDict.copy()
        try:
            field = v[self.name]
            del v[self.name]
        except KeyError:
            raise Invalid(self.message('missing', state,
                                       name=repr(self.name)),
                          valueDict, state)
        return field, v

class FormValidator(FancyValidator):
    """
    A FormValidator is something that can be chained with a
    Schema.  Unlike normal chaining the FormValidator can
    validate forms that aren't entirely valid.

    The important method is .validate(), of course.  It gets passed a
    dictionary of the (processed) values from the form.  If you have
    .validate_partial_form set to True, then it will get the incomplete
    values as well -- use .has_key() to test if the field was able to
    process any particular field.

    Anyway, .validate() should return a string or a dictionary.  If a
    string, it's an error message that applies to the whole form.  If
    not, then it should be a dictionary of fieldName: errorMessage.
    The special key "form" is the error message for the form as a whole
    (i.e., a string is equivalent to {"form": string}).

    Return None on no errors.
    """

    validate_partial_form = False

    validate_partial_python = None
    validate_partial_other = None

class FieldsMatch(FormValidator):

    """
    Tests that the given fields match, i.e., are identical.  Useful
    for password+confirmation fields.  Pass the list of field names in
    as `field_names`.
    """

    show_match = False
    field_names = None
    validate_partial_form = True
    __unpackargs__ = ('*', 'field_names')

    messages = {
        'invalid': "Fields do not match (should be %(match)s)",
        'invalidNoMatch': "Fields do not match",
        }

    def validate_partial(self, field_dict, state):
        for name in self.field_names:
            if not field_dict.has_key(name):
                return
        self.validate_python(field_dict, state)

    def validate_python(self, field_dict, state):
        ref = field_dict[self.field_names[0]]
        errors = {}
        for name in self.field_names[1:]:
            if field_dict.get(name, '') != ref:
                if self.show_match:
                    errors[name] = self.message('invalid', state,
                                                match=ref)
                else:
                    errors[name] = self.message('invalidNoMatch', state)
        if errors:
            error_list = errors.items()
            error_list.sort()
            error_message = '<br>\n'.join(
                ['%s: %s' % (name, value) for name, value in error_list])
            raise Invalid(error_message,
                          {}, field_dict, state,
                          error_dict=errors)

class CreditCardValidator(FormValidator):
    """
    Checks that credit card numbers are valid (if not real).

    You pass in the name of the field that has the credit card
    type and the field with the credit card number.  The credit
    card type should be one of "visa", "mastercard", "amex",
    "dinersclub", "discover", "jcb".

    You must check the expiration date yourself (there is no
    relation between CC number/types and expiration dates).
    """

    validate_partial_form = True

    cc_type_field = 'ccType'
    cc_number_field = 'ccNumber'
    __unpackargs__ = ('cc_type_field', 'cc_number_field')

    messages = {
        'invalidNumber': "Please enter only the number, no other characters",
        'badLength': "You did not enter a valid number of digits",
        'invalidNumber': "That number is not valid",
        }

    def validate_partial(self, field_dict, state):
        if not field_dict.get(self.cc_type_field, None) \
           or not field_dict.get(self.cc_number_field, None):
            return None
        self.validate(field_dict, state)

    def validate(self, field_dict, state):
        errors = self._validateReturn(field_dict, state)
        if errors:
            error_list = errors.items()
            error_list.sort()
            raise Invalid(
                '<br>\n'.join(["%s: %s" % (name, value)
                               for name, value in error_list]),
                {},
                field_dict, state, error_dict=errors)

    def _validateReturn(self, field_dict, state):
        ccType = field_dict[self.cc_type_field].lower().strip()
        number = field_dict[self.cc_number_field].strip()
        number = number.replace(' ', '')
        number = number.replace('-', '')
        try:
            long(number)
        except ValueError:
            return {self.cc_number_field: self.message('invalidNumber', state)}

        assert self._cardInfo.has_key(ccType), (
            "I can't validate that type of credit card")
        foundValid = False
        validLength = False
        for prefix, length in self._cardInfo[ccType]:
            if len(number) == length:
                validLength = True
            if len(number) == length \
               and number[:len(prefix)] != prefix:
                foundValid = True
                break
        if not validLength:
            return {self.cc_number_field: self.message('badLength', state)}
        if not foundValid:
            return {self.cc_number_field: self.message('invalidNumber', state)}

        if not self._validateMod10(number):
            return {self.cc_number_field: self.message('invalidNumber', state)}
        return None

    def _validateMod10(self, s):
        """
        This code by Sean Reifschneider, of tummy.com
        """
        double = 0
        sum = 0
        for i in range(len(s) - 1, -1, -1):
            for c in str((double + 1) * int(s[i])):
                sum = sum + int(c)
            double = (double + 1) % 2
        return((sum % 10) == 0)

    _cardInfo = {
        "visa": [('4', 16),
                 ('4', 13)],
        "mastercard": [('51', 16),
                       ('52', 16),
                       ('53', 16),
                       ('54', 16),
                       ('55', 16)],
        "discover": [('6011', 16)],
        "amex": [('34', 15),
                 ('37', 15)],
        "dinersclub": [('300', 14),
                       ('301', 14),
                       ('302', 14),
                       ('303', 14),
                       ('304', 14),
                       ('305', 14),
                       ('36', 14),
                       ('38', 14)],
        "jcb": [('3', 16),
                ('2131', 15),
                ('1800', 15)],
            }

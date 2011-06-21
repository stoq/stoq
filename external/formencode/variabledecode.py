"""
VariableDecode.py
Ian Bicking <ianb@colorstudy.com>

Takes GET/POST variable dictionary, as might be returned by
`cgi`, and turns them into lists and dictionaries.

Keys (variable names) can have subkeys, with a ``.`` and
can be numbered with ``-``, like ``a.b-3=something`` means that
the value ``a`` is a dictionary with a key ``b``, and ``b``
is a list, the third(-ish) element with the value ``something``.
Numbers are used to sort, missing numbers are ignored.

This doesn't deal with multiple keys, like in a query string of
``id=10&id=20``, which returns something like ``{'id': ['10',
'20']}``.  That's left to someplace else to interpret.  If you want to
represent lists in this model, you use indexes, and the lists are
explicitly ordered.
"""

import api

__all__ = ['variable_decode', 'variable_encode', 'NestedVariables']

def variable_decode(d):
    """
    Decodes the flat dictionary d into a nested structure.
    """
    result = {}
    dicts_to_sort = {}
    known_lengths = {}
    for key, value in d.items():
        keys = key.split('.')
        new_keys = []
        was_repetition_count = False
        for key in keys:
            if key.endswith('--repetitions'):
                key = key[:-len('--repetitions')]
                new_keys.append(key)
                known_lengths[tuple(new_keys)] = int(value)
                was_repetition_count = True
                break
            elif '-' in key:
                key, index = key.split('-')
                new_keys.append(key)
                dicts_to_sort[tuple(new_keys)] = 1
                new_keys.append(int(index))
            else:
                new_keys.append(key)
        if was_repetition_count:
            continue

        place = result
        for i in range(len(new_keys)-1):
            try:
                if isinstance(place[new_keys[i]], (str, unicode, list)):
                    place[new_keys[i]] = {None: place[new_keys[i]]}
                place = place[new_keys[i]]
            except KeyError:
                place[new_keys[i]] = {}
                place = place[new_keys[i]]
        if place.has_key(new_keys[-1]):
            if isinstance(place[new_keys[-1]], dict):
                place[new_keys[-1]][None] = value
            elif isinstance(place[new_keys[-1]], list):
                if isinstance(value, list):
                    place[new_keys[-1]].extend(value)
                else:
                    place[new_keys[-1]].append(value)
            else:
                if isinstance(value, list):
                    place[new_keys[-1]] = [place[new_keys[-1]]]
                    place[new_keys[-1]].extend(value)
                else:
                    place[new_keys[-1]] = [place[new_keys[-1]], value]
        else:
            place[new_keys[-1]] = value

    to_sort_keys = dicts_to_sort.keys()
    to_sort_keys.sort(lambda a, b: -cmp(len(a), len(b)))
    for key in to_sort_keys:
        to_sort = result
        source = None
        last_key = None
        for sub_key in key:
            source = to_sort
            last_key = sub_key
            to_sort = to_sort[sub_key]
        if to_sort.has_key(None):
            noneVals = [(0, x) for x in to_sort[None]]
            del to_sort[None]
            noneVals.extend(to_sort.items())
            to_sort = noneVals
        else:
            to_sort = to_sort.items()
        to_sort.sort()
        to_sort = [v for k, v in to_sort]
        if known_lengths.has_key(key):
            if len(to_sort) < known_lengths[key]:
                to_sort.extend(['']*(known_lengths[key] - len(to_sort)))
        source[last_key] = to_sort

    return result

def variable_encode(d, prepend='', result=None):
    """
    Encodes a nested structure into a flat dictionary.
    """
    if result is None:
        result = {}
    if isinstance(d, dict):
        for key, value in d.items():
            if key is None:
                name = prepend
            elif not prepend:
                name = key
            else:
                name = "%s.%s" % (prepend, key)
            variable_encode(value, name, result)
    elif isinstance(d, list):
        for i in range(len(d)):
            variable_encode(d[i], "%s-%i" % (prepend, i), result)
        if prepend:
            repName = '%s--repetitions' % prepend
        else:
            repName = '__repetitions__'
        result[repName] = str(len(d))
    else:
        result[prepend] = d
    return result

class NestedVariables(api.FancyValidator):

    def _to_python(self, value, state):
        return variable_decode(value)

    def _from_python(self, value, state):
        return variable_encode(value)

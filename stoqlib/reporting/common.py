# -*- coding: iso-8859-1 -*-
import string, re

# from domain.states import states as states_dict

from mx import DateTime

#
# Funções geralmente úteis para a importação
#

def read_file(s):
    fd = open(s)
    fd.readline() # linha de descrição
    lines = fd.readlines()
    ret = []
    for line in lines:
        ret.append([string_strip(l) for l in line.split("\t")])
    return ret

def safe_phone(p):
    # Deve retornar no mínimo dois elementos
    ps = []
    if p.find("/") != -1:
        ps = p.split("/")
        ps = map(string.strip, ps)
        return ps
    else:
        return [p, None]

def safe_date(date):
    # Suportando strings "DD/MM/YY HH:MM:SS" 
    if len(date.split()) == 2 and date.split()[1] == "00:00:00":
        date = date.split()[0]
    d = date.replace(" ", "")
    if not d:
        return None
    if d == "__/__/____":
        return None
    try:
        parts = d.split("/")
        if len(parts) != 3:
            raise "Bad date %r" % d
        if len(parts[2]) == 2:
            return DateTime.strptime(d, "%d/%m/%y")
        elif len(parts[2]) == 4:
            return DateTime.strptime(d, "%d/%m/%Y")
        else:
            raise "Bad date %r" % d
    except DateTime.Error:
        raise "Bad date %r" % d

def safe_currency(text):
    if not text:
        return
    if text.startswith("R$ "): 
        text = text[3:]
    return safe_float(text)

def match_and_cut(s, l):
    for i in l:
        if s.upper().startswith(i.upper()):
            return s[len(i):].strip()
    return None

#def do_consave_id(id, unit, precision):
#    return int("%s%s" % (unit,  string.zfill(id, precision)))

def safe_float(f):
    if type(f) is type(""):
        if f.find(",") != -1:
            f = f.replace(".", "")
            return float(f.replace(",", "."))
    return float(f)

def safe_int(i):
    if type(i) is type(""):
        if i.find(",") != -1:
            i = i.replace(".", "")
            i = i.replace(",", ".")
            return int(float(i))
    return int(i or 0)

def string_strip(s):
    if s and type(s) is type(""):
        if s[0] == '"': s = s[1:]
        if s[-1] == '"': s = s[:-1]
    return str(s).strip()

def get_person_by_document(conn, doc, attr, klass):
    return conn[klass].query('%s == "%s"' % (attr, doc))

def raw_number(number):
    return re.sub('[^0-9]', '', number)

def query_single(conn, klass, query):
    res = conn[klass].query(query)
    if res:
        assert len(res) == 1
        return res[0]
    return None

# def safe_state(s):
#     if not s or s.upper() not in states_dict.keys():
#         print "Aviso: Estado %r não é um estado válido, usado SP" % s
#         return "SP"
#     return s.upper()

def get_street_info(a):
    s, rest = get_street_type(a)
    if rest.startswith(".") or rest.startswith(";") or rest.startswith(":"):
        rest = rest[1:].strip()
    new_s, new_rest = get_street_number(rest)
    if new_s is None:
        return s, rest, None, None
    else:
        num, compl = grab_number_bits(new_rest)
        compl = compl.replace(" - ", "")
        if compl.startswith("-"):
            compl = compl[1:]
        return s, new_s.strip(), num.strip(), compl.strip()

def get_street_type(a):
    s = match_and_cut(a, ["rua", "r.", "r:", "r "])
    if s is not None:
        return "Rua", s
    s = match_and_cut(a, ["praca", "praça", "pc.", "pc:", "pc "])
    if s is not None:
        return "Praça", s
    s = match_and_cut(a, ["avenida", "av.", "av:", "av ", "a.",  "a:", "a"])
    if s is not None:
        return "Avenida", s
    s = match_and_cut(a, ["travessa", "tr.", "tr:", "tr "])
    if s is not None:
        return "Travessa", s
    else:
        return "", a

def get_street_number(s):
    m = re.match("^(.*)\s+N\s*[ªº°.:]*\s*(\d+.*)$", s)
    if m:
        return m.group(1), m.group(2)

    m = re.match("^(.*)\s*,\s*(\d+.*)$", s)
    if m:
        return m.group(1), m.group(2)

    m = re.match("^([\sA-z]+)\s+(\d+.*)$", s)
    if m:
        return m.group(1), m.group(2)

    m = re.match("^(\d+)\s+(\d+.*)$", s)
    if m:
        return m.group(1), m.group(2)
    
    m = re.match("([^\d]+)\s+(\d+.*)$", s)
    if m:
        return m.group(1), m.group(2)

    return None, None

def grab_number_bits(nums):
    nums = re.split("[\s-]", nums)
    return nums[0], " ".join(nums[1:])


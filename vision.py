import re
from toolkit import *
from common import *
from core import *
from elements import *
from classes import *


def cut_first_part(s):
    if s.startswith('('):
        f = lambda ch, i, o: not o and i and (ch.isupper() or ch == '(')
    else: f = lambda ch, i, o: ch == '('
    return cut_at_begin(s, f)


def extract_parts(s):
    parts = []
    while s:
        f, s = cut_first_part(s)
        parts.append(f)
    return parts


def set_analyze(s):
    if len(s) != 4 or s[0] + s[2] != '*=':
        return None
    return s[1] + ';' + s[3]


def create_filter(pattern, db):
    pattern = pattern.replace(' ', '')
    coef, main = extract_minor_coef(pattern, str_coef=True)
    set_a = set_analyze(main)

    if set_a is not None:
        return SetFilter(coef, set_a, db)

    elif '(' not in main:
        return PlainFilter(coef, main)

    return ComplexFilter(coef, main, db)


def pass_through(parallels, filter_):
    new_parall = []
    for p in parallels:
        new_parall += filter_.check(
            p.p, p.args)
    return new_parall


class Enum:
    def __init__(self, d):
        self.d = d
    
    def __getattr__(self, v):
        return self[v]
    
    def __getitem__(self, v):
        return self.d[v]

    def __repr__(self):
        return f'Enum({self.d})'


class Parallel:
    def __init__(self, p, args):
        self.args = args.copy()
        self.p = p

    def __repr__(self):
        return f'Parallel("{self.p}", {self.args})'


class Filter:
    def __init__(self, coef, *args):
        if coef and not coef.isnumeric():
            self.coef = None
            self.cvname = coef
        else:
            self.coef = coef_to_int(coef)
        self.config(*args)

    def _coef_node(self, c):
        cb = self.coef is None or c == self.coef
        addit = {self.cvname: c} if self.coef is None else {}
        return cb, addit

    def _cuts_node(self, p):
        sets = []
        w = ''
        while p:
            w_, p = cut_first_unit(p)
            w += w_
            c, z = extract_minor_coef(w)
            sets.append((z, c, p))
        return sets

    def config(self):
        pass
    

class PlainFilter(Filter):
    def config(self, main):
        self.main = main
    
    def check(self, p, args):
        for z, c, p in self._cuts_node(p):
            cb, addit = self._coef_node(c)
            
            if not cb or z != self.main:
                continue
            
            return [Parallel(p, args | addit)]
        return []


class SetFilter(Filter):
    def config(self, p, db):
        self.main, self.uvname = p.split(';')
        self.db = db

    def search(self, m):
        return self.db.get(self.main, m)

    def check(self, p, args):
        result = []
        for z, c, p in self._cuts_node(p):
            cb, addit = self._coef_node(c)
            
            if not cb:
                continue

            unit = self.search(z)

            if unit is None:
                continue
            
            new_args = args | {
                self.uvname: unit
            } | addit
            result.append(Parallel(p, new_args))
        
        return result


class ComplexFilter(Filter):
    def config(self, main, db):
        parts = extract_parts(main)
        self.units = [create_filter(p, db) for p in parts]
    
    def check(self, p, args):
        result = []
        for z, c, p in self._cuts_node(p):
            cb, addit = self._coef_node(c)
            if not cb:
                continue
            q = [Parallel(z, args | addit)]
            for u in self.units:
                q = pass_through(q, u)
            for qi in q:
                if qi.p:
                    continue
                qi.p = p
                result.append(qi)
        return result
        

class Database:
    def __init__(self, data):
        self.data = data

    def search(self, lbl, arr):
        for unit in arr:
            if lbl == unit.label:
                return unit
        return None

    def get(self, path, lbl):
        return self.search(lbl, self.data[path])

    def __getitem__(self, v):
        return self.data[v]

    def __setitem__(self, n, v):
        self.data[n] = v


class Vision:
    def __init__(self, db, *engines):
        self.units = []
        self.db = db
        for e in engines:
            local = [
                obj for a in dir(e)
                if type(obj := getattr(e, a)) \
                  == parseunit
            ]
            self.units += local
        for u in self.units:
            u.cfg_filter(db)

    def register_excep(self, excep):
        self.excep = excep

    def parse_excep(self, expr):
        for u in self.excep:
            if u.label == expr:
                return u
        return None

    def parse(self, expr):
        expr = expr.strip()
        coef, main = extract_major_coef(expr)

        i = main.find('{')
        if i > 0:
            descr = main[i + 1:-1]
            main = main[:i]
        else:
            descr = ''

        fc = lambda x: x.add_descr(descr)

        u = self.parse_excep(main)
        if u is not None:
            return coef * fc(u)
    
        for un in self.units:
            try:
                cb = un(main)
                assert cb is not None
            except:
                continue
            return coef * fc(cb)

        return None


class parseunit:
    def __init__(self, expr):
        self.expr = expr

    def cfg_filter(self, db):
        self.filter = create_filter(self.expr, db)

    def past_init(self, func):
        self.func = func
        return self
    
    def __call__(self, inp):
        p = self.filter.check(inp, {})
        p = [q for q in p if not q.p]
        if not p:
            return None
        enum = Enum(p[0].args)
        return self.func(enum)


def ParseUnit(expr):
    pu = parseunit(expr)
    return pu.past_init


def config(units, charge=0):
    if not units:
        return None if charge else []
    unit, units = units[0], units[1:]
    options = [unit] if type(unit) != Element else [
               unit(pch) for pch in unit.possible_charges
               if pch != 0]
    for op in options:
        cb = config(units, charge - op.full_charge())
        if cb is None:
            continue
        return [op] + cb
    return None


def b_single(unit, count, charge):
    unit, = config([unit * count], -charge)
    return unit


db = Database({
    'r': [Br(-1), CO3, Cl(-1), F(-1),
        I(-1), NO3, NO2, PO4, S(-2), SO3,
        SO4, SiO3, Cr2O7, MnO4, ClO3],
    'a': all_elements
})

db['b'] = db['a'] + [NH4]


class ParseEngine:
    @ParseUnit('(*b=a)n(*r=b)m')
    def plain_salt(w):
        main = b_single(w.a, w.n, w.m * w.b.charge)
        return Salt(main, w.b)

    @ParseUnit('(*b=a)(OH)n')
    def hydroxide(w):
        main = b_single(w.a, 1, -w.n)
        return Hydroxide(main)

    @ParseUnit('(*b=a)n(O)m')
    def oxide(w):
        main = b_single(w.a, w.n, -2 * w.m)
        return Oxide(main)

    @ParseUnit('(H)n(*r=a)m')
    def acid(w):
        return Acid(w.a)

    @ParseUnit('(*a=i)k')
    def simple(w):
        return Simple(w.i)
    
    @ParseUnit('((*b=a)(OH)n)m(*r=q)k')
    def hydro_salt(w):
        ch = -w.n * w.m + w.q.charge * w.k
        main = b_single(w.m, w.a, ch)
        return HydroSalt(
            (main.identity() & OH * w.n) * w.m,
            w.q * w.k
        )

    @ParseUnit('(*b=a)n((H)k(*r=b)p)m')
    def acidic_salt(w):
        res = H(1) * w.k & w.b * w.p
        main = b_single(w.a, w.n, res.charge * w.m)
        return AcidicSalt(main, res)


vision = Vision(db, ParseEngine())
vision.register_excep([
    N(-3) & H(1) * 3, H2O,
    Si(-4) & 4 * H(1)
])


def parse(c):
    return vision.parse(c)


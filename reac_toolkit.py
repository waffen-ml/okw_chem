from balance import *
from classes import *
from core import *
from elements import *
from data import *
from itertools import permutations
from types import FunctionType
from vision import parse
from common import *
from acids import *


N2 = Simple(N)
O2 = Simple(O)


class Tag:
    def __init__(self, name, short, interp):
        self.short = short
        self.name = name
        self.interp = interp

    def __repr__(self):
        return self.interp

    def IF(self, state):
        return self if state else None


class ReacEnum:
    def __init__(self, *tags):
        self.tags = tags

    def _search(self, attr, v):
        for t in self.tags:
            if getattr(t, attr) == v:
                return t
        return None

    def _get_by_short(self, short):
        return self._search('short', short)
    
    def _get_by_name(self, name):
        return self._search('name', name)

    def __call__(self, short):
        return self._get_by_short(short)

    def __getattr__(self, v):
        return self._get_by_name(v)
    
    def __getitem__(self, v):
        return getattr(self, v)


class overridefunc:
    def __init__(self, *args):
        cond, to_overr = args[:-1], args[-1]
        self.cond = OverrideCond(*cond)
        self.id = to_overr.id

    def past_init(self, func):
        self.func = func
        return self

    def __call__(self, *units):
        units = self.cond(*units)
        if units is not None:
            return self.func(*units)


class OverrideCond:
    def __init__(self, *units):
        self.is_cycl = False
        if len(units) == 1 and type(units[0]) == FunctionType:
            self.cond = units[0]
        else:
            self.cond = make_cycl_filter(make_filter(*units))
            self.is_cycl = True

    def __call__(self, *units):
        if self.is_cycl:
            return self.cond(*units)
        elif self.cond(*units):
            return units


class ResultUnion:
    def __init__(self, tags=None, descr=''):
        self.tags = tags
        self.descr = descr

    def make_result(self, *products, descr='', tags=None):
        return make_result(*products, 
            descr=descr or self.descr,
            tags=tags or self.tags)


class reacfunc:
    INCR_ID = 0

    def __init__(self, *cond, key=None):
        if type(cond[-1]) == FunctionType:
            key = cond[-1]
            cond = cond[:-1]
        cond_filter = make_filter(*cond)
        key_filter = key or (lambda *x: True)
        self.filter = make_cycl_filter(
            cond_filter, key_filter)
        self.inp_len = len(cond)
        self.overrides = []
        self.id = reacfunc.INCR_ID
        reacfunc.INCR_ID += 1
    
    def add_override(self, f):
        self.overrides.append(f)

    def past_init(self, func):
        self.func = func
        return self

    def __call__(self, *units):
        if len(units) != self.inp_len:
            return None
        units = self.filter(*units)
        if units is None:
            return None
        for overr in self.overrides:
            result = overr(*units)
            if result is not None:
                return result
        return self.func(*units)


class Equation:
    def __init__(self, left, right, bidirect=False, show_descr=False):
        self.left = left
        self.right = right
        self.bidirect = bidirect
        self.show_descr = show_descr

    def __repr__(self):
        l_str, r_str = [' + '.join(str(p) for p in arr)
            for arr in (self.left, self.right)]
        arrow = '<-->' if self.bidirect else '-->'
        return l_str + f' {arrow} ' + r_str


class Result:
    def __init__(self, left, right, description, tags):
        left = combine_units(left)
        right = combine_units(right)
        self.description = description
        self.tags = tags
        self.is_bidirect = self.contains_tag(RT.BIDIRECT)
        self.plain = Equation(*make_balance(left, right),
            self.is_bidirect)
        self._make_full_ion()
        self._make_short_ion()

    def _make_full_ion(self):
        to_iter = self.plain.left, self.plain.right
        parts = [[], []]
        for i, arr in enumerate(to_iter):
            for j in arr:
                parts[i] += j.dissolve()
            parts[i] = combine_units(parts[i])
        self.full_ion = Equation(*parts, self.is_bidirect)

    def _make_short_ion(self):
        left = self.full_ion.left.copy()
        right = self.full_ion.right.copy()
        idx = 0
        while idx < len(left):
            for idx2, ion in enumerate(right):
                if str(ion) == str(left[idx]):
                    left.pop(idx)
                    right.pop(idx2)
                    break
            else:
                idx += 1
        if len(left) == len(self.full_ion.left):
            self.short_ion = None
            return
        self.short_ion = Equation(left, right, self.is_bidirect)

    def is_empty(self):
        return self.short_ion is not None \
            and not self.short_ion.left

    def contains_tag(self, tag):
        for t in self.tags:
            if t.name == tag.name:
                return True
        return False

    def __call__(self, ion=False, short=False):
        if not ion:
            return self.plain
        elif ion and short:
            return self.short_ion
        else:
            return self.full_ion

    def __repr__(self):
        return str(self())

    def describe(self):
        output = ''
        if self.description:
            output += self.description + '\n\n'
        output += underlined('Обычное уравнение:') + '\n' + str(self())
        output += '\n\n' + underlined('Полное ионное:') + '\n' + str(self(ion=True))
        output += f'\n\n{underlined("Короткое ионное:")}\n{self.short_ion}' * \
            (1 - (self.short_ion is None))
        if self.tags:
            output += '\n\n' + underlined('Дополнительно:')
            for tag in self.tags:
                output += '\n * ' + str(tag)
        return output


class ReactCore:
    def __init__(self, *engines):
        self.funcs = {}

        for engine in engines:
            self.append_funcs(list(
                vars(engine).values()
            ))

    def append_funcs(self, funcs):
        for f in funcs:
            if type(f) == reacfunc:
                self.funcs[f.id] = f
            elif type(f) == overridefunc:
                self.funcs[f.id].add_override(f)

    def append_from_file(self, path):
        fe = FileExtractor()
        funcs = fe.extract(path)
        self.append_funcs(funcs)

    def append_unique_reacs(self, reacs):
        for r in reacs:
            self.append_funcs(r.convert())
    
    def __call__(self, *units):
        units = [u.identity() for u in units]

        if any(u.charge != 0 for u in units):
            return None

        results = []

        for func in self.funcs.values():
            try:
                pot_result = func(*units)
                assert pot_result is not None
            except Exception as ex:
                if type(ex) == AssertionError:
                    continue
                raise ex
                continue
            if type(pot_result) not in [list, tuple]:
                pot_result = [pot_result]
            results += [Result(units, pr['end_products'],
                    pr['description'], pr['tags']) for pr in pot_result]

        results = [r for r in results if not r.is_empty()]
        rcleaner = RepeatCleaner()

        return rcleaner.clean(results)


class RepeatCleaner:
    def unit_labels(self, units):
        return [str(u) for u in units]
    
    def collection_label(self, coll):
        labels = self.unit_labels(coll)
        return ';'.join(sorted(labels))

    def reac_label(self, r):
        left_lbl = self.collection_label(r.plain.left)
        right_lbl = self.collection_label(r.plain.right)
        return left_lbl + '=' + right_lbl

    def calc_potential(self, r):
        return (r.description is not None) + \
            (len(r.tags) > 0) * 1.5

    def clean(self, results):
        state = {}
        results = [(r, self.reac_label(r)) for r in results]
        for res, lbl in results:
            pot = self.calc_potential(res)
            if lbl not in state or state[lbl][1] <= pot:
                state[lbl] = (res, pot)
        return [p[0] for p in state.values()]


class Transforms:
    def __init__(self, *tf_arr):
        self.tf_arr = tf_arr

    def __call__(self, unit):
        for p, ch in self.tf_arr:
            if p != unit:
                continue
            return [c * unit.coef for c in ch]
        return [unit]

    def proc_arr(self, arr):
        new_arr = []
        for el in arr:
            new_arr += self(el)
        return new_arr


class UniqueReac:
    def __init__(self, base_unit, reacs):
        self.base_unit = base_unit
        self.reacs = reacs
    
    def convert(self):
        return [
            reac.convert(self.base_unit)
            for reac in self.reacs
        ]


class URUnit:
    def __init__(self, addits, result, descr='', tags=None, overr=None):
        self.overr = overr
        self.addits = wrap(addits)
        self.result = result
        self.descr = descr
        self.tags = tags
        self.organize_result()
        self.set_defaults()

    def set_defaults(self):
        for d in self.result:
            if not d['description']:
                d['description'] = self.descr
            elif not d['tags'] and self.tags is not None:
                d['tags'] = wrap(self.tags)
    
    def organize_result(self):
        if is_chemunit(self.result):
            self.result = [self.result]
            self.organize_result()
        elif type(self.result) == dict:
            self.result = [self.result]
        elif is_chemunit(self.result[0]):
            self.result = [self.result]
            
        converted = []
        for obj in self.result:
            if type(obj) != dict:
                obj = make_result(*obj)
            converted.append(obj)
        self.result = converted

    def convert(self, base_unit):
        all_units = [base_unit] + self.addits

        if self.overr is None:
            func = reacfunc(*all_units)
        else:
            func = overridefunc(*all_units, self.overr)
        
        return func.past_init(lambda *x: self.result)


class FileExtractor:
    SPLITTER = '#'

    def parse_units_eq(self, equat):
        return [parse(u.strip())
                for u in equat.split('+')]

    def parse_eq(self, equat):
        left, right = equat.split('->')
        return [self.parse_units_eq(left),
                self.parse_units_eq(right)]

    def extract_reaction(self, line):
        units = line.split(FileExtractor.SPLITTER)
        descr = None if len(units) < 2 else units[1].strip().capitalize()
        units = units[0].split(',')
        left, right = self.parse_eq(units[0])
        tags = [RT(t.strip()) for t in units[1:]]

        @Reaction(*left)
        def f(*args):
            return make_result(*right, tags=tags, descr=descr)
        
        return f 

    def valid(self, line):
        return not (line.startswith(FileExtractor.SPLITTER) or not strweight(line))

    def extract(self, filename):
        with open(filename, 'r', encoding='utf8') as f:
            lines = f.read().splitlines()
        return [self.extract_reaction(line)
                for line in lines if self.valid(line)]


def chem_filter(units, f_units):
    for f_unit, unit in zip(f_units, units):
        a = type(f_unit) in [list, tuple] and (unit in f_unit or type(unit) in f_unit)
        b = type(f_unit) == type and f_unit == type(unit)
        c = issubclass(type(f_unit), ChemUnit) and f_unit == unit
        if not (a or b or c):
            return False
    return True


def make_filter(*f_units):
    func = lambda *units: chem_filter(units, f_units)
    return func


def make_cycl_filter(*filters, return_seq=True):
    def f(*units):
        perm = permutations(
            range(len(units)),
            len(units))
        for p in perm:
            params = [units[i] for i in p]
            for filter_ in filters:
                if not filter_(*params):
                    break
            else:
                return params
        return None
    def g(*units):
        seq = f(*units)
        if not return_seq:
            return seq is not None
        return seq
    return g


def Reaction(*args, **kwargs):
    rf = reacfunc(*args, **kwargs)
    return rf.past_init


def Override(*args):
    ov = overridefunc(*args)
    return ov.past_init


def make_result(*products, descr='', tags=None):
    if type(tags) not in [list, tuple]:
        tags = [tags]
    tags = list(filter(lambda x: x, tags))
    d = dict(
        end_products = list(products),
        description = descr,
        tags = tags
    )
    return d


def is_alkali_metal(metal):
    return metal.pos_group == metal.pos_sub == 1


def is_alkali_earth_metal(metal):
    return metal.pos_group == 2 and metal.pos_sub == 1


def is_al_ea_metal(metal):
    return is_alkali_metal(metal) or is_alkali_earth_metal(metal)


def is_halogen(el):
    return el.pos_group == 7 and el.pos_sub == 1


RT = ReacEnum(
    Tag('BIDIRECT', 'bidir', 'Реакция обратима'),
    Tag('EXOTERM', 'exoterm', 'Реакция экзотермична'),
    Tag('ENDOTERM', 'endoterm', 'Реакция эндотермична'),
    Tag('NEED_HEAT', 't', 'Необходимо нагревание'),
    Tag('NEED_CATALYST', 'cat', 'Необходим катализатор'),
    Tag('NEED_LIGHT', 'hv', 'Необходим свет'),
    Tag('NEED_PRESSURE', 'p', 'Необходимо давление')
)


fe = FileExtractor()
r = fe.extract_reaction('SiCl4 + H2O -> H2SiO3 + HCl')

print(r(Si & 4 * Cl, H2O))
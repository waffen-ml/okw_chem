from balance import *
from classes import *
from core import *
from elements import *
from data import *
from itertools import permutations
from types import FunctionType
from common import *


class Tag:
    def __init__(self, name, interp, data):
        self.name = name
        self.interp = interp
        self._set_data(data)
    
    def _set_data(self, data):
        self.data = wrap(data)

    def interpret(self):
        if type(self.interp) == str:
            return self.interp
        return self.interp(*self.data)
    
    def __repr__(self):
        return self.interpret()

    def __call__(self, data):
        return apply_to_copy(self, Tag._set_data, data)

    def IF(self, state):
        return self if state else None


class ReacEnum:
    def __init__(self, **d):
        self.items = d
    
    def __getattr__(self, v):
        if v in self.items:
            return self.make_tag(v)
        raise Exception('Wrong attribute')
    
    def __getitem__(self, v):
        return getattr(self, v)

    def make_tag(self, name, data=None):
        return Tag(name, self.items[name], data)


class overridefunc:
    def __init__(self, key_func, id):
        self.key_func = key_func
        self.id = id

    def past_init(self, func):
        self.func = func
        return self

    def __call__(self, *units):
        if not self.key_func(*units):
            return None
        return self.func(*units)


class ResultUnion:
    def __init__(self, tags=None, descr=''):
        self.tags = tags
        self.descr = descr

    def make_result(self, *products, descr='', tags=None):
        return make_result(*products, 
            descr or self.descr,
            tags or self.tags)


class reacfunc:
    INCR_ID = 0

    def __init__(self, *cond, key=None):
        if type(cond[-1]) == FunctionType:
            key = cond[-1]
            cond = cond[:-1]
        self.cond = make_filter(*cond)
        self.inp_len = len(cond)
        self.key = key or (lambda *x: True)
        self.overrides = []
        self.id = reacfunc.INCR_ID
        reacfunc.INCR_ID += 1
    
    def add_override(self, f):
        self.overrides.append(f)

    def past_init(self, func):
        self.func = func
        return self

    def _perm_fit(self, units):
        return self.cond(*units) and self.key(*units)

    def proceed(self, *params):
        for overr in self.overrides:
            result = overr(*params)
            if result is not None:
                return result
        return self.func(*params)

    def __call__(self, *units):
        if len(units) != self.inp_len:
            return None
        
        perm = permutations(range(len(units)), len(units))

        for p in perm:
            params = [units[i] for i in p]
            if not self._perm_fit(params):
                continue
            return self.proceed(*params)


class Equation:
    def __init__(self, left, right, bidirect=False):
        self.left = left
        self.right = right
        self.bidirect = bidirect

    def __repr__(self):
        l_str, r_str = [' + '.join(str(p) for p in arr)
            for arr in (self.left, self.right)]
        arrow = '<->' if self.bidirect else '->'
        return l_str + f' {arrow} ' + r_str


class Result:
    def __init__(self, left, right, description, tags):
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

    def contains_tag(self, tag):
        for t in self.tags:
            if t.name == tag:
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
        output = underlined('Обычное уравнение:') + '\n' + str(self())
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
            for el in dir(engine):
                a = getattr(engine, el)

                if type(a) == reacfunc:
                    self.funcs[a.id] = a

                elif type(a) == overridefunc:
                    self.funcs[a.id].add_override(a)

    def __call__(self, *units):
        units = [u.identity() for u in units]

        if any(u.charge != 0 for u in units):
            return None

        results = []

        for func in self.funcs.values():
            pot_result = func(*units)
            if pot_result is None:
                continue
            if type(pot_result) not in [list, tuple]:
                pot_result = [pot_result]
            results += [Result(units, pr['end_products'],
                    pr['description'], pr['tags']) for pr in pot_result]

        return results


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


def chem_filter(units, f_units):
    for f_unit, unit in zip(f_units, units):
        a = type(f_unit) in [list, tuple] and (unit in f_unit or type(unit) in f_unit)
        b = type(f_unit) == type and f_unit == type(unit)
        c = f_unit == unit
        if not (a or b or c):
            return False
    return True


def make_filter(*f_units):
    func = lambda *units: chem_filter(units, f_units)
    return func


def Reaction(*args, **kwargs):
    rf = reacfunc(*args, **kwargs)
    return rf.past_init


def Override(key_func, rf):
    ov = overridefunc(key_func, rf.id)
    return ov.past_init


def make_result(*products, descr='', tags=None):
    if type(tags) not in [list, tuple]:
        tags = [tags]
    tags = list(filter(lambda x: x, tags))
    return dict(
        end_products = list(products),
        description = descr,
        tags = tags
    )


class MainReactions:
    @Reaction(Hydroxide, Acid)
    def hydroxide_acid(hydr, acid):
        return make_result(H2O, Salt(
            hydr.base(), acid.residue()))
        
    @Reaction(Hydroxide, Oxide, lambda x, y: x.is_soluble and y.type == CT.ACIDIC)
    def hydroxide_acid_oxide(hydr, oxide):
        new_residue = Compound(oxide.base(), oxide.residue().incr(1))
        return make_result(H2O, Salt(hydr.base(), new_residue))
        
    @Reaction(Salt, Hydroxide, are_all_soluble)
    def salt_hydroxide(salt, hydr):
        new_hydr = Hydroxide(salt.base())
        new_salt = Salt(hydr.base(), salt.residue())

        if not are_all_soluble(new_hydr, new_salt):
            return make_result(new_hydr, new_salt)

    @Reaction(Salt, Acid)
    def salt_acid(salt, acid):
        new_salt = Salt(salt.base(), acid.residue())
        new_acid = Acid(salt.residue())

        if new_acid.strength < acid.strength or not new_salt.is_soluble:
            return make_result(new_salt, new_acid)

    @Reaction(Salt, Simple, lambda x, y: x.is_soluble and y.is_metal)
    def salt_metal(salt, metal_in):
        metal_out = salt.base()
        if ActivityRow.get_more_active_id(metal_out, metal_in) == 1:
            return make_result(Salt(
                metal_in, salt.residue()), metal_in)

    @Reaction(Salt, Salt, lambda x, y: are_all_soluble)
    def salt_salt(salt1, salt2):
        new_salt1 = Salt(salt1.base(), salt2.residue())
        new_salt2 = Salt(salt2.base(), salt1.residue())
        if not are_all_soluble(new_salt1, new_salt2):
            return make_result(new_salt1, new_salt2)
    
    @Reaction(Hydroxide, lambda x: not x.is_soluble)
    def insoluble_hydroxide_decomp(hydr):
        return make_result(Oxide(hydr.base()), H2O, tags=[RT.NEED_HEAT])

    @Reaction(Oxide, Acid, lambda x, y: x.type != CT.ACIDIC)
    def oxide_acid(oxide, acid):
        return make_result(Salt(oxide.base(), acid.residue()), H2O)

    @Reaction(Oxide, Oxide, lambda x, y: x.ctype == CT.BASIC and y.type == CT.ACIDIC)
    def basic_oxide_acidic_oxide(b_oxide, a_oxide):
        residue = Compound(a_oxide.base(), a_oxide.residue().incr(1))
        return make_result(Salt(b_oxide.base(), residue))
    
    @Reaction(Simple, Acid, lambda x, y: x.is_metal)
    def metal_acid(metal, acid):
        if ActivityRow.get_more_active_id(metal, H) == 0:
            return make_result(Simple(H), Salt(metal, acid.residue()))

    # FUUUUUUUCK

    @Reaction(Oxide, H2O, lambda x, y: x.type == CT.BASIC)
    def basic_oxide_water(oxide, _):
        return make_result(Hydroxide(oxide.base()))

    @Reaction(Oxide, H2O, lambda x, y: x.type == CT.ACIDIC and x.base() != Si)
    def acidic_oxide_water(oxide, _):
        residue = Compound(oxide.base(), oxide.residue().incr(1))
        return make_result(Acid(residue))

    @Reaction(Oxide, Hydroxide, lambda x, y: x.type == CT.AMPHOTERIC \
        and y.is_soluble and y.type == CT.BASIC)
    def amphoteric_oxide_with_hydroxide(oxide, hydr):
        b_metal = hydr.base(coef=1)
        a_metal = oxide.base(coef=1)
        meta = Compound(a_metal, O(-2) * 2)
        orto = Compound(a_metal, O(-2) * 3)

        if a_metal.charge == 2:
            return make_result(H2O, Salt(b_metal, meta))
        elif a_metal.charge == 3:
            return [
                make_result(H2O, Salt(b_metal, meta), descr='Мета-форма'),
                make_result(H2O, Salt(b_metal, orto), descr='Орто-форма')
            ]
        else:
            return make_result(H2O, Salt(b_metal, orto))
    
    @Reaction(Oxide, Hydroxide, H2O)
    def amphot_oxide_with_hydr_and_water(*args):
        amphot, hydr = args[:2]
        U = ResultUnion(tags=RT.NEED_HEAT.IF(type(amphot) == Hydroxide))
        
        if not (amphot.type == CT.AMPHOTERIC and hydr.is_soluble and hydr.type == CT.BASIC):
            return None
        
        a_metal = amphot.base(coef=1)
        b_metal = hydr.base(coef=1)

        alpha_complex = Complex(a_metal, OH * 4)
        beta_complex = Complex(a_metal, OH * 6)

        if a_metal.charge == 2:
            return U.make_result(Salt(b_metal, alpha_complex))
        elif a_metal.charge == 3:
            return [
                U.make_result(Salt(b_metal, alpha_complex)),
                U.make_result(Salt(b_metal, beta_complex))
            ]
        else:
            return U.make_result(Salt(b_metal, beta_complex))
    
    @Reaction(Hydroxide, Hydroxide, lambda x, y: x.type == CT.AMPHOTERIC)
    def amphot_hydroxide_overload(hydr1, hydr2):
        return Engine.amphot_oxide_with_hydr_and_water.func(hydr1, hydr2)

    @Reaction(H2SO4, Simple, lambda x, y: y.is_metal)
    def conc_h2so4_metal(_, metal):
        salt = Salt(metal, SO4) # TODO
        U = ResultUnion(tags=RT.NEED_HEAT.IF(metal in [Al, Cr, Fe]))
        if activity_row.compare_activity(metal, Al) <= 0:
            return U.make_result(salt, Acid(S(-2)), H2O)
        elif activity_row.compare_activity(metal, H) == 0:
            return [
                U.make_result(salt, H2O, S(0)),
                U.make_result(salt, H2O, Oxide(S(4)))
            ]
        elif metal not in [Au, Pt]:
            return U.make_result(salt, H2O, Oxide(S(4)))


class AmmoniumReac:
    @Reaction(NH3, Simple(O))
    def ammonia_oxygen(a, o):
        return [
            make_result(Simple(N), H2O),
            make_result(Oxide(N(2)), H2O,
            tags=RT.NEED_CATALYST(Pt))
        ]

    @Reaction(NH3, Acid)
    def ammonia_acid(a, acid):
        return make_result(Acid(NH4, acid.residue()))

    @Reaction(Salt, lambda x: x.base == NH4)
    def ammonium_salt(salt):
        U = ResultUnion(RT.NEED_HEAT)
        res = salt.residue
        if res == NO2:
            return U.make_result(H2O, Simple(N))
        elif res == NO3:
            return U.make_result(H2O, Oxide(N(1)))
        return U.make_result(NH3, Acid(salt.residue))

    @Override(lambda x, y: x.base == NH4, MainReactions.salt_metal)
    def ammonium_metal(a, b):
        pass


RT = ReacEnum(
    BIDIRECT = 'Реакция обратима',
    EXOTERM = 'Реакция экзотермична',
    ENDOTERM = 'Реакция эндотермична',
    NEED_HEAT = 'Необходимо нагревание',
    NEED_CATALYST = lambda x: f'Необходим катализатор: {x}'
)

rcore = ReactCore(MainReactions(), AmmoniumReac())
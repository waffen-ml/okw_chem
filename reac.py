from copy import copy
from balance import *
from classes import *
from core import *
from elements import *
from data import *


H2O = Compound(H(1) * 2, O(-2))


class Tag:
    def __init__(self, name, interp, data):
        if type(data) not in [tuple, list]:
            self.data = [data]
        else:
            self.data
        self.name = name
        self.interp = interp
    
    def interpret(self):
        if type(self.interp) == str:
            return self.interp
        return self.interp(*self.data)
    
    def __repr__(self):
        return self.interpret()


class ReacEnum:
    def __init__(self, **d):
        self.items = d
    
    def __getattr__(self, v):
        if v in self.items:
            return v
        raise Exception('Wrong attribute')
    
    def __getitem__(self, v):
        return getattr(self, v)

    def make_tag(self, name, data):
        return Tag(name, self.items[name], data)


RT = ReacEnum(
    BIDIRECT = 'Реакция обратима',
    EXOTERM = 'Реакция экзотермична',
    ENDOTERM = 'Реакция эндотермична',
    NEED_HEAT = 'Необходимо нагревание',
    NEED_CATALYST = lambda x: f'Необходим катализатор: {x}'
)


def Reaction(type1, type2, key=lambda x, y: True):
    rf = reacfunc(type1, type2, key)
    return rf.past_init


def make_result(*products, descr='', tags=None):
    return dict(
        end_products = list(products),
        description = descr,
        tags = tags or []
    )


class reacfunc:
    def __init__(self, cond1, cond2, key):
        self.cond1 = cond1
        self.cond2 = cond2
        if type(self.cond1) == type(self.cond2) == type:
            self.degree = 0
        elif type(self.cond1) == type:
            self.degree = 1
        elif type(self.cond2) == type:
            self.degree = 1
            self.cond1, self.cond2 = cond2, cond1
        else:
            self.degree = 2 
        self.key = key
    
    def past_init(self, func):
        self.func = func
        return self

    def fit_cond(self, u1, u2):
        p1 = type(u1) if self.degree <= 1 else u1
        p2 = type(u2) if self.degree == 0 else u2
        return p1 == self.cond1 and p2 == self.cond2

    def __call__(self, u1, u2):
        if self.fit_cond(u1, u2):
            return self.func(u1, u2)
        elif self.fit_cond(u2, u1):
            return self.func(u2, u1)
        else:
            return None


class Equation:
    def __init__(self, left, right, bidirect):
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
        self.full_ion = Equation(*[[Ion(u) for u in arr] 
            for arr in to_iter], self.is_bidirect)

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


class FullResult:
    def __init__(self, res_units):
        self.res_units = res_units

    def __repr__(self):
        pass

    def describe(self):
        pass


class ReactCore:
    def __init__(self):
        engine = Engine()
        self.funcs = [
            a for el in dir(engine)
            if type(a := getattr(engine, el)) == reacfunc
        ]

    def __call__(self, u1, u2):
        u1 = u1.identity()
        u2 = u2.identity()

        for u in u1, u2:
            if u.charge != 0:
                return None

        results = []

        for func in self.funcs:
            pot_result = func(u1, u2)
            if pot_result is None:
                continue
            res = Result([u1, u2], pot_result['end_products'],
                pot_result['description'], pot_result['tags'])
            results.append(res)

        return results
            

class Engine:
    @Reaction(Hydroxide, Acid)
    def hydroxide_acid(hydr, acid):
        return make_result(H2O, Salt(
            hydr.base(), acid.residue()))
        
    @Reaction(Hydroxide, Oxide, lambda x, y: x.is_soluble and y.type == Oxide.TYPES.ACIDIC)
    def hydroxide_acid_oxide(hydr, oxide):
        new_residue = Compound(oxide.base(), oxide.residue().incr(1))
        return make_result(H2O, Salt(hydr.base(), new_residue))
        
    @Reaction(Salt, Hydroxide, lambda x, y: are_all_soluble(x, y))
    def salt_hydroxide(salt, hydr):
        new_hydr = Hydroxide(salt.base())
        new_salt = Salt(hydr.base(), salt.residue())

        if not are_all_soluble(new_hydr, new_salt):
            return make_result(new_hydr, new_salt)

    @Reaction(Salt, Acid, lambda x, y: x.is_soluble)
    def salt_acid(salt, acid):
        new_salt = Salt(salt.base(), acid.residue())
        new_acid = Acid(salt.residue())

        if new_acid.strength < acid.strength or not new_salt.is_soluble:
            return make_result(new_salt, new_acid)

    @Reaction(Salt, Simple, lambda x, y: x.is_soluble and y.is_metal)
    def salt_metal(salt, metal_in):
        metal_out = salt.base()
        if get_more_active_id(metal_out, metal_in) == 1:
            return make_result(Salt(
                metal_in, salt.residue()), metal_in)

    @Reaction(Salt, Salt, lambda x, y: are_all_soluble(x, y))
    def salt_salt(salt1, salt2):
        new_salt1 = Salt(salt1.base(), salt2.residue())
        new_salt2 = Salt(salt2.base(), salt1.residue())
        if not are_all_soluble(new_salt1, new_salt2):
            return make_result(new_salt1, new_salt2)
    
    




from residues import *

core = ReactCore()

res = core(Hydroxide(Cu(2)), Acid(SO4))

print(res)
from balance import *
from classes import *
from core import *
from elements import *
from data import *
from itertools import permutations
from types import FunctionType
from common import *
from acids import *


N2 = Simple(N)
O2 = Simple(O)


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
            descr=descr or self.descr,
            tags=tags or self.tags)


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
        c = issubclass(type(f_unit), ChemUnit) and f_unit == unit
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


def is_alkali_metal(metal):
    if type(metal) != Element:
        return False
    return metal.pos_group == metal.pos_sub == 1


class MainReactions:
    @Reaction(Hydroxide, Acid)
    def hydroxide_acid(hydr, acid):
        return make_result(H2O, Salt(
            hydr.base(), acid.residue()),
            descr='Реакция кислоты с основанием.')
        
    @Reaction(Hydroxide, Oxide, lambda x, y: x.is_soluble and y.type == CT.ACIDIC)
    def hydroxide_acid_oxide(hydr, oxide):
        new_residue = Compound(oxide.base(), oxide.residue().incr(1))
        return make_result(H2O, Salt(hydr.base(), new_residue),
            descr='Реакция основания с кислотным оксидом.')
        
    @Reaction(Salt, Hydroxide, are_all_soluble)
    def salt_hydroxide(salt, hydr):
        new_hydr = Hydroxide(salt.base())
        new_salt = Salt(hydr.base(), salt.residue())

        if not are_all_soluble(new_hydr, new_salt):
            return make_result(new_hydr, new_salt,
                decsr='Реакция раствора соли с щелочью.')

    @Reaction(Salt, Acid)
    def salt_acid(salt, acid):
        new_salt = Salt(salt.base(), acid.residue())
        new_acid = Acid(salt.residue())

        if new_acid.strength < acid.strength or not new_salt.is_soluble:
            return make_result(new_salt, new_acid,
                descr='Реакция соли с кислотой.')

    @Reaction(H2SO4, Salt, lambda _, x: x.residue == Cl(-1))
    def h2so4_conc_salt(_, salt):
        return make_result(HCl, AcidicSalt(salt.base, H(1) & SO4),
            descr='Взаимодействие конц. серной кислоты с твердым хлоридом.')

    @Reaction(Salt, Simple, lambda x, y: x.is_soluble and y.is_metal)
    def salt_metal(salt, metal_in):
        metal_in = metal_in.base
        metal_out = salt.base
        if activity_row.compare_activity(metal_out, metal_in):
            return make_result(Salt(metal_in, salt.residue()), metal_out,
                descr='Замещение металла в соли')

    @Reaction(Salt, Salt, lambda x, y: are_all_soluble)
    def salt_salt(salt1, salt2):
        new_salt1 = Salt(salt1.base(), salt2.residue())
        new_salt2 = Salt(salt2.base(), salt1.residue())
        if not are_all_soluble(new_salt1, new_salt2):
            return make_result(new_salt1, new_salt2,
                descr='Взаимодействие растворов солей')
    
    @Reaction(Oxide, Acid, lambda x, y: x.type != CT.ACIDIC)
    def oxide_acid(oxide, acid):
        return make_result(Salt(oxide.base(), acid.residue()), H2O,
            descr='Взаимодействие оксида с кислотой')

    @Reaction(Oxide, Oxide, lambda x, y: x.type == CT.BASIC and y.type == CT.ACIDIC)
    def basic_oxide_acidic_oxide(b_oxide, a_oxide):
        residue = Compound(a_oxide.base(), a_oxide.residue().incr(1))
        return make_result(Salt(b_oxide.base(), residue),
            make_result='Взаимодействие двух оксидов')
    
    @Reaction(Simple, Acid, lambda x, y: x.is_metal)
    def metal_acid(metal, acid):
        if not activity_row.compare_activity(metal, H):
            return make_result(Simple(H),
                Salt(metal.base.orig, acid.residue),
                descr='Замещение водорода в кислоте')

    @Reaction(Oxide, H2O, lambda x, y: x.type == CT.BASIC)
    def basic_oxide_water(oxide, _):
        hydr = Hydroxide(oxide.base())
        if not hydr.is_soluble:
            return
        return make_result(hydr, 
            'Взаимодействие основного оксида с водой')

    @Reaction(Oxide, H2O, lambda x, y: x.type == CT.ACIDIC)
    def acidic_oxide_water(oxide, _):
        if oxide.base == Si:
            return
        residue = Compound(oxide.base(), oxide.residue().incr(1))
        return make_result(Acid(residue), descr='Взаимодействие кислотного оксида с водой')

    @Reaction(Oxide, Hydroxide, lambda x, y: x.type == CT.AMPHOTERIC \
        and y.is_soluble and y.type == CT.BASIC)
    def amphoteric_oxide_with_hydroxide(oxide, hydr):
        b_metal = hydr.base(coef=1)
        a_metal = oxide.base(coef=1)
        meta = Compound(a_metal, O(-2) * 2)
        orto = Compound(a_metal, O(-2) * 3)
        u = ResultUnion(descr='Взаимодействие основного гидроксида с амфотерным оксидом')

        if a_metal.charge == 2:
            return u.make_result(H2O, Salt(b_metal, meta))
        elif a_metal.charge == 3:
            return [
                u.make_result(H2O, Salt(b_metal, meta)),
                u.make_result(H2O, Salt(b_metal, orto))
            ]
        else:
            return u.make_result(H2O, Salt(b_metal, orto))
    
    @Reaction(Oxide, Hydroxide, H2O)
    def amphot_oxide_with_hydr_and_water(*args):
        amphot, hydr = args[:2]
        U = ResultUnion(tags=RT.NEED_HEAT.IF(type(amphot) == Hydroxide),
            descr='Взаимодействие основного оксида/гидроксида с амфот. гидроксидом в воде')
        
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
        return MainReactions.amphot_oxide_with_hydr_and_water.func(hydr1, hydr2)

    @Reaction(H2SO4, Simple, lambda x, y: y.is_metal)
    def conc_h2so4_metal(_, metal):
        metal = metal.base
        salt = Salt(metal.orig(), SO4)
        U = ResultUnion(tags=RT.NEED_HEAT.IF(metal in [Al, Cr, Fe]),
            descr='Взаимодействие металла с конц. серной кислотой')
        if activity_row.compare_activity(metal, Al) <= 0:
            return U.make_result(salt, Acid(S(-2)), H2O)
        elif activity_row.compare_activity(metal, H) == 0:
            return [
                U.make_result(salt, H2O, S(0)),
                U.make_result(salt, H2O, Oxide(S(4)))
            ]
        elif metal not in [Au, Pt]:
            return U.make_result(salt, H2O, Oxide(S(4)))

    @Reaction(N2, O2)
    def n2_o2(a, b):
        return make_result(Oxide(N(2)),
            tags=RT.NEED_HEAT)

    @Reaction(N(2) & O(-2), O2)
    def no_o2(a, b):
        return make_result(Oxide(N(4)))

    @Reaction(Oxide, H2O, lambda x, y: x.base == N)
    def nitr_oxide_h2o(x, y):
        if x.charge == 3:
            return make_result(HNO2)
        elif x.charge == 4:
            return make_result(HNO2, HNO3)
        elif x.charge == 5:
            return make_result(HNO3)

    @Reaction(HNO2, O2)
    def hno2_o2(x, y):
        return make_result(HNO3)
    
    @Reaction(Oxide(N(4)), H2O, O2)
    def no2_h2o_o2(x, y, z):
        return make_result(HNO3)
    
    @Reaction(C, O2)
    def co2(x, y):
        return make_result(CO2)

    @Reaction(C, CO2)
    def c_co2(x, y):
        return make_result(Oxide(C(2)))

    @Reaction(Oxide(C(2)), O2)
    def co_o2(x, y):
        return make_result(CO2)

    @Reaction(Oxide(C(2)), Oxide, lambda x, y: y.base.is_metal)
    def co_metal_oxide(x, y):
        return make_result(CO2, Simple(y.base))
    
    @Reaction(CO2, Mg)
    def co2_mg(x, y):
        return make_result(
            Oxide(Mg(2)),
            Simple(C),
            tags=RT.NEED_HEAT,
            descr='Сгорание магния в угл. газе')
    
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
    
    @Reaction(AcidicSalt, Simple, lambda x, y: y.is_metal and y not in [Li, Na, K, Ba])
    def acidic_salt_metal(salt, metal):
        new_res = salt.residue.residue
        return make_result(Salt(metal, new_res),
            Salt(salt.base, new_res), Simple(H))
        
    @Reaction(AcidicSalt, Acid)
    def acidic_salt_acid(salt, acid):
        new_res = salt.residue.residue
        new_acid = Acid(new_res)

        if new_acid.is_more_vol_than(acid) or acid.is_stronger_than(new_acid):
            return make_result(new_acid, Salt(salt.base, acid.residue))
    
    @Reaction(AcidicSalt, Hydroxide, lambda _, y: y.is_soluble)
    def acidic_salt_hydroxide(salt, hydr):
        new_res = salt.residue.residue
        return make_result(H2O, Salt(salt.base, new_res),
            Salt(hydr.base, new_res))
        
    @Reaction(AcidicSalt, Oxide, lambda _, y: y.type == CT.BASIC)
    def acidic_salt_oxide(salt, oxide):
        new_res = salt.residue.residue
        return make_result(H2O, Salt(salt.base, new_res),
            Salt(oxide.base, new_res))

    @Reaction(AcidicSalt, Salt, lambda x, y: y.is_soluble)
    def acidic_salt_salt(asalt, psalt):
        new_res = asalt.residue.residue
        acid = Acid(psalt.residue)
        s1 = Salt(asalt.base, new_res)
        s2 = Salt(psalt.base, new_res)
        if not are_all_soluble(s1, s2) or not acid.is_stable():
            return make_result(s1, s2, acid)


class Decomposing:
    ACIDS_MAT = {
        'H2CO3': [CO2, H2O],
        'H2SO3': [Oxide(S(4)), H2O],
        'HNO2': [Oxide(N(2)), Oxide(N(4)), H2O],
        'HNO2_T': [HNO3, Oxide(N(2)), H2O],
        'HNO3_T': [Oxide(N(4)), O2, H2O],
        'H2SiO3_T': [Oxide(Si(4)), H2O]
    }
    
    @Reaction(Hydroxide, lambda x: not x.is_soluble)
    def insoluble_hydroxide(hydr):
        return make_result(Oxide(hydr.base()), H2O, tags=[RT.NEED_HEAT],
            descr='Разложение нерастворимого основания')

    @Reaction(Salt, lambda x: x.base == K)
    def potassium_salts(x):
        u = ResultUnion(descr='Особое разложение соли калия', tags=RT.NEED_HEAT)
        
        if x.residue == MnO4:
            new_res = (Mn(6), 4 * O(-2))
            return u.make_result(
                Salt(K(1), new_res),
                Oxide(Mn(4)), O2
            )
        elif x.residue == Cr2O7:
            return u.make_result(
                Salt(K(1), CrO4),
                Oxide(Cr(3)), O2
            )
        elif x.residue == ClO3:
            return [
                u.make_result(Salt(K(1), Cl(-1)), O2),
                u.make_result(Salt(K(1), Cl(-1)), Salt(K(1), ClO4),
                    tags=[RT.NEED_HEAT, RT.NEED_CATALYST])
            ]

    @Reaction(Acid)
    def acids(x):
        results = []
        for pfx in '', '_T':
            lbl = x.label + pfx
            if lbl not in Decomposing.ACIDS_MAT:
                continue
            products = Decomposing.ACIDS_MAT[lbl]
            results.append(make_result(*products,
                descr='Разложение кислоты', tags=RT.NEED_HEAT.IF(pfx)))
        return results

    @Reaction(HydroSalt)
    def hydrosalts(x):
        pass

    @Reaction([Salt, AcidicSalt])
    def salts(x):
        u = ResultUnion(descr='Разложение соли', tags=RT.NEED_HEAT)

        if x.base == NH4:
            return Decomposing.ammonium_salts(x, u)
        elif x.residue == NO3:
            return Decomposing.nitrate(x, u)
        elif x.residue == H(1) & CO3:
            return Decomposing.acidic_salt_like(x, CO2, u)
        elif x.residue == H(1) & SO3:
            return Decomposing.acidic_salt_like(x, Oxide(S(4)), u)
        elif x.residue == CO3:
            return Decomposing.carbonate(x, u)
        elif x.residue == SO3:
            return Decomposing.sulfite(x, u)
        elif x.residue == SO4:
            return Decomposing.sulfate(x, u)

    def ammonium_salts(x, u):
        if x.residue == NO3:
            return u.make_result(H2O, Oxide(N(1)))
        elif x.residue == NO2:
            return u.make_result(H2O, Simple(N))
        
        if type(x) == AcidicSalt:
            residue = x.residue.residue
        else:
            residue = x.residue
        
        return u.make_result(NH3, Acid(residue))

    def acidic_salt_like(x, oxide, u):
        residue = x.residue.residue

        psalt = Salt(x.base, residue)
        result = [u.make_result(psalt, oxide, H2O)]
        if not is_alkali_metal(x.base):
            result.append(u.make_result(
                Oxide(x.base), oxide, H2O
            ))
        return result
    
    def carbonate(x, u):
        if x.is_soluble and x.base != Li:
            return
        return u.make_result(CO2, Oxide(x.base))

    def nitrate(x, u):
        base, n4ox = x.base, Oxide(N(4))

        if base.identity().equals(Mn(2)):
            base = Mn(4)
        elif base.charge == 2 and base in [Cr, Fe]:
            base = base(3)
        
        if base != Li and activity_row.compare_activity(base, Mg) == 0:
            return u.make_result(Salt(base, NO2), O2)
        elif base in Li or not activity_row.compare_activity(base, Hg):
            return u.make_result(Oxide(base), n4ox, O2)
        else:
            return u.make_result(Simple(base), n4ox, O2)

    def sulfate(x, u):
        metal = x.base
        if is_alkali_metal(metal):
            return None
        elif metal in [Ag, Hg]:
            return u.make_result(Simple(metal), O2, Oxide(S(4)))
        return u.make_result(Oxide(metal), Oxide(S(4)), O2)

    def sulfite(x, u):
        a = Salt(x.base, SO4)
        b = Salt(x.base, S(-2))
        return u.make_result(a, b)

    @Reaction(Si & H * 4)
    def silan_decomp(x):
        return make_result(Simple(Si), Simple(H),
            descr='Разложение силана', tags=RT.NEED_HEAT)


class Silicon:
    @Reaction(Simple, Simple(Si), lambda x, _: x.is_metal)
    def metal_si(x, y):
        metal = x.base.orig()
        return make_result(Salt(metal, Si(-4)),
            descr='Окисление металла кремнием',
            tags=RT.NEED_HEAT)


class Overrides:
    @Override(lambda x, y: x.is_metal and y == HNO3, MainReactions.metal_acid)
    def hno3_metal(y, x):
        metal = y.base
        if metal in [Au, Pt, Ir]:
            return None
        
        if activity_row.compare_activity(Mn, metal):
            group = 0
        elif activity_row.compare_activity(H, metal):
            group = 1
        else: group = 2

        d = {
            'Концентрация >80%': [Oxide(N(4))] * 3,
            'Концентрация 45-75%': [Oxide(N(1)), Oxide(N(2)), Oxide(N(4))],
            'Концентрация 10-40%': [Simple(N), Oxide(N(1)), Oxide(N(2))],
            'Концентрация <5%': [Salt(NH4, NO3), Simple(N), None]
        }

        results = []

        for r, arr in d.items():
            comp = arr[group]
            if comp is None:
                continue
            results.append(make_result(
                Salt(metal.orig(), NO3), H2O, comp,
                descr=r
            ))

        return results



RT = ReacEnum(
    BIDIRECT = 'Реакция обратима',
    EXOTERM = 'Реакция экзотермична',
    ENDOTERM = 'Реакция эндотермична',
    NEED_HEAT = 'Необходимо нагревание',
    NEED_CATALYST = lambda x: 'Необходим катализатор' + \
        (f': {x}' if x else '')
)


rcore = ReactCore(MainReactions(), Decomposing(),
    Silicon(), Overrides())

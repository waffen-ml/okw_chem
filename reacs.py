from reac_toolkit import *
from classes import *
from core import *
from elements import *
from data import *
from common import *
from acids import *


H2 = Simple(H)


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
                descr='Реакция раствора соли с щелочью.')

    @Reaction(Salt, Acid)
    def salt_acid(salt, acid):
        new_salt = Salt(salt.base(), acid.residue())
        new_acid = Acid(salt.residue())
        if acid.is_stronger_than(new_acid) or not new_salt.is_soluble:
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
            return make_result(Salt(metal_in.orig(), salt.residue()),
                Simple(metal_out), descr='Замещение металла в соли')

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
            descr='Взаимодействие двух оксидов')
    
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
            descr='Взаимодействие основного оксида с водой')

    @Reaction(Oxide, Hydroxide, lambda x, y: x.type == CT.AMPHOTERIC \
        and y.is_soluble and y.type == CT.BASIC)
    def amphoteric_oxide_with_hydroxide(oxide, hydr):
        b_metal = hydr.base(coef=1)
        a_metal = oxide.base(coef=1)
        meta = Compound(a_metal, O(-2) * 2)
        orto = Compound(a_metal, O(-2) * 3)
        u = ResultUnion(descr='Взаимодействие основного гидроксида с амфотерным оксидом в расплаве')

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

    @Reaction(Oxide, H2O, lambda x, y: x.type == CT.ACIDIC)
    def acidic_oxide_water(oxide, _):
        if oxide.base in [Si, N, P]:
            return
        residue = Compound(oxide.base(), oxide.residue().incr(1))
        return make_result(Acid(residue), descr='Взаимодействие кислотного оксида с водой')

    @Reaction(Oxide, H2O, lambda x, y: x.base == N)
    def nitr_oxide_h2o(x, y):
        w = x.base
        if w.charge == 3:
            return make_result(HNO2)
        elif w.charge == 4:
            return make_result(HNO2, HNO3)
        elif w.charge == 5:
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
        if activity_row.compare_activity(metal, H):
            return
        return make_result(Salt(metal.base.orig(), new_res),
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

    @Reaction(H2, Simple)
    def h2_halogen(x, y):
        el = y.base
        if not (is_halogen(el) or el == S):
            return
        charge = el.pos_group - 8
        return make_result(Acid(el(charge)),
            tags=RT.NEED_HEAT)

    @Reaction(H2, Simple, lambda x, y: y.is_metal)
    def h2_metal(x, y):
        metal = y.base
        if not is_al_ea_metal(metal):
            return
        return make_result(Salt(metal.orig(), H(-1)), tags=RT.NEED_HEAT)

    @Reaction(H2, Oxide)
    def h2_oxide(x, y):
        elem = y.base
        if type(elem) != Element:
            return
        elif not elem.is_metal or is_al_ea_metal(elem):
            return
        elif elem == Al:
            return
        return make_result(H2O, Simple(elem), tags=RT.NEED_HEAT)


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
        elif base == Li or not activity_row.compare_activity(base, Hg):
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

    @Reaction([Hydroxide(NH4), Oxide(NH4)])
    def nh4_ox_hydrox(x):
        return make_result(NH3, H2O)


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


class KrutieReakcii:
    pass # Kostov Ilya


class GovnoReakcii:
    @Reaction(Si, Simple(Cl))
    def fasfasfasfas(a, b):
        return make_result(Si(4) & Cl(-1) * 4, tags=RT.NEED_HEAT, descr='aszfdfg')
    
    @Reaction(Si & Cl * 4, H2O)
    def fakgaslfasfas(a, b):
        return make_result()

    
    """
Осн/амф оксид + кислота
Осн. оксид + кисл. оксид
Металл + кислота
Вода + основный оксид
Амф. оксид + щелочь
Амф. оксид + щелочь + вода
Амф.гидроксид + щелочь
Металл + конц. H2SO4
Различн. реакции оксидов азота
Различн. реакции оксидов углерода
Различн. реакции азотной кислоты
Кислотный оксид + вода
Кисл. соль + металл
Кисл. соль + кислота
Кисл. соль + щелочь
Кисл. соль + основные оксиды
Кисл. соль + р. соль
H2 + галогены
H2 + металл
H2 + оксиды
HNO3 + металл (разные концентрации)
"""




reacs = [
    UniqueReac(H2, [
        URUnit(Simple(N), NH3, tags=[RT.NEED_HEAT,
            RT.NEED_PRESSURE, RT.NEED_CATALYST])
    ]),
    UniqueReac(Si, [
        URUnit(Simple(Cl), Si(4) & Cl(-1) * 4, tags=RT.NEED_HEAT, descr='aszfdfg')
    ])
]


rcore = ReactCore(MainReactions, Decomposing, Overrides)
rcore.append_from_file('test.txt')


rcore.append_unique_reacs(reacs)


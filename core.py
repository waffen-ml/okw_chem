from toolkit import *
from copy import copy
from data import *


class ChemUnit:
    label = 'X'
    charge = 0
    coef = 1

    def __eq__(self, other):
        return self.label == other.label

    def equals(self, other):
        return other.coef == self.coef \
            and other.charge == self.charge \
            and self.label == other.label

    def __call__(self, coef=None):
        c = copy(self)
        if coef is not None:
            c.set_coef(coef)
        return c

    def identity(self):
        return self(1)

    def set_coef(self, new_coef):
        if new_coef <= 0:
            raise Exception(f'Invalid coef: {new_coef}')
        self.coef = new_coef
    
    def set_label(self, lbl):
        self.label = lbl

    def to_str(self, full=False, free=True):
        coef_part = optimized_int(self.coef)
        main_part = self._wrap(free)
        if free:
            label = coef_part + main_part
        else:
            label = main_part + coef_part
        if full:
            label += make_charge_lbl(self.charge)
        return label

    def _wrap(self, is_free):
        if is_free:
            return self.label
        el_count = count_upper(self.label)
        return f'({self.label})' if el_count > 1 \
            and self.coef > 1 else self.label
    
    def __repr__(self):
        return self.to_str(full=True)
    
    def __str__(self):
        return self.to_str(full=False)

    def mul_coef_(self, k):
        self.set_coef(self.coef * k)

    def incr_coef_(self, k):
        self.set_coef(self.coef + k)

    def mul(self, k):
        return apply_to_copy(self, ChemUnit.mul_coef_, k)

    def incr(self, k):
        return apply_to_copy(self, ChemUnit.incr_coef_, k)

    def __mul__(self, k):
        return apply_to_copy(self, ChemUnit.mul_coef_, k)

    def __rmul__(self, k):
        return self * k

    def __imul__(self, k):
        self.mul_coef_(k)

    def get_full_charge(self):
        return self.coef * self.charge

    def __getstate__(self):
        return self.__dict__
    
    def __setstate__(self, d):
        self.__dict__ = d.copy()


class Element(ChemUnit):
    def __init__(self, label):
        self.label = label

    def __call__(self, charge=None, coef=None):
        c = copy(self)
        if charge is not None:
            if charge not in self.possible_charges:
                raise Exception('Forbidden  charge for ' + self.label)
            c.charge = charge
        if coef is not None:
            c.set_coef(coef)
        return c

    def calc_particles(self):
        protons = self.number
        electrons = self.number - self.charge
        neutrons = round(self.atomic_mass) - protons
        return protons, electrons, neutrons

    def identity(self):
        return self(self.default_charge, 1)

    def describe(self):
        p, e, n = self.calc_particles()
        return '\n'.join([
            f'Элемент {self(coef=1).to_str(True)} ({self.name}), ' +
            f'{"металл" if self.is_metal else "неметалл"};',
            f'ПН: {self.number}, {self.pos_period} период, ' +
            f'{group_to_rome_num(self.pos_group)} группа, {["побочная", "главная"][self.pos_sub]} подгруппа;',
            f'Состав атома: {p} протонов, {e} электронов, {n} нейтронов;',
            f'Степени окисления: {", ".join(map(append_sign, self.possible_charges))};',
            f'Атомная масса: {self.atomic_mass:.2f};',
            f'Электроотрицательность: {self.electroneg:.2f}.'
        ])

    def __getattr__(self, name):
        if name == 'ctype':
            return comp_activity.get_type(self)
        return element_table(self.label, name)


class Compound(ChemUnit):
    def config(self, *args, **kwargs):
        return args

    def __init__(self, *args, **kwargs):
        args = flatten(args)
        input_units = self.config(*args, **kwargs)
        self.units = []
        self.charge = 0

        for u in input_units:
            u = u()
            self.units.append(u)
            self.charge += u.get_full_charge()

        self._optim_coef()
        self._make_label()

    def _make_label(self):
        self.label = ''
        for u in self.units:
            self.label += u.to_str(free=False)
    
    @property
    def base(self):
        return self[0]
    
    @property
    def residue(self):
        return self[1:]

    def __getitem__(self, val):
        if type(val) == int:
            return self.units[val]
        elif type(val) == slice:
            return Compound(*self.units[val])
        else:
            raise Exception('Incorrect selector')

    def __len__(self):
        return len(self.units)
    
    def get_all_elements(self):
        el = []
        for u in self.units:
            if type(u) != Element:
                m = u.get_all_elements()
                el += [k * u.coef for k in m]
            else:
                el += [u]
        return el

    def _optim_coef(self):
        g = gcd(*[
            u.coef for u in self.units
        ])
        self.charge = self.charge // g
        self.units = [u(coef=u.coef // g)
            for u in self.units]
        self.mul_coef_(g)

    def _flatten(self):
        new_units = []
        for u in self.units:
            if type(u) == Element or u.coef != 1:
                new_units.append(u)
            else:
                new_units += u.squeeze()
        self.units = new_units

    def squeeze(self):
        return self.units

    def _dissolve_cond(self):
        return False

    def _true_dissolve(self):
        return [
            Ion(u) * self.coef
            for u in (self.base, self.residue)
        ]

    def dissolve(self):
        if self._dissolve_cond():
            return self._true_dissolve()
        return [Ion(self)]


class Ion(ChemUnit):
    def __init__(self, obj):
        self.coef = obj.coef
        self.obj = obj.identity()
        self.label = obj.label
        self.charge = self.obj.charge

    def __str__(self):
        return self.to_str(True)


class Complex(Compound):
    def squeeze(self):
        return [self]
    
    def _wrap(self, _):
        return f'[{self.label}]'



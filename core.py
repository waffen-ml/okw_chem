from toolkit import *
from copy import copy
from data import get_element_attr


class ChemUnit:
    label = 'X'
    charge = 0
    coef = 1

    def __eq__(self, other):
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
        if not free:
            el_count = count_uppercase(self.label)
            main_lbl = f'({self.label})' if el_count > 1 \
                and self.coef > 1 else self.label
            label = main_lbl + coef_part
        else:
            label = coef_part + self.label
        if full:
            label += make_charge_lbl(self.charge)
        return label

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

    def identity(self):
        return self(self.default_charge, 1)

    def __getattr__(self, name):
        return get_element_attr(self, name)


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
        if not kwargs.get('no_simplify'):
            self.simplify_()
        self.flatten_()
        self._make_label()

    def _make_label(self):
        self.label = ''
        for u in self.units:
            self.label += u.to_str(free=False)
        
    def base(self):
        return self[0]
    
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

    def simplify(self):
        return apply_to_copy(self, Compound.simplify_)

    def simplify_(self):
        g = gcd(*[
            u.coef for u in self.units
        ])
        self.charge = self.charge // g
        self.units = [u(coef=u.coef // g)
            for u in self.units]
        self.mul_coef_(g)

    def flatten_(self):
        new_units = []
        for u in self.units:
            if type(u) == Element:
                new_units.append(u)
            elif u.coef != 1:
                new_units.append(u.flatten())
            else:
                new_units += u.flatten().units
        self.units = new_units

    def flatten(self):
        return apply_to_copy(self, Compound.flatten_)

    def _dissolve_cond(self):
        return False

    def _true_dissolve(self):
        return [
            Ion(u) * self.coef
            for u in self.units
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


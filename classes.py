from toolkit import *
from core import *
from elements import *
from data import *
from common import *


def get_base_ctype(base):
    if base.label == 'NH4':
        return CT.BASIC
    return base.ctype


class Oxide(Compound):
    def config(self, unit):
        self.type = get_base_ctype(unit)
        return bin_balance(unit, O(-2))


class Hydroxide(Compound):
    def config(self, base):
        self.type = get_base_ctype(base)
        self.is_soluble = solubility.check(base, OH)
        return bin_balance(base, OH)
    
    def _dissolve_cond(self):
        return self.is_soluble


class Acid(Compound):
    def config(self, *args):
        residue = Compound(*args)
        if residue.charge >= 0:
            raise Exception()
        return bin_balance(H(1), residue)

    def _post_init(self):
        self.strength = acidinfo.get_strength(self)
        self.vol = acidinfo.get_vol(self)

    def _dissolve_cond(self):
        return acidinfo.is_strong(self)

    def is_stronger_than(self, other):
        return self.strength > other.strength

    def is_more_vol_than(self, other):
        return self.vol > other.vol


class Simple(Compound):
    def config(self, element):
        index = 2 if element.is_paired_simple else 1
        element = element(charge=0, coef=index)
        return [element]

    def _optim_coef(self):
        pass

    @property
    def is_metal(self):
        return self.base.is_metal


class Salt(Compound):
    def config(self, base, res):
        return bin_balance(base, res)

    def _post_init(self):
        self.is_soluble = solubility.check(
            self.base, self.residue)

    def _dissolve_cond(self):
        return self.is_soluble


class AcidicSalt(Salt):
    pass


class HydroSalt(Salt):
    def _post_init(self):
        pass

    def _dissolve_cond(self):
        return True



from toolkit import *
from core import Compound
from elements import *
from data import *


def get_base_ctype(base):
    if base.label == 'NH4':
        return CT.BASIC
    return base.ctype


class Oxide(Compound):
    def config(self, unit):
        self.type = get_base_ctype(unit)
        return bin_balance(unit, O(-2))


class Hydroxide(Compound):
    RESIDUE = Compound(O(-2), H(1))

    def config(self, base):
        residue = Hydroxide.RESIDUE * base.charge
        self.type = get_base_ctype(base)
        self.is_soluble = solubility.check(base, residue)
        return [base, residue]
    
    def _dissolve_cond(self):
        return self.is_soluble


class Salt(Compound):
    def config(self, *args):
        base_metal = args[0]
        residue = Compound(args[1:])
        self.is_soluble = solubility.check(base_metal, residue)
        return bin_balance(base_metal, residue)

    def _dissolve_cond(self):
        return self.is_soluble


class Acid(Compound):
    CLASSIFICATION = {
        0: ['F', 'NO2', '2S', 'CO3', 'SiO3'],
        1: ['SO3', 'PO4'],
        2: ['Cl', 'Br', 'I', 'SO4', 'NO3']
    }

    @staticmethod
    def get_acid_strength(label):
        for strength, arr in Acid.CLASSIFICATION.items():
            if label in arr:
                return strength
        return 0

    def config(self, *args):
        residue = Compound(*args)
        if residue.charge >= 0:
            raise Exception()
        self.strength = Acid.get_acid_strength(residue.label)
        return [H(1) * -residue.charge, residue]

    def _dissolve_cond(self):
        return self.strength == 2


class Simple(Compound):
    def config(self, element):
        index = 2 if element.is_paired_simple else 1
        element = element(charge=0, coef=index)
        return [element]

    def simplify_(self):
        pass

    @property
    def is_metal(self):
        return self.base.is_metal
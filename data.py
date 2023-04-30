import pandas as pd
from enum import Enum


class ElementTable:
    def __init__(self):
        mtab = pd.read_csv('elements.csv')
        mtab.set_index('label', drop=True, inplace=True)
        mtab['is_metal'] = mtab['is_metal'].astype('bool')
        mtab['is_paired_simple'] = mtab['is_paired_simple'].astype('bool')
        new_charges_col = []
        for pch in mtab['possible_charges'].values:
            new_charges_col.append(tuple(int(i) for i in pch.split()))
        mtab['possible_charges'] = new_charges_col
        self.table = mtab

    def __call__(self, label, attr):
        col = self.table[attr]
        return col[label]

    def get_all_labels(self):
        return list(self.table.index)


class ActivityRow:
    ROW = ['Li', 'K', 'Ba', 'Ca', 'Na', 'La', 'Mg', 'Al', 'Mn',
        'Zn', 'Cr', 'Fe', 'Cd', 'Co', 'Ni', 'Sn', 'Pb', 'H', 'Cu', 'Hg',
        'Ag', 'Au', 'Pt']
    
    def compare_activity(self, u1, u2):
        a1, a2 = [ActivityRow.ROW.index(
            u if type(u1) == str else u.label)
            for u in (u1, u2)
        ]
        if a1 < a2:
            return 0
        elif a1 > a2:
            return 1
        return -1


class Solubility:
    def __init__(self):
        self.table = pd.read_csv('sbtable.csv')
        self.table.set_index('RESIDUE', drop=True, inplace=True)
    
    def check(self, metal, addition):
        metal_label = metal(coef=1).to_str(True)
        addit_label = addition(coef=1).to_str(True)

        if metal_label not in self.table.columns:
            return False
        
        column = self.table[metal_label]

        if addit_label not in column:
            return False
        
        status = column[addit_label]
        
        if status == 'Р':
            return True
        elif status == 'М' and metal_label in ['Ca(2+)', 'Sr(2+)']:
            return True
        else:
            return False


class CompActivity:
    TYPES = Enum('CTYPES', ['NSF', 'ACIDIC', 'BASIC', 'AMPHOTERIC'])
    AMPH_EXCEP = ['Zn', 'Be', 'Fe']
    NSF_BASES = ['N(+)', 'N(2+)', 'C(2+)', 'Si(2+)', 'S(+)']

    def _is_amph_excep(self, unit):
        return unit.label in CompActivity.AMPH_EXCEP

    def get_type(self, unit):
        if unit.is_metal:
            if self._is_amph_excep(unit) or 3 <= unit.charge <= 4:
                return CompActivity.TYPES.AMPHOTERIC
            elif 1 <= unit.charge <= 2:
                return CompActivity.TYPES.BASIC
            else:
                return CompActivity.TYPES.ACIDIC
        else:
            if unit(coef=1).to_str(charge=True) in CompActivity.NSF_BASES:
                return CompActivity.TYPES.NSF
            else:
                return CompActivity.TYPES.ACIDIC


class AcidInfo:
    STRENGTH_ROW = ['H2SiO3', 'H2S', 'H2CO3', 'HNO2', 'HF', 'H3PO4',
        'H2SO3', 'HMnO4', 'HNO3', 'H2SO4', 'HCl', 'HBr', 'HClO4', 'HI']
    STRONG_FROM = 'HMnO4'
    NSTABLE_ACIDS = ['H2CO3', 'H2SiO3']
    VOL_ROW = ['HCl', 'H2S', 'HNO3', 'HClO4']


    def is_strong(self, acid):
        s2 = self._get_strength_label(self.STRONG_FROM)
        return acid.strength >= s2

    def is_stable(self, acid):
        return acid.label in self.NSTABLE_ACIDS

    def scale(self, arr, el):
        return (arr.index(el) + 1) / len(arr)

    def _get_strength_label(self, lbl):
        return self.scale(self.STRENGTH_ROW, lbl)

    def get_strength(self, acid):
        return self._get_strength_label(acid.label)

    def _get_vol_label(self, lbl):
        return int(lbl in self.VOL_ROW)

    def get_vol(self, acid):
        return self._get_vol_label(acid.label)


element_table = ElementTable()
activity_row = ActivityRow()
solubility = Solubility()
comp_activity = CompActivity()
CT = comp_activity.TYPES
acidinfo = AcidInfo()
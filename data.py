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
    ROW = ['Li', 'K', 'Ba', 'Ca', 'Na', 'Mg', 'Al',
        'C', 'Zn', 'Fe', 'Ni', 'Sn', 'Pb', 'H', 'Cu', 'Hg',
        'Ag', 'Au', 'Pt']
    
    def compare_activity(self, u1, u2):
        a1 = ActivityRow.ROW.index(u1.label)
        a2 = ActivityRow.ROW.index(u2.label)
        if a1 > a2:
            return 0
        elif a1 < a2:
            return 1
        return -1


class Solubility:
    def __init__(self):
        self.table = pd.read_csv('sbtable.csv')
        self.table.set_index('RESIDUE', drop=True, inplace=True)
    
    def check(self, metal, addition):
        metal_label = metal(coef=1).to_str(True)
        addit_label = addition(coef=1).to_str(True) 
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
            if unit(coef=1).to_str(full=True) in CompActivity.NSF_BASES:
                return CompActivity.TYPES.NSF
            else:
                return CompActivity.TYPES.ACIDIC


element_table = ElementTable()
activity_row = ActivityRow()
solubility = Solubility()
comp_activity = CompActivity()
CT = comp_activity.TYPES
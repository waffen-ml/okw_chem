import pandas as pd
from enum import Enum


def proc_main_table(mtab):
    mtab = mtab.copy()
    mtab = pd.read_csv('elements.csv')
    mtab.set_index('label', drop=True, inplace=True)
    mtab['is_metal'] = mtab['is_metal'].astype('bool')
    mtab['is_paired_simple'] = mtab['is_paired_simple'].astype('bool')
    new_charges_col = []
    for pch in mtab['possible_charges'].values:
        new_charges_col.append(tuple(int(i) for i in pch.split()))
    mtab['possible_charges'] = new_charges_col
    return mtab


def get_activity_type(unit):
    if unit.is_metal:
        if 1 <= unit.charge <= 2:
            return ACTYPES.BASIC
        elif 3 <= unit.charge <= 4:
            return ACTYPES.AMPHOTERIC
        else:
            return ACTYPES.ACIDIC
    else:
        if unit(coef=1).to_str(full=True) in NSF_BASES:
            return ACTYPES.NSF
        else:
            return ACTYPES.ACIDIC


def get_element_attr(unit, attr_name):
    if attr_name == 'actype':
        return get_activity_type(unit)
    
    col = main_table[attr_name]
    return col[unit.label]


def get_all_labels():
    return list(main_table.index)


def get_more_active_id(u1, u2):
    l1, l2 = u1.label, u2.label
    i1 = activity_row.index(l1)
    i2 = activity_row.index(l2)
    return 0 if i1 >= i2 else 1


def is_soluble(metal, addition):
    metal_label = metal(coef=1).to_str(True)
    addit_label = addition(coef=1).to_str(True) 
    column = sb_table[metal_label]
    
    if addit_label not in column:
        return False
    
    status = column[addit_label]
    
    if status == 'Р':
        return True
    elif status == 'М' and metal_label in ['Ca(2+)', 'Sr(2+)']:
        return True
    else:
        return False


main_table = proc_main_table(pd.read_csv('elements.csv'))
sb_table = pd.read_csv ('sbtable.csv')
activity_row = ['Li', 'K', 'Ba', 'Ca', 'Na', 'Mg', 'Al',
    'C', 'Zn', 'Fe', 'Ni', 'Sn', 'Pb', 'H', 'Cu', 'Hg',
    'Ag', 'Au', 'Pt']

ACTYPES = Enum('ACTYPES', ['NSF', 'ACIDIC', 'BASIC', 'AMPHOTERIC'])
NSF_BASES = ['N(+)', 'N(2+)', 'C(2+)', 'Si(2+)', 'S(+)']
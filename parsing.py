from residues import *
from elements import *
from classes import *
from core import *


PARSE_RESIDUES = [
    SO4, SO3, NO3, CO3, SiO3, PO4, NO2, OH,
    O(-2), S(-2), Cl(-1), Br(-1), F(-1), I(-1)
]


def get_residue_by_label(label):
    for r in PARSE_RESIDUES:
        if r.label == label:
            return r
    return None


def coef_to_int(coef):
    return 1 if not coef else int(coef)    


def extract_major_coef(s, str_coef=False):
    coef = ''
    for ch in s:
        if ch.isnumeric():
            coef += ch
        else:
            break
    
    remain = s[len(coef):]
    
    if str_coef:
        return coef, remain
    else:
        return coef_to_int(coef), remain


def extract_minor_coef(s_orig):
    coef, s = extract_major_coef(s_orig[::-1], str_coef=True)
    s, coef = s[::-1], coef[::-1]
    coef = coef_to_int(coef)

    if s[0] + s[-1] != '()' and count_upper(s) > 1:
        return 1, s_orig
    else:
        proc_s = s.lstrip('(').rstrip(')')
        return coef, proc_s
    

def cut_first_unit(s):
    opened = 0
    for i, ch in enumerate(s):
        if (ch.isupper() or ch == '(') and not opened and i:
            return s[:i], s[i:]
        if ch == '(':
            opened += 1
        elif ch == ')':
            opened -= 1
    else:
        return s, ''


def count_upper(s):
    return sum(ch.isupper() for ch in s)


def rec(s, req):
    if (res := get_residue_by_label(s)) is not None:
        if res.charge == req:
            return res
        return None

    # input without coef
    curr, rem = cut_first_unit(s)
    #print(curr, rem)

    if count_upper(curr) != 1:
        raise Exception('Invalid expression')
    
    coef, lbl = extract_minor_coef(curr)
    el = Element(lbl)
    
    if not rem and req == 0:
        if coef == (1 + el.is_paired_simple):
            return Simple(el)
        return None
    elif not rem and req != 0:
        if req in el.possible_charges:
            return coef * el(req)
        return None
    
    rem_coef, rem_lbl = extract_minor_coef(rem)

    for ch in el.possible_charges:
        if ch <= 0:
            continue
        new_req = req - ch * coef
        response = rec(rem_lbl, new_req / rem_coef)
        if response is None:
            #print(el, 'nan')
            continue
        return Compound(coef * el(ch), rem_coef * response)
    
    return None


def classify_compound(comp):
    main = comp.units[0]
    residue = Compound(comp.units[1:])
    
    if residue.label == 'O':
        parsed = Oxide(main)
    elif residue.label == 'OH':
        parsed = Hydroxide(main)
    elif main.label == 'H':
        parsed = Acid(residue)
    else:
        parsed = Salt(main, residue)

    return parsed * comp.coef


def parse(s):
    coef, s = extract_major_coef(s)
    result = rec(s, 0)

    if type(result) != Simple:
        result = classify_compound(result)
    
    return coef * result


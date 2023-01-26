from copy import copy
import math


def are_all_soluble(units):
    return all(u.is_soluble for u in units)


def apply_to_copy(obj, method, *args, **kwargs):
    c = copy(obj)
    method(c, *args, **kwargs)
    return c


def gcd(*args):
    if len(args) == 1:
        return args[0]
    elif len(args) == 0:
        return 1
    g = math.gcd(args[0], args[1])
    for i in range(2, len(args)):
        g = math.gcd(g, args[i])
    return g


def lcm(*values):
    r = 1
    for v in values:
        r *= v // gcd(v, r)
    return r


def int_to_charge(n):
    if n == 0:
        return '0'
    n_sign = '-' if n < 0 else '+'
    n_abs = abs(n)
    if n_abs == 1:
        return n_sign
    return f'{n_abs}{n_sign}'


def make_charge_lbl(n):
    return f'({int_to_charge(n)})'


def optimized_int(n):
    if n > 1:
        return str(n)
    return ''


def append_sign(coef):
    if coef <= 0:
        return str(coef)
    return f'+{coef}'


def group_to_rome_num(gr):
    if gr <= 3:
        return 'I' * gr
    a = 5 - gr
    return 'I' * max(0, a) + 'V' + 'I' * max(0, -a)


def flatten(obj):
    if type(obj) not in [list, tuple]:
        return [obj]
    other = []
    for o in obj:
        other += flatten(o)
    return other


def underlined(s):
    return s + '\n' + '-' * len(s) * 2


def bin_balance(u1, u2):
    idx1 = abs(u1.charge)
    idx2 = abs(u2.charge)
    g = gcd(idx1, idx2)
    return u1(coef=idx2 // g), u2(coef=idx1 // g)


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


def cut_first_units(s, n):
    cut = ''
    for i in range(n):
        unit, s = cut_first_unit(s)
        cut += unit
    return cut, s


def coef_to_int(coef):
    return 1 if not coef else int(coef)    


def count_upper(s):
    return sum(ch.isupper() for ch in s)


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


def wrap(obj):
    if type(obj) in [list, tuple]:
        return obj
    return [obj]

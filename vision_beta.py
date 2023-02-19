from elements import *
from core import *
from residues import *
from toolkit import *
from classes import *


class ChemVision:
    def __init__(self):
        self.setup_bases()
        self.setup_exceptions()
        self.setup_residues()

    def setup_residues(self):
        self.residues = [
            Br(-1), CO3, Cl(-1), F(-1),
            I(-1), NO3, NO2, OH, PO4, S(-2), SO3,
            SO4, O(-2), SiO3
        ]

    def setup_bases(self):
        self.bases = [
            el for el in all_elements
            if any(pc > 0 for pc in el.possible_charges)
        ] + [NH4]

    def setup_exceptions(self):
        self.exceptions = [
            Compound(N(-3), 3 * H(1))
        ]

    def _get_unit(self, arr, label):
        for a in arr:
            if a.label == label:
                return a
        return None

    def get_exception(self, label):
        return self._get_unit(self.exceptions, label)

    def get_residue(self, label):
        return self._get_unit(self.residues, label)

    def get_base(self, label):
        return self._get_unit(self.bases, label)

    def _cut_base(self, s):
        to_return = None
        i = 1
        while True:
            new_base, rem = cut_first_units(s, i)
            _, base_s = extract_minor_coef(new_base)
            if self.get_base(base_s) is not None:
                to_return = (new_base, rem)
            if not rem:
                break
            i += 1
        return to_return

    def parse(self, s, charge=0):
        coef, s = extract_major_coef(s)
        
        if (excep := self.get_exception(s)) is not None:
            return excep * coef

        result = self._parse_rec(s, charge)

        #if charge != 0 and type(result) != Simple:
        #    result = self.classify_compound(result)
        
        return coef * result

    def _parse_rec(self, s, req):
        # s -> without coef!!!
        if (res := self.get_residue(s)) is not None:
            if res.charge == req:
                return res
        
        curr, res = self._cut_base(s)
        coef, lbl = extract_minor_coef(curr)
        base = self.get_base(lbl)

        if not res and req == 0 and type(base) == Element:
            if coef == (1 + base.is_paired_simple):
                return coef * Simple(base)
            return None
        
        elif not res and req != 0:
            if req == base.charge:
                return coef * base
            elif type(base) == Element and req in base.possible_charges:
                return coef * base(req)
            return None
            
        rem_coef, rem_lbl = extract_minor_coef(res)

        if type(base) == Element:
            configs = [base(pch) for pch in base.possible_charges
                if pch > 0]
        else:
            configs = [base]

        for conf in configs:
            new_req = req - conf.charge * coef
            response = self._parse_rec(rem_lbl, new_req / rem_coef)
            if response is None:
                continue
            return Compound(coef * conf, rem_coef * response)
        return None

    def regroup(self, comp):
        t = type(comp)
        coef, comp_s = extract_major_coef(str(comp))
        result = self._parse_rec(comp_s, comp.charge)
        return t(*result.units) * coef


vision = ChemVision()
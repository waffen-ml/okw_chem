from elements import *
from core import Compound
from classes import Acid, Simple


# Кислотные остатки

SO4 = Compound(S(6), O(-2) * 4)
SO3 = Compound(S(4), O(-2) * 3)
NO3 = Compound(N(5), O(-2) * 3)
CO3 = Compound(C(4), O(-2) * 3)
SiO3 = Compound(Si(4), O(-2) * 3)
PO4 = Compound(P(5), O(-2) * 4)
NO2 = Compound(N(3), O(-2) * 2)

# Кислоты

H2SO4 = Acid(SO4)
H2SO3 = Acid(SO3)
HNO3 = Acid(NO3)
HNO2 = Acid(NO2)
H3PO4 = Acid(PO4)
H2SiO3 = Acid(SiO3)
H2CO3 = Acid(CO3)
HCl = Acid(Cl(-1))
HBr = Acid(Br(-1))
HF = Acid(F(-1))
HI = Acid(I(-1))
H2S = Acid(S(-2))

# Другие соединения

H2 = Simple(H)
O2 = Simple(O)
OH = Compound(O(-2), H(1))
NH4 = Compound(N(-3), 4 * H(1))
NH3 = Compound(N(-3), H(1) * 3)
H2O = Compound(H(1) * 2, O(-2))




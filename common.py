from elements import *
from core import Compound


# Кислотные остатки

SO4 = Compound(S(6), O(-2) * 4)
SO3 = Compound(S(4), O(-2) * 3)
NO3 = Compound(N(5), O(-2) * 3)
CO3 = Compound(C(4), O(-2) * 3)
SiO3 = Compound(Si(4), O(-2) * 3)
PO4 = Compound(P(5), O(-2) * 4)
NO2 = Compound(N(3), O(-2) * 2)
ClO3 = Compound(Cl(5), 3 * O(-2))
ClO4 = Compound(Cl(7), 4 * O(-2))
Cr2O7 = Compound(Cr(6) * 2, O(-2) * 7)
CrO4 = Compound(Cr(6), 4 * O(-2))
MnO4 = Compound(Mn(7), O(-2) * 4)


# Другие соединения

OH = Compound(O(-2), H(1))
NH4 = Compound(N(-3), 4 * H(1))
NH3 = Compound(N(-3), H(1) * 3)
H2O = Compound(H(1) * 2, O(-2))
CO2 = Compound(C(4), O(-2) * 2)



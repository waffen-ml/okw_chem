from core import *
from elements import *
from common import *
from classes import *
from reacs import *
from balance import make_balance



# Три способа создания соединений
# Cu(HSO4)2

comp1 = Cu(2) & (H(1) & SO4) * 2
comp2 = Compound(Cu(2), 2 * Compound(H(1), SO4))

# Индексы расставляются автоматически
comp3 = AcidicSalt(Cu(2), H(1) & SO4)



# Все типы соединений

c1 = Oxide(Al(3))
c2 = Hydroxide(Na(1))
c3 = Salt(K(1), SO4)
c4 = AcidicSalt(Ca(2), H(1) & SO4)
c5 = HydroSalt(Cu(2) & OH, CO3)
c6 = Simple(H)
c7 = Acid(SO4)



# МЭБ

left = [H2SO4, Simple(Al)]
right = [Salt(Al(3), SO4), H2S, H2O]
eq1 = Equation(left, right)

print(eq1, '(без коэф.)')

new_left, new_right = make_balance(left, right)
eq2 = Equation(new_left, new_right)

print(eq2, '(с коэф.)')


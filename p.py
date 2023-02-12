from classes import *
from elements import *
from core import *
from common import *
from reac import *

s1 = Salt(
    Ca(2), (H(1), PO4)
)
s2 = Salt(K(1), SO4)

print(s1, s2)
print(type(s1), type(s2))

print(rcore(s1, s2))
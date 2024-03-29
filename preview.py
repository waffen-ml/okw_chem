# Получение доступа к элементам
# из таблицы Менделеева

from elements import *

# В Python можно создавать переменные
# И записывать в них элементы с их С.О. и коэф-том.

a1 = Cu(2) # Cu(2+)
a2 = 5 * Na(1) # 5Na(+)
a3 = Ti(4, coef=10) # 10Ti(4+)
a4 = 2 * K(0) # 2K(0)

p1 = a2.identity() # Удаление коэф-та, 5Na(+) -> Na(+)
p2 = a3(coef=5) # Изменение коэф-та, 10Ti(4+) -> 5Ti(4+)
p3 = a2(coef=1) # Также удаление коэф-та, 5Na(+) -> Na(+)
p4 = a1(1) # Постановка в другую С.О., Cu(2+) -> Cu(+)
p5 = a4.orig() # Постановка в стандартную С.О.,
               # А также удаление коэф-та, 2K(0) -> K(+)
p6 = a3 * 3 # Домножение элементов, 10Ti(4+) -> 30Ti(4+)

# Сравнение эл-тов
# (только по названию)
if a2 == Na: # 5Na(+) и Na(+), Да
    pass

# Сравнение эл-тов
# (по названию, С.О. и коэф-ту)
if a2.equals(Na): # 5Na(+) и Na(+), Нет
    pass

# Вхождение эл-та в список
# 5Na(+) in [Al(3+), Na(+), P(5+)], Да 
if a2 in [Al, Na, P]:
    pass # код



# Импортируем нужный класс
from core import Compound

# Для простоты будем давать переменным
# имена, соответствующие хим. формулам
# хранящихся в них соединений.

# Но некоторые формулы не соответствуют
# правилам синтаксиса Python. Тогда
# будем писать просто "comp"

# Создаем несколько соединений.

H2 = Compound(H(0) * 2) # водород, простое вещ.
H2O = Compound(H(1) * 2, O(-2)) # вода
N2O5 = Compound(2 * N(5), O(-2) * 5) # оксид азота (5)
SO4 = Compound(S(6), 4 * O(-2)) # сульфат-анион
NH4 = Compound(N(-3), 4 * H(1)) # аммоний (катион)
OH = Compound(O(-2), H(1)) # гидроксогруппа (анион)

# Теперь создадим соединения из
# уже готовых составляющих

CuOH = Compound(Cu(2), OH) # катион
Na2SO4 = Compound(2 * Na(1), SO4) # сульфат натрия
comp1 = Compound(CuOH * 2, SO4) # (CuOH)2SO4
NH4Cl = Compound(NH4, Cl(-1)) # хлорид аммония

# Также соединения можно создавать
# более удобным способом:

NaOH = Na(1) & OH
SO2 = S(4) & 2 * O(-2)
comp2 = (Ba(2) & OH) * 2 & S(-2)


# Можно легко получить состав соединения.

arr1 = NaOH.get_all_elements() # [Na(+), O(2-), H(+)]
arr2 = comp2.get_all_elements() # [2Ba(2+), 2O(2-), 2H(+), S(2-)]
arr3 = NH4Cl.get_all_elements() # [N(3-), 4H(+), Cl(-)]

# Но соединение также можно разбить на более
# понятные для человека единицы.

arr4 = NH4Cl.squeeze() # [NH4(+), Cl(-)]
arr5 = Na2SO4.squeeze() # [2Na(+), SO4(2-)]

# Для удобства в движок была введена возможность
# поделить соединение на две части: на "базу" и "остаток".

# Приведем пример:

NaHSO4 = Na(1) & (H(1) & SO4)

a = NaHSO4.base # Na(+)
b = NaHSO4.residue # HSO4(-)
p = b.base # H(+)
q = b.residue # SO4(2-)
m = q.base # S(6+)
n = q.residue # 4O(2-)

# Таким образом мы последовательно
# разложили соединение на части.
# Это бывает очень полезно при разработке
# реакций разложения, замещения, обмена.

# Также можно добавить соединениям описание.
# Например это необходимо в данной реакции:
# KCl {тв.} + H2SO4 {конц.} -> KHSO4 + HCl

# Если бы условия твердости хлорида и высокой
# концентрации кислоты не выполнялись,
# реакция бы не пошла.

KCl = K(1) & Cl(-1)
KCl = KCl.add_descr('тв.') # I способ
KCl.add_descr_('тв.') # II способ

print(KCl) # KCl{тв.}


# Импортируем класс комплекса
from core import Complex

# Классы Compound и Complex
# очень схожи в функционале

c1 = Complex(Al(3), 4 * OH) # [Al(OH)4]
c2 = Complex(Zn(2), 4 * OH) # [Zn(OH)4]

# Используем комплекс
# в соединениях

p1 = Na(1) & c1 # Na[Al(OH)4]
p2 = 2 * K(1) & c2 # K2[Zn(OH)2]



# Пишем название класса и не забываем в скобках
# указать родительский класс -- Compound.


class Oxide(Compound):
    # Метод сборки оксида; Сюда подается
    # введенный пользователем элемент.
    def config(self, unit):
        # Определение типа оксида: основный,
        # Амфотерный, кислотный или несолеобр.
        self.type = get_base_ctype(unit)

        # Расстановка индексов у эл-та и кислорода
        # Чтобы добиться нулевого заряда соединения.
        # Возвращаем итоговые части соединения.
        return bin_balance(unit, O(-2))


class Acid(Compound):
    # Метод сборки кислоты; Сюда пользователь может
    # разными способами подать кислотный остаток.
    # Например: 
    # 1. Acid(SO4) -- в виде соединения
    # 2. Acid(S(6), 4 * O(-2)) -- как набор составных частей
    def config(self, *args):
        # Восстанавливаем кислотный остаток.
        # Соединяем составные части, если необходимо.
        residue = Compound(*args)
        # Проверяем остаток на корректность заряда
        if residue.charge >= 0:
            raise Exception()
        # Уравниваем кислотный остаток и водород,
        # чтобы итоговый заряд соединения был равен 0.
        # Возвращаем составные части кислоты.
        return bin_balance(H(1), residue)

    # Специальный метод, вызываемый после настройки
    # соединения.
    def _post_init(self):
        # В данном случае с помощью различных баз данных
        # получаем силу и летучесть этой кислоты
        self.strength = acidinfo.get_strength(self)
        self.vol = acidinfo.get_vol(self)

    # Метод, разрешающий диссоциацию кислоты в Н.У.
    def _dissolve_cond(self):
        # В данном случае вердикт зависит от силы кислоты.
        # Для H2SO4 вернет истину, для HF -- ложь
        # (т.к. серная -- сильная кисл., плавиковая -- слабая)
        return acidinfo.is_strong(self)

    # Метод для сравнения силы кислот
    def is_stronger_than(self, other):
        return self.strength > other.strength

    # Метод для сравнения летучести кислот
    def is_more_vol_than(self, other):
        return self.vol > other.vol


from common import *


# Подключаем нужные классы веществ
from classes import *

# Эти классы не требуют от пользователя
# ввода индексов для элементов;
# Они расставляются автоматически.

# Рассмотрим разные классы веществ

# 1. Средние соли

CuCO3 = Salt(Cu(2), CO3) # Карбонат меди (2)
KNO3 = Salt(K(1), NO3) # Нитрат калия

# Можно проверить растворимость солей
s1 = CuCO3.is_soluble # Нет
s2 = KNO3.is_soluble # Да

# Можно также попытаться получить
# продукты диссоциации этих солей

arr1 = KNO3.dissolve() # [K(+), NO3(-)], дисс. прошла
arr2 = CuCO3.dissolve() # [CuCO3(0)], дисс. не прошла

# 2. Кислые и основные соли

salt1 = HydroSalt(Cu(2) & OH, SO4) # (CuOH)2SO4
NaHCO3 = AcidicSalt(Na(1), H(1) & CO3) # Гидрокарбонат натрия

# Их функционал аналогичен средним солям.

# 3. Оксиды

P2O5 = Oxide(P(5)) # Оксид фосфора (5)
Na2O = Oxide(Na(2)) # Оксид натрия
N2O = Oxide(N(1)) # Веселящий газ
TiO2 = Oxide(Ti(4)) # Оксид титана (4)

# Можно определить тип оксида

t1 = P2O5.type # ACIDIC, кислотный
t2 = Na2O.type # BASIC, основный
t3 = N2O.type # NSF, несолеобр.
t4 = TiO2.type # AMPHOTERIC, амфотерный

# 4. Гидроксиды

hydr1 = Hydroxide(Zn(2)) # Zn(OH)2
NaOH = Hydroxide(Na(1)) # едкий натр

# У гидроксидов можно определить тип,
# как и у оксида.

t5 = hydr1.type # AMPHOTERIC, амфотерный
t6 = NaOH.type # BASIC, основный

# Также можно узнать растворимость гидроксида

p1 = hydr1.is_soluble # Нет
p2 = NaOH.is_soluble # Да

# Растворимые гидроксиды диссоциируют

w = NaOH.dissolve() # [Na(+), OH(-)]

# 5. Кислоты

H2SO4 = Acid(SO4) # Серная кислота
H2CO3 = Acid(CO3) # Угольная кислота
HCl = Acid(Cl(-1)) # Хлороводород

# Сильные кислоты диссоциируют

a1 = H2SO4.dissolve() # [2H(+), SO4(2-)]
a2 = H2CO3.dissolve() # [H2CO3(0)]
a3 = HCl.dissolve() # [H(+), Cl(-)]

# Кислоты можно сравнивать между собой по силе

if H2SO4.is_stronger_than(H2CO3): # Да
    pass # код

# Их также можно сравнивать по летучести

if H2SO4.is_more_vol_than(HCl): # Нет
    pass # код

# 6. Простые вещества

H2 = Simple(H) # Водород
Mg = Simple(Mg) # Магний
Na = Simple(Na) # Натрий

# Не диссоциируют.
# Можно проверить Ме/Неме:

m1 = H2.is_metal # Нет
m2 = Mg.is_metal # Да
m3 = Na.is_metal # Да




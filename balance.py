import numpy as np
from toolkit import gcd
from sklearn.linear_model import LinearRegression
from classes import *


def get_unique_el_forms(units):
    d = {}
    for unit in units:
        elements = unit.get_all_elements()
        for el in elements:
            lbl = el.label
            if lbl not in d:
                d[lbl] = set()
            d[lbl].add(el.charge)
    return d


def encode_unit(unit, labels):
    elements = unit.get_all_elements()
    arr = np.zeros((len(labels),))
    for el in elements:
        arr[labels.index(el.label)] += el.coef
    return arr


def encode_group(units, labels):
    return [
        encode_unit(u, labels)
        for u in units
    ]


def make_charge_vector(left, right, diff):
    charge_vector = np.zeros((len(left) + len(right),))
    for i, unit in enumerate(left + right):
        cc = 1 if i < len(left) else -1
        ellist = unit.get_all_elements()
        for el in ellist:
            if el.label not in diff:
                continue
            charge_vector[i] += cc * el.full_charge()
    return charge_vector


def get_coef(x, y):
    model = LinearRegression(fit_intercept=False).fit(x, y)
    score = model.score(x, y)
    if 1 - score > 5e-2:
        raise Exception('Problem with balance.')
    return model.coef_


def rec_f(x, eps=1e-3):
    phi = x - int(x)
    if phi < eps:
        return 1
    beta = 1 / phi
    n = rec_f(beta, eps)
    return n * beta


def make_integer_coef(coef):
    s = set()
    for c in coef:
        mul = rec_f(c)
        s.add(round(mul))
    k = lcm(*list(s))
    return np.round(coef * k).astype('int32')


def apply_coef(units, coef):
    return [u(coef=c) for u, c in zip(units, coef)]


def make_balance(left, right, only_coef=False):
    d = get_unique_el_forms(left + right)
    labels = list(d.keys())
    diff = [k for k in d if len(d[k]) > 1]

    # Составление матрицы количества элементов

    left_enc = encode_group(left, labels)
    right_enc = encode_group(right, labels)
    count_matrix = np.array(left_enc + right_enc)
    count_matrix[len(left_enc):, :] *= -1

    # Составление вектора заряда элементов

    charge_vector = make_charge_vector(left, right, diff)

    # Вспомогательный вектор

    lock_vector = np.zeros_like(charge_vector)
    lock_vector[0] = 1

    # Соединение всего в один обучающий датасет

    x_train = np.concatenate([
        count_matrix.T,
        charge_vector.reshape(1, -1),
        lock_vector.reshape(1, -1)
    ], axis=0)
    y_train = np.zeros((len(x_train),))
    y_train[-1] = 1

    # Тренировка линейной регрессии
    # Получение коээфициентов и домножение
    # чтобы сделать их целыми числами
    
    coef = get_coef(x_train, y_train)
    coef = make_integer_coef(coef)

    if only_coef:
        return coef

    return [apply_coef(left, coef[:len(left)]),
        apply_coef(right, coef[len(left):])]


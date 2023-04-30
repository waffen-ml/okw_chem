import os
from vision import parse
from reacs import *
from balance import make_balance
from random import choice
from server_base import TelegramManager, ScriptFunction


API_KEY = '5862544108:AAG9iti1jjkSiGKPj6BGcTuCN9UrAC6km6g'

fmsg = lambda t: t.replace('\n', ' ')

STARTUP_MSG = fmsg('''
Привет. Я являюсь карманной копией Ильи и в меня
вложены почти все его знания о взаимодействии различных
химических соединений.
''') + '\n\n' + '''/help - Помощь;
/feedback - Обратная связь.'''
HELP_MSG = '\n\n'.join(['Как и обещал, помогу.',
fmsg('''1. Чтобы получить результат протекания химической реакции, достаточно 
ввести ее левую часть без коэффициентов, например: HNO3 + Cu. Иногда
результатов реакции может быть несколько в зависимости от условий проведения
реакции. Обычно калькулятор дает реакциям описание.'''),
fmsg('''2. В случае, если вам нужно провести баланс в химическом уравнении,
следует записать его левую и правую части, поставив между ними стрелку.
Например: Cu + H2SO4 -> CuSO4 + SO2 + H2O.'''),
fmsg('''3. Если вы увидели ошибку в рассуждениях бота или знаете, что можно
еще в него добавить, пишите /feedback и расскажите об этом. Такая
обратная связь мне очень поможет.''')])

phrases = {
    'nothing': [
        'Я не знаю что делать в такой ситуации...',
        'Я такому не научен.',
        'Я не могу сказать, что получится.',
        'Я не уверен в своих догадках.',
        'Не могу ответить...',
        'Не знаю ответ.',
        'Я не могу это решить...'
    ],
    'error': [
        'Произошла ошибка!',
        'Случилась ошибка!',
        'В вычислении произошла ошибка.',
        'Ошибка! Без них не обходится.',
        'У меня не получилось посчитать! Ошибка!'
    ]
}


def parse_sum(text):
    return [parse(o.strip()) for o in text.split('+')]


def random_phrase(cat):
    return choice(phrases[cat])


def send_phrase(cat, func):
    func(random_phrase(cat))


def append_feedback(text):
    with open('feedback.txt', '+a', encoding='utf8') as f:
        f.write('[UNIT] ' + fmsg(text) + '\n')


class MainFunc:
    def make_coef(self, text, func):
        left_s, right_s = text.split('->')
        left = parse_sum(left_s)
        right = parse_sum(right_s)
        left_b, right_b = make_balance(left, right)
        eq = Equation(left_b, right_b)
        func(f'Итоговое уравнение:\n{eq}')

    def make_reac(self, text, func):
        objs = parse_sum(text)
        #print([(o, type(o)) for o in objs])
        result = rcore(*objs)
        if not result:
            send_phrase('nothing', func)
            return
        if len(result) == 1:
            func('Вот нужная реакция:')
        else:
            func('Получилось несколько возможных реакций:')
        for r in result:
            func(r.describe())

    def step(self, text, func):
        if '->' in text:
            self.make_coef(text, func)
        else:
            self.make_reac(text, func)

    def __call__(self, text, func):
        try:
            self.step(text, func)
        except Exception as ex:
            send_phrase('error', func)
            raise ex


class Engine:
    @ScriptFunction('f1', '/start')
    def on_start(self, _):
        self.send_message(STARTUP_MSG)

    @ScriptFunction('f2_1', '/feedback')
    def on_feedback(self, _):
        self.send_message('Выскажите мне свои мысли')
        return 'f2_2'

    @ScriptFunction('f2_2')
    def feedback_done(self, text):
        self.send_message('Спасибо! Ваше мнение '
                          'поможет улучшить проект.')
        append_feedback(text)

    @ScriptFunction('f3', 'default')
    def on_default(self, text):
        mf = MainFunc()
        mf(text, self.wrap_send())
    
    @ScriptFunction('f4', '/help')
    def on_start(self, _):
        self.send_message(HELP_MSG)


mgr = TelegramManager(API_KEY, Engine())






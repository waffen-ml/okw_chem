import telebot
from vision import parse
from reacs import *
from balance import make_balance
from random import choice


API_KEY = '5862544108:AAG9iti1jjkSiGKPj6BGcTuCN9UrAC6km6g'
bot = telebot.TeleBot(API_KEY)


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


def send(msg, id):
    print('SENDING', msg, 'TO', id)
    bot.send_message(id, msg)


def send_phrase(set_name, id):
    send(choice(phrases[set_name]), id)


def make_coef(text, user_id):
    left_s, right_s = text.split('->')
    left = parse_sum(left_s)
    right = parse_sum(right_s)
    left_b, right_b = make_balance(left, right)
    eq = Equation(left_b, right_b)
    send(f'Итоговое уравнение:\n{eq}', user_id)


def make_reac(text, user_id):
    objs = parse_sum(text)
    #print([(o, type(o)) for o in objs])
    result = rcore(*objs)
    if not result:
        send_phrase('nothing', user_id)
        return
    if len(result) == 1:
        send('Вот нужная реакция:', user_id)
    else:
        send('Получилось несколько возможных реакций:', user_id)
    for r in result:
        send(r.describe(), user_id)


def step(text, user_id):
    if '->' in text:
        make_coef(text, user_id)
    else:
        make_reac(text, user_id)


@bot.message_handler(content_types=['text'])
def new_message(msg):
    text = msg.text
    user_id = msg.from_user.id

    print(f'NEW MESSAGE FROM USER {user_id}:', text)

    try:
        step(text, user_id)
    except Exception as ex:
        send_phrase('error', user_id)
        raise ex





bot.infinity_polling()



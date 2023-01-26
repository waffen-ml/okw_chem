import telebot
from parsing import *
from reac import *
from bot_data import *
#from vision import vision
from balance import make_balance


API_KEY = '5862544108:AAG9iti1jjkSiGKPj6BGcTuCN9UrAC6km6g'
bot = telebot.TeleBot(API_KEY)


def parse_sum(text):
    return [parse(o.strip()) for o in text.split('+')]


def send(msg, id):
    bot.send_message(id, msg)


def make_coef(text, user_id):
    left_s, right_s = text.split('->')
    left = parse_sum(left_s)
    right = parse_sum(right_s)
    left_b, right_b = make_balance(left, right)
    eq = Equation(left_b, right_b)
    send(f'Итоговое уравнение:\n{eq}', user_id)


def make_reac(text, user_id):
    objs = parse_sum(text)
    result = rcore(*objs)
    if not result:
        send('Я не могу это решить...', user_id)
        return
    if len(result) == 1:
        send('Вот нужная реакция:', user_id)
    else:
        send('Получилось несколько возможных реакций:', user_id)
    for r in result:
        send(r.describe(), user_id)


@bot.message_handler(content_types=['text'])
def new_message(msg):
    text = msg.text
    user_id = msg.from_user.id

    if '->' in text:
        make_coef(text, user_id)
    else:
        make_reac(text, user_id)


bot.infinity_polling()



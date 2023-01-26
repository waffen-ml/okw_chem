import telebot
from telebot import types
from parsing import *
from reac import *
from shell import shell_run
from bot_data import *


API_KEY = '5862544108:AAG9iti1jjkSiGKPj6BGcTuCN9UrAC6km6g'
SHELL_PASSWORD = 'dick_shell'
bot = telebot.TeleBot(API_KEY)


class scriptfunc:
    def __init__(self, name, command):
        self.name = name
        self.command = command

    def past_init(self, func):
        self.func = func
        return self

    def __call__(self, *args):
        return self.func(*args)


def ScriptFunction(name, command=None):
    sf = scriptfunc(name, command)
    return sf.past_init


class UserHandler:
    def __init__(self, user_id):
        self.user_id = user_id
        self.script = None
        self.markup = None
        self.funcs = {
            f.name: f for m in dir(self)
            if type(f := getattr(self, m)) == scriptfunc
        }

    def is_busy(self):
        return self.script is not None

    def send_message(self, text, markup=None):
        if markup is not None:
            mk_obj = types.ReplyKeyboardMarkup(
                row_width=2,
                resize_keyboard=True,
                one_time_keyboard=True
            )
            for k in markup:
                button = types.KeyboardButton(text=k)
                mk_obj.add(button)
        else:
            mk_obj = types.ReplyKeyboardRemove()
        self.markup = markup
        bot.send_message(self.user_id, text, reply_markup=mk_obj)

    def call_func(self, name, content=None):
        func = self.funcs[name]
        self.script = func(self, content)

    def parse(self, text):
        for f in self.funcs.values():
            if f.command != text:
                continue
            self.call_func(f.name)

    def forward(self, text):
        if self.markup is not None:
            text = self.markup[text]
            self.markup = None
        if not self.is_busy():
            return self.parse(text)
        self.call_func(self.script, text)
    
    @ScriptFunction('start', '/start')
    def start(self, _):
        self.send_message(construct_main_menu(), {
            'Проведение реакций': '/calc_reac'
        })

    @ScriptFunction('calc_reac_input', '/calc_reac')
    def calc_reac_input(self, _):
        self.send_message('Введи реагенты, как показано ниже:\n\nAl2O3 + KOH')
        return 'calc_reac_main'

    @ScriptFunction('calc_reac_main')
    def calc_reac_main(self, reac):
        objs = [parse(o) for o in reac.split() if o != '+']
        result = rcore(*objs)
        if not result:
            self.send_message('Я не могу это решить...')
            return
        if len(result) == 1:
            self.send_message('Вот нужная реакция:')
        else:
            self.send_message('Получилось несколько возможных реакций:')
        for r in result:
            self.send_message(r.describe())
        return 'calc_reac_main'
        
    @ScriptFunction('shell_input', '/shell')
    def shell_input(self, _):
        self.send_message('Введите пароль')
        return 'shell_password'

    @ScriptFunction('shell_password')
    def shell_password(self, password):
        if password == SHELL_PASSWORD:
            self.send_message('Пароль верный! Теперь вы имеете доступ к оболочке.')
            return 'shell_main'
        self.send_message('Пароль неверный!')

    @ScriptFunction('shell_main')
    def shell_main(self, inp):
        if inp == '!exit_shell':
            self.send_message('Closing shell...')
            return
        output = shell_run(inp)
        if output is not None:
            self.send_message(str(output))
        return 'shell_main'


handlers = {}


def get_user_handler(user_id):
    if user_id not in handlers:
        handlers[user_id] = UserHandler(user_id)
    return handlers[user_id]


@bot.message_handler(content_types=['text'])
def new_message(msg):
    handler = get_user_handler(msg.from_user.id)
    handler.forward(msg.text)

@bot.callback_query_handler(func=lambda cb: cb.data)
def new_callback_data(callback):
    cmd = callback.data
    print(cmd)


# infantry polling
bot.infinity_polling()



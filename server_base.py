import telebot
from telebot import types


class scriptfunc:
  def __init__(self, name, command=None):
    self.name = name
    self.command = command

  def is_default(self):
    return self.command == 'default'

  def past_init(self, func):
    self.func = func
    return self

  def __call__(self, *args):
    return self.func(*args)


def ScriptFunction(name, command=None):
  sf = scriptfunc(name, command)
  return sf.past_init


class User:
  def __init__(self, user_id, mgr):
    self.user_id = user_id
    self.script = None
    self.markup = None
    self.mgr = mgr

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
    self.mgr.bot.send_message(self.user_id, text, reply_markup=mk_obj)

  def call_func(self, name, content=None):
    func = self.mgr.funcs[name]
    self.script = func(self, content)

  def parse(self, text):
    name = ''
    for f in self.mgr.funcs.values():
      if f.is_default():
        name = f.name
        continue
      elif f.command == text:
        name = f.name
        break
    if not name:
      return
    self.call_func(name, text)

  def wrap_send(self):
    def x(text, markup=None):
      self.send_message(text, markup)
    return x

  def forward(self, text):
    if self.markup is not None:
      text = self.markup[text] if type(self.markup) == dict else text
      self.markup = None
    if not self.is_busy():
      return self.parse(text)
    self.call_func(self.script, text)


class TelegramManager:
  def __init__(self, token, engine):
    self.bot = telebot.TeleBot(token)
    self.users = {}
    self.funcs = {f.name: f for m in dir(engine)
      if type(f := getattr(engine, m)) == scriptfunc
    }
    
    @self.bot.message_handler(content_types=['text'])
    def new_msg_wrapper(msg):
      self.new_message(msg)

    self.bot.infinity_polling()

  def get_user(self, user_id):
    if user_id not in self.users:
      self.users[user_id] = User(user_id, self)
    return self.users[user_id]

  def new_message(self, msg):
    handler = self.get_user(msg.from_user.id)
    handler.forward(msg.text)
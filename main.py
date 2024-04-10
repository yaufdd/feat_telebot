import telebot
import redis
import requests

from sbt_json import test_json

r = redis.Redis(host='localhost', port=6379, db=0)

bot = telebot.TeleBot('7128882313:AAHlbCt3AtnbkYpzqWinVYkH71GqKOT6n1k')

def is_adress_not_unique(cur_address):
    has_duplicates = False
    cursor = 0
    while True:
        cursor, keys = r.scan(cursor=cursor, match='user:*')
        for key in keys:
            value = r.hget(key, 'ton_address')
            if str(cur_address).encode() == value:
                print(f"Найден дубликат: {value}")
                has_duplicates = True
                break
        if cursor == 0 or has_duplicates:
            break
    if not has_duplicates:
        print("Дубликаты не найдены.")
    return has_duplicates

user_states = {}
def set_user_state(user_id, state):
    global user_states
    user_states[user_id] = state

def get_user_state(user_id):
    return user_states.get(user_id, None)

def request_post(url, data):
    responce = requests.post(url, data=data)
    return responce

def mint_request(url, data):
    mint_responce = requests.post(url, data=data)
    return mint_responce

def is_sbt_exist(json_data):
    if 'sbt_connected' in json_data and json_data['sbt_connected']:
        return True
    else:
        return False
    
def get_sbt_data(url, ton_address):
    responce = requests.get(url, data=ton_address)
    jsoned_data = responce.json()

    return jsoned_data



def check_sbt(sbt_json, message):
    if is_sbt_exist(sbt_json):
        if 'revoked' in sbt_json and sbt_json['revoked']:
            try:
                chat_id = -4120754132
                invite_link = bot.export_chat_invite_link(chat_id)
                bot.send_message(message.chat.id, invite_link)
            except Exception as e:
                bot.send_message(chat_id, "Произошла ошибка при генерации ссылки.")
                print(e)
        else:
            bot.send_message(message.chat.id, 'Твой sbt отозван')
    else:
        if 'status' in sbt_json and sbt_json['status'] == 'requested':
            bot.send_message(message.chat.id, 'Ваш sbt запрошен\n/help\n/sbt_status')
            r.hset(user_key, mapping={'sbt_status' : sbt_json['status']})
            
        elif 'status' in sbt_json and sbt_json['status'] == 'none':
            r.hset(user_key, mapping={'sbt_status' : sbt_json['status']})
            bot.send_message(message.chat.id, "Выпуск SBT запрошен, как только будет готово - придет уведомление")
            #mint_request('url', data)
            print("mint request sent to server.")
            r.hset(user_key, mapping={'sbt_status' : sbt_json['status']})

        elif 'status' in sbt_json and sbt_json['status'] == 'minted':
            bot.send_message(message.chat.id, 'SBT на авторизованном кошельке отсуствует \n/ Связаться с поддержкой - /help\n Авторизоваться через другой кошелек - /auth_wallet')
            r.hset(user_key, mapping={'sbt_status' : sbt_json['status']})


@bot.message_handler(commands=['start'])
def start(message):
    global tg_id
    #tg_id = 18
    tg_id = message.from_user.id
    print(tg_id)

    global user_key
    user_key = f"user:{tg_id}" # Найти пользователя по TGID

    global role
    role = r.hget(user_key, 'role')

    if r.hget(user_key, 'is_incollective') == "0".encode(): # Пользователь состоит в FEAT COLLECTIVE ?
        bot.send_message(message.chat.id, """Список команд \n /telegram_id  - получить мой Telegram ID\n /feat_collective - Как попасть в FEAT Collective""")
    else:
        if role == "admin".encode() or role == "team".encode(): # Проверить роль пользователя
            bot.send_message(message.chat.id, "Список команд \n /telegram_id  - получить мой Telegram ID\n /join_group - Попасть в группу\n /add_user - Добавить пользователя")
        elif role == "artist".encode() or role == "user".encode(): # Проверить роль пользователя
            ton_address = r.hget(user_key, 'ton_address') 
            if ton_address is None: # Проверить привязан ли кошелек к Telegram
                bot.send_message(message.chat.id, "Отправьте мне адрес вашего тон кошелька")
                set_user_state(tg_id, 'awaiting_ton_address')
                
            else:
                data = {tg_id : ton_address}
                print(data)
                #request_post("url", data)

                #sbt_json = get_sbt_data()
                global sbt_json
                sbt_json = test_json
                check_sbt(sbt_json, message)
        else:
            bot.send_message(message.chat.id, """Список команд \n /telegram_id  - получить мой Telegram ID\n /feat_collective - Как попасть в FEAT Collective""")


@bot.message_handler(commands=['telegram_id'])
def get_tg_id(message):
    bot.send_message(message.chat.id, message.from_user.id)

@bot.message_handler(commands=['feat_collective '])
def get_tg_id(message):
    bot.send_message(message.chat.id, "В группу попадаешь вот так ")

@bot.message_handler(commands=['help'])
def get_tg_id(message):
    bot.send_message(message.chat.id, "Связываем с поддержкой")

@bot.message_handler(commands=['sbt_status'])
def get_tg_id(message):
    check_sbt(sbt_json, message)

@bot.message_handler(commands=['auth_wallet'])
def auth_with_wallet(message):
    r.hdel(f'user:{tg_id}','ton_address')
    bot.send_message(message.chat.id, "Отправьте мне адрес вашего тон кошелька")
    set_user_state(tg_id, 'awaiting_ton_address')




@bot.message_handler(func=lambda message: get_user_state(tg_id) == 'awaiting_ton_address')
def handle_message(message):
        sent_ton_address = message.text
        if is_adress_not_unique(sent_ton_address):
            bot.send_message(message.chat.id, "Этот адресс уже используется используйте другой")
        else:
            set_user_state(tg_id, None)
            r.hset(user_key, mapping={'role' : role, 'ton_address' : sent_ton_address})
            bot.reply_to(message, "Адрес вашего тон кошелька сохранен! Введите /start для продолжения или выберите другую команду.")

bot.polling(True)





#commands list :
# /telegram_id
# /feat_collective

import bot_token
import telebot
import time
import ast
import random
import threading
import sys
from telebot import util
from datetime import datetime
import bot_constant as const

known_users = []
user_error = []
global data
data = {}
not_understand = ['Что-то я тебя не пойму никак...', 'Ты серьезно???', 'Ты хорошо подумал???', 'Не шути так, братанчик']

try:
    with open('bot_users.txt', 'r')as f:
        known_users = [int(user) for user in f.read().split('\n')]
    with open('bot_error.txt', 'r')as f:
        text_file = f.read()
        if len(text_file) > 1:
            user_error = [int(user) for user in text_file.split('\n')]
        else:
            user_error = []
except FileNotFoundError:
    pass


def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            text_mes = str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text
            # send the sent message to admin( me:) )
            if m.chat.id != bot_token.myChatId:
                bot.send_message(bot_token.myChatId, text_mes)
                try:
                    with open('bot_listener.log', 'a')as f:
                        f.write(text_mes + '\n')
                except UnicodeEncodeError:
                    pass


bot = telebot.TeleBot(bot_token.token, threaded=False)
bot.set_update_listener(listener)  # register listener
keyboard = telebot.types.ReplyKeyboardMarkup(True)
keyboard.row('/status all', '/value all', '/errors on', '/errors off')

# t = threading.Thread(target=bot.polling, kwargs={'none_stop': True, 'interval': 5, 'timeout': 30})

@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    if cid not in known_users:  # if user hasn't used the "/start" command yet:
        known_users.append(cid)  # save user id, so you could brodcast messages to all users of this bot later
        str_known_users = ([str(user) for user in known_users])
        with  open('bot_users.txt', 'w')as f:
            f.write('\n'.join(str_known_users))
        bot.send_message(cid, "Приветствую тебя, прямоходящий....")
        time.sleep(2)
        bot.send_message(cid, f"Я метео бот, а ты походу {m.chat.first_name}")
        time.sleep(2)
        bot.send_message(cid, "Я тебя запомнил...")
        time.sleep(3)
        command_help(m)  # show the new user the help page
    else:
        bot.send_message(cid, f"{m.chat.first_name}, мы с тобой уже знакомы, нет смысла знакомиться повторно!")


@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "На данный момент доступны следующие команды: \n"
    for key in const.help:  # generate help text out of the commands dictionary defined at the top
        help_text += key + ": "
        help_text += const.help[key].expandtabs() + "\n"
    bot.send_message(cid, help_text)  # send the generated help page


@bot.message_handler(commands=['sendmes'])
def send_message_to(m):
    try:
        user = m.text.split()[1]
        message = m.text.split()[2:]
        answer = ''
        for text in message:
            answer += text + ' '
        if user.upper() == 'ALL':
            with open('bot_users.txt', 'r')as f:
                for user in f.read().split('\n'):
                    bot.send_message(int(user), answer)
        else:
            bot.send_message(int(user), answer)
    except Exception:
        writeLog('send_message_to ' + str(sys.exc_info()))


@bot.message_handler(commands=['status'])
def botStatus(m):
    global data
    cid = m.chat.id
    try:
        status = data['status']
        text = m.text.split()
        sens = text[1].upper()
        answer = 'Сообщение о статусе:\n\n'
        if sens == 'ALL':
            for s, v in status.items():
                answer += v + '\n'
            bot.send_message(cid, util.split_string(answer, 3000))
        elif sens == 'SENSORS':
            l = []
            for s in status.keys():
                l.append(s)
            bot.send_message(cid, f"Список доступных датчиков\n {'  '.join(l)}")
        else:
            try:
                answer += status[sens]
                bot.send_message(cid, answer)
            except KeyError:
                writeLog('botStatus ' + str(sys.exc_info()))
                bot.send_message(cid, "Введите правильное имя датчика ")
    except Exception:
        writeLog('botStatus ' + str(sys.exc_info()))
        bot.send_message(cid, "Проверьте введенную команду ")


@bot.message_handler(commands=['value'])
def botValue(m):
    global data
    cid = m.chat.id
    try:
        value = data['value']
        text = m.text.split()
        sens = text[1].upper()
        answer = 'Сообщение со значениями:\n\n'
        if sens == 'ALL':
            for s, v in value.items():
                answer += s + '  ' + v + '\n'
            bot.send_message(cid, util.split_string(answer, 3000))
        elif sens == 'SENSORS':
            l = []
            for s in value.keys():
                l.append(s)
            bot.send_message(cid, f"Список доступных датчиков\n {'  '.join(l)}")
        else:
            try:
                answer += value[sens]
                bot.send_message(cid, answer)
            except KeyError:
                writeLog('botValue ' + str(sys.exc_info()))
                bot.send_message(cid, "Введите правильное имя датчика ")
    except Exception:
        writeLog('botValue ' + str(sys.exc_info()))
        bot.send_message(cid, "Проверьте введенную команду ")


@bot.message_handler(commands=['errors'])
def botErrors(m):
    cid = m.chat.id
    try:
        state = m.text.split()[1].upper()
        if state == 'ON':
            if cid not in user_error:
                user_error.append(cid)
                str_user_error = [str(user) for user in user_error]
                with open('bot_error.txt', 'w')as f:
                    f.write('\n'.join(str_user_error))
                bot.send_message(cid, 'Подключаю уведомление об ошибках')
            elif cid in user_error:
                bot.send_message(cid, 'Уведомление об ошибках уже подключено')
        elif state == 'OFF':
            if cid in user_error:
                user_error.remove(cid)
                str_user_error = [str(user) for user in user_error]
                with open('bot_error.txt', 'w')as f:
                    f.write('\n'.join(str_user_error))
                bot.send_message(cid, 'Отключил уведомление об ошибках')
            else:
                bot.send_message(cid, 'Уведомление об ошибках уже отключено')
    except Exception as e:
        writeLog('botErrors ' + str(sys.exc_info()))


@bot.message_handler(content_types=['text'])
def botMessage(m):
    global data
    cid = m.chat.id
    if m.text.upper() == 'PING':
        bot.send_message(cid, "Я на месте и в полной боевой готовности!!!", reply_markup=keyboard)
    if cid == bot_token.myChatId:
        if m.text.upper() == 'USERS KNOWN':
            users = ''
            for user in known_users:
                users += str(user) + '\n'
            bot.send_message(cid, users)
        elif m.text.upper() == 'LISTENER':
            listener_log = open('bot_listener.log', 'r').read()
            splited_listener_log = util.split_string(listener_log, 3000)
            if len(splited_listener_log) < 1:
                bot.send_message(bot_token.myChatId, 'File is empty')
            else:
                for text in splited_listener_log:
                    bot.send_message(bot_token.myChatId, text)
        elif m.text.upper() == 'LISTENER CLEAR':
            open('bot_listener.log', 'w').write('listener log')
            bot.send_message(bot_token.myChatId, 'LISTENER CLEARED')
        elif m.text.upper() == 'LOG':
            try:
                with open('bot.log', 'r')as f:
                    log = f.read()
                    splited_log = util.split_string(log, 3000)
                bot.send_message(bot_token.myChatId, splited_log)
            except Exception as e:
                writeLog(e)
        elif m.text.upper() == 'LOG CLEAR':
            open('bot.log', 'w').write('bot log')
            bot.send_message(bot_token.myChatId, 'LOG CLEARED')
        elif m.text.upper() == 'USERS ERROR':
            users = ''
            for user in user_error:
                users += str(user) + '\n'
            bot.send_message(cid, users)
        elif m.text.upper() == 'GET DATAFILE':
            with open('bot_data.txt', 'rb')as f:
                answer = f.read()
            bot.send_message(bot_token.myChatId, answer)
        elif m.text.upper() == 'GET DATA':
            answer = ''
            for n in data:
                V = data[n]
                for k, v in V.items():
                    answer += f"'{k}': '{v}', "
            bot.send_message(bot_token.myChatId, util.split_string(answer, 3000))
    else:
        bot.send_message(cid, random.choice(not_understand))

def writeLog(e):
    time_now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    with open('bot.log', 'a')as f:
        f.write('\n' + time_now + ' ' + str(e))

def readDB():
    global data
    while True:
        data = {}
        with open('bot_data.txt', 'r')as f:
            data = f.read()
            data = ast.literal_eval(data)
            errors = data['error']
            sensors = []
            for sens, error in errors.items():
                if error == 1 or error == 2:
                    sensors.append(sens)
            if len(sensors) >= 1:
                if len(user_error) >= 1:
                    for user in user_error:
                        answer = 'Ошибка или сбой:\n' + '\n'.join(sensors)
                        bot.send_message(user, answer)
        time.sleep(5)


t1 = threading.Thread(target=readDB)
t1.start()

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception:
            writeLog('main ' + str(sys.exc_info()))
            time.sleep(3)

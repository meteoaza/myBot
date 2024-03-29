from shutil import copyfile
from gtts import gTTS
import speech_recognition as sr
import bot_token
import telebot
import requests
import time
import random
import threading
import sys
import os
import json
from pullATIS import getAtisFile
from stat import ST_MTIME
from telebot import util
from datetime import datetime
from bs4 import BeautifulSoup
import bot_constant as const
import subprocess as sp

known_users = []
user_error = []
not_understand = ['Что-то я тебя не пойму никак...', 'Ты серьезно???', 'Ты хорошо подумал???', 'Не шути так, братанчик']

if not os.path.exists('DATA'):
    os.mkdir('DATA')
if not os.path.exists('DATA/USERDATA'):
    os.mkdir('DATA/USERDATA')
try:
    with open(const.bot_path + 'bot_users.txt', 'r')as f:
        known_users = [int(user) for user in f.read().split('\n')]
    with open(const.bot_path + 'bot_error.txt', 'r')as f:
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
                    with open(const.bot_path + 'bot_listener.log', 'a')as f:
                        f.write(text_mes + '\n')
                except UnicodeEncodeError:
                    pass


bot = telebot.TeleBot(bot_token.token, threaded=False)
bot.set_update_listener(listener)  # register listener
keyboard = telebot.types.ReplyKeyboardMarkup(True, False)
keyboard.row('/status all', '/value all', '/errors on', '/errors off', '/atis')


@bot.message_handler(commands=['start', 'help', 'status', 'value', 'errors', 'atis', 'sendmes'])
def botCommander(m):
    global data
    cid = m.chat.id
    if '/start' in m.text:
        if cid not in known_users:  # if user hasn't used the "/start" command yet:
            known_users.append(cid)  # save user id, so you could brodcast messages to all users of this bot later
            str_known_users = ([str(user) for user in known_users])
            with  open(const.bot_path + 'bot_users.txt', 'w')as f:
                f.write('\n'.join(str_known_users))
            bot.send_message(cid, "Приветствую тебя, прямоходящий....")
            time.sleep(2)
            bot.send_message(cid, f"Я метео бот, а ты походу {m.chat.first_name}")
            time.sleep(2)
            bot.send_message(cid, "Я тебя запомнил...", reply_markup=keyboard)
            time.sleep(3)
            bot.send_message(cid, 'Набери /help для вызова списка командд')
        else:
            bot.send_message(cid, f"{m.chat.first_name}, мы с тобой уже знакомы, нет смысла знакомиться повторно!",
                             reply_markup=keyboard)

    elif '/help' in m.text:
        help_text = "На данный момент доступны следующие команды: \n"
        for key in const.help:  # generate help text out of the commands dictionary defined at the top
            help_text += key + ": "
            help_text += const.help[key].expandtabs() + "\n"
        bot.send_message(cid, help_text)  # send the generated help page

    elif '/status' in m.text:
        try:
            status = data['status']
            text = m.text.split()
            sens = text[1].upper()
            answer = f'Сообщение о статусе:\n{file_time}\n\n'
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
                answer += status[sens]
                bot.send_message(cid, answer)
        except Exception:
            writeLog('botStatus ' + str(sys.exc_info()))
            bot.send_message(cid, "Что-то пошло не так... ")

    elif '/value' in m.text:
        try:
            value = data['value']
            text = m.text.split()
            sens = text[1].upper()
            answer = f'Сообщение со значениями:\n{file_time}\n\n'
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
                answer += value[sens]
                bot.send_message(cid, answer)
        except Exception:
            writeLog('botValue ' + str(sys.exc_info()))
            bot.send_message(cid, "Что-то пошло не так... ")

    elif '/errors' in m.text:
        try:
            state = m.text.split()[1].upper()
            if state == 'ON':
                if cid not in user_error:
                    user_error.append(cid)
                    str_user_error = [str(user) for user in user_error]
                    with open(const.bot_path + 'bot_error.txt', 'w')as f:
                        f.write('\n'.join(str_user_error))
                    bot.send_message(cid, 'Подключаю уведомление об ошибках')
                elif cid in user_error:
                    bot.send_message(cid, 'Уведомление об ошибках уже подключено')
            elif state == 'OFF':
                if cid in user_error:
                    user_error.remove(cid)
                    str_user_error = [str(user) for user in user_error]
                    with open(const.bot_path + 'bot_error.txt', 'w')as f:
                        f.write('\n'.join(str_user_error))
                    bot.send_message(cid, 'Отключил уведомление об ошибках')
                else:
                    bot.send_message(cid, 'Уведомление об ошибках уже отключено')
        except Exception:
            writeLog('botErrors ' + str(sys.exc_info()))

    elif '/atis' in m.text:
        try:
            atis_file_name = getAtisFile()
            with open(atis_file_name, 'r')as f:
                atis_file_text = f.read()
            bot.send_message(cid, atis_file_text)
            textToVoice(cid, atis_file_text, m.chat.first_name, 'en')
        except Exception:
            writeLog('atis' + str(sys.exc_info()))

    elif '/sendmes' in m.text:
        try:
            user = m.text.split()[1]
            message = m.text.split()[2:]
            answer = ''
            for text in message:
                answer += text + ' '
            if user.upper() == 'ALL':
                with open(const.bot_path + 'bot_users.txt', 'r')as f:
                    for user in f.read().split('\n'):
                        bot.send_message(int(user), answer)
            else:
                bot.send_message(int(user), answer)
        except Exception:
            writeLog('send_message_to ' + str(sys.exc_info()))


@bot.message_handler(content_types=['text'])
def getTextMessage(m):
    global data
    cid = m.chat.id
    if m.text.upper() == 'PING':
        bot.send_message(cid, "Я на месте и в полной боевой готовности!!!")
    if cid == bot_token.myChatId:
        if m.text.upper() == 'USERS KNOWN':
            users = ''
            for user in known_users:
                users += str(user) + '\n'
            bot.send_message(cid, users)
        elif m.text.upper() == 'LISTENER':
            with open(const.bot_path + 'bot_listener.log', 'r')as f:
                listener_log = f.read()
            splited_listener_log = util.split_string(listener_log, 3000)
            if len(splited_listener_log) < 1:
                bot.send_message(bot_token.myChatId, 'File is empty')
            else:
                for text in splited_listener_log:
                    bot.send_message(bot_token.myChatId, text)
        elif m.text.upper() == 'LISTENER CLEAR':
            with open(const.bot_path + 'bot_listener.log', 'w')as f:
                f.write('listener log')
            bot.send_message(bot_token.myChatId, 'LISTENER CLEARED')
        elif m.text.upper() == 'LOG':
            try:
                with open(const.bot_path + 'bot.log', 'r')as f:
                    log = f.read()
                    splited_log = util.split_string(log, 3000)
                bot.send_message(bot_token.myChatId, splited_log)
            except FileNotFoundError:
                with open(const.bot_path + 'bot.log', 'w')as f:
                    f.write('Bot log')
            except Exception:
                writeLog('getTextMessage ' + str(sys.exc_info()))
        elif m.text.upper() == 'LOG CLEAR':
            open(const.bot_path + 'bot.log', 'w').write('bot log')
            bot.send_message(bot_token.myChatId, 'LOG CLEARED')
        elif m.text.upper() == 'USERS ERROR':
            users = ''
            for user in user_error:
                users += str(user) + '\n'
            bot.send_message(cid, users)
        elif m.text.upper() == 'GET DATAFILE':
            with open(const.data_path, 'r')as f:
                answer = f.read()
            bot.send_message(bot_token.myChatId, answer)
        elif m.text.upper() == 'GET DATA':
            answer = ''
            for n in data:
                V = data[n]
                for k, v in V.items():
                    answer += f"'{k}': '{v}', "
            bot.send_message(bot_token.myChatId, util.split_string(answer, 3000))
        elif m.text.upper() == 'GET IP':
            html = requests.get('http://ifconfig.co')
            html.encoding = '1251'
            soup = BeautifulSoup(html.text, 'html.parser')
            ip = soup.find('code', {'class': 'ip'})
            bot.send_message(cid, ip.text)
    else:
        bot.send_message(cid, random.choice(not_understand))


@bot.message_handler(content_types=['voice'])
def getVoiceMessage(m):
    cid = m.chat.id
    src_filename = const.bot_path + 'voice_src.ogg'
    dst_filename = const.bot_path + 'voice_dst.wav'
    try:
        os.remove(src_filename)
        os.remove(dst_filename)
    except FileNotFoundError:
        pass
    file_info = bot.get_file(m.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(src_filename, 'wb') as new_file:
        new_file.write(downloaded_file)
    process = sp.run(['ffmpeg', '-i', src_filename, dst_filename])
    if process.returncode != 0:
        raise Exception(bot.send_message(cid, 'Случилась какая-то жопа...'))
    bot.send_message(cid, 'Занимаюсь обработкой...минуту..')
    name = m.chat.first_name
    r = sr.Recognizer()
    audio_file = sr.AudioFile(dst_filename)
    with audio_file as source:
        audio = r.listen(source)
    text = r.recognize_google(audio, language='ru')
    if cid != bot_token.myChatId:
        bot.send_message(bot_token.myChatId, m.chat.first_name + ' :' + text)
        tm = datetime.now().strftime('%d%m%H%M%S')
        copyfile(dst_filename, const.bot_path + 'USERDATA/{}_{}.wav'.format(name, tm))
    if 'РАССКАЖИ АНЕКДОТ' in text.upper() or 'АНЕКДОТ РАССКАЖИ' in text.upper():
        bot.send_message(cid, 'Щас расскажу. Дай вспомню, не торопи...')
        try:
            html = requests.get('http://anekdotme.ru/random')
            html.encoding = '1251'
            writeLog('anekdot : ' + str(html))
            soup = BeautifulSoup(html.text, 'html.parser')
            soup_text = soup.find_all('div', {'class': 'anekdot_text'})
            n_random = len(soup_text)
            n = random.randint(0, n_random)
            a = soup_text[n]
            anekdot = a.text.strip()
            if 'ГОЛОСОМ' in text.upper():
                textToVoice(cid, anekdot, m.chat.first_name, 'ru')
            else:
                bot.send_message(cid, anekdot)
        except Exception:
            writeLog('anekdot' + str(sys.exc_info()))
            bot.send_message(cid, 'Чет не вспомню ни хера.. Сорян')
    elif 'ГРАФИК РАБОТЫ' in text.upper():
        bot.send_message(cid, 'Встречай график работы! Смотри не проспи свою смену)))')
        sendShedule(cid)
    elif 'ГОЛОСОВОЕ ВЕЩАНИЕ' in text.upper():
        atis_file_name = getAtisFile()
        with open(atis_file_name, 'r')as f:
            atis_file_text = f.read()
        bot.send_message(cid, atis_file_text)
        textToVoice(cid, atis_file_text, m.chat.first_name, 'en')
    else:
        bot.send_message(cid, 'Что значит твое ' + text + '???')


def textToVoice(cid, text, user, lang):
    snd = gTTS(text=str(text), lang=lang)
    file_name = const.bot_path + 'voice.mp3'
    snd.save(file_name)
    bot.send_message(cid, f'Почти готово, {user}. Высылаю файл...')
    with open(file_name, 'rb')as sound:
        bot.send_audio(cid, sound)
    os.remove(file_name)


def playMusic():
    pass


def sendShedule(cid):
    file_name = const.bot_path + 'graf.jpg'
    with open(file_name, 'rb')as pic:
        bot.send_photo(cid, pic)


def writeLog(e):
    time_now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    with open(const.bot_path + 'bot.log', 'a')as f:
        f.write('\n' + time_now + ' ' + str(e))


def readDB():
    global data, file_time
    while True:
        data = {}
        try:
            st = os.stat(const.data_path)
            file_time = datetime.fromtimestamp(st[ST_MTIME])
            data = json.load(open(const.data_path))
            status = data['status']
            errors = data['error']
            sensors = []
            for sens, error in errors.items():
                if error == 1 or error == 2:
                    sensors.append(status[sens])
            if len(sensors) >= 1:
                if len(user_error) >= 1:
                    for user in user_error:
                        answer = '\n'.join(sensors)
                        bot.send_message(user, answer)
        except Exception:
            writeLog('readDB' + str(sys.exc_info()))
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

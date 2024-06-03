# import requests
#TOKEN = "7019968682:AAGvOMxDxPLV9Y33TagpSXTexMDws1SNxzU"
#chat_id = "1011425465"
#message = "Вы записаны на 19:00"
#url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
#print(requests.get(url).json()) # Эта строка отсылает сообщение
import pymssql
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
import asyncio
from pyrogram import Client
from pyrogram.types import InputPhoneContact
import json
import tempfile
import telebot
import datetime
botTimeWeb = telebot.TeleBot('7019968682:AAGvOMxDxPLV9Y33TagpSXTexMDws1SNxzU')

from telebot import types

# Конфигурация
TELEGRAM_TOKEN = '7019968682:AAGvOMxDxPLV9Y33TagpSXTexMDws1SNxzU'
DB_CONFIG = {
    'server': '79.174.83.32',
    'port':'2000',
    'user': 'production',
    'password': 'pP_5647382910',
    'database': 'SKstudio'
} 

password = ""
bd = ""

@botTimeWeb.message_handler(commands=['start'])
def startBot(message):
    first_mess = f"<b>{message.from_user.first_name}</b>, привет!\nДля работы с этим ботом, нужно ввести пароль, который вам выдали в салоне SKstudio"
    markup = types.InlineKeyboardMarkup()
    button_yes = types.InlineKeyboardButton(text = 'Продолжить', callback_data='yes')
    markup.add(button_yes)
    global password
    password = ""
    botTimeWeb.send_message(message.chat.id, first_mess, parse_mode='html', reply_markup=markup)

@botTimeWeb.callback_query_handler(func=lambda call:True)
def response(function_call):
  if function_call.message:
    global bd, password
    if function_call.data == "yes":        
        mess_password = "Введите пароль:"
        botTimeWeb.send_message(function_call.message.chat.id, mess_password)
        botTimeWeb.answer_callback_query(function_call.id)     
    if function_call.data == "service":
        bd = fetch_notifications(password)
        count = 0
        for mess in bd:
            if mess['startDateTime'] > datetime.datetime.now():
                botTimeWeb.send_message(function_call.message.chat.id, "Вы записны в " + str(mess["startDateTime"]) + " на " + mess["name"])
                count += 1
            if count == 0:
                botTimeWeb.send_message(function_call.message.chat.id, "Вы не записаны\nЧтобы записаться позвоните по телефону: 8 905 515-81-41")
                mess_password_true = "Выбрите ту инфоомацию, что вам необходимо узнать"
                markup = types.InlineKeyboardMarkup()
                button_service = types.InlineKeyboardButton(text = 'Мои записи на прием', callback_data='service')
                markup.add(button_service)        
                button_pattern = types.InlineKeyboardButton(text = 'Рекомендации перед приемом', callback_data='pattern')
                markup.add(button_pattern)
                botTimeWeb.send_message(function_call.message.chat.id, mess_password_true, parse_mode='html', reply_markup=markup)    
            else:
                mess_pattern  = "Хотите узнать рекомендации перед приемом?"
                markup = types.InlineKeyboardMarkup()
                button_pattern = types.InlineKeyboardButton(text = 'Продолжить', callback_data='pattern')
                markup.add(button_pattern)
                botTimeWeb.send_message(function_call.message.chat.id, mess_pattern, parse_mode='html', reply_markup=markup)
    if function_call.data == "pattern":
        bd = fetch_notifications(password)
        count = 0
        for mess in bd:
            if mess['startDateTime'] > datetime.datetime.now() and mess['Text'] is not None:
                botTimeWeb.send_message(function_call.message.chat.id, str(mess["Text"]))
                count += 1
            if count == 0:
                botTimeWeb.send_message(function_call.message.chat.id, "Рекомендаций не найдено")
                mess_password_true = "Выбрите ту инфоомацию, что вам необходимо узнать"
                markup = types.InlineKeyboardMarkup()
                button_service = types.InlineKeyboardButton(text = 'Мои записи на прием', callback_data='service')
                markup.add(button_service)        
                button_pattern = types.InlineKeyboardButton(text = 'Рекомендации перед приемом', callback_data='pattern')
                markup.add(button_pattern)
                botTimeWeb.send_message(function_call.message.chat.id, mess_password_true, parse_mode='html', reply_markup=markup)    
            else:
                mess_pattern  = "Хотите узнать ваши записи на прием?"
                markup = types.InlineKeyboardMarkup()
                button_pattern = types.InlineKeyboardButton(text = 'Продолжить', callback_data='service')
                markup.add(button_pattern)
                botTimeWeb.send_message(function_call.message.chat.id, mess_pattern, parse_mode='html', reply_markup=markup)

@botTimeWeb.message_handler(content_types=['text'])
def after_text(message):
    if message.text != None:
        global bd, password
        password = message.text
        bd = fetch_notifications(password)
        if bd != None:
            mess_password_true = "Верный пароль. Теперь можешь выбрать ту инфоомацию, что тебе необходимо узнать"
            markup = types.InlineKeyboardMarkup()
            button_service = types.InlineKeyboardButton(text = 'Мои записи на прием', callback_data='service')
            markup.add(button_service)        
            button_pattern = types.InlineKeyboardButton(text = 'Рекомендации перед приемом', callback_data='pattern')
            markup.add(button_pattern)
            botTimeWeb.send_message(message.chat.id, mess_password_true, parse_mode='html', reply_markup=markup)
        else:
            botTimeWeb.send_message(message.chat.id, "Неверный пароль. Попробуйте еще раз")
            mess_password = "Введите пароль:"
            botTimeWeb.send_message(message.chat.id, mess_password)



def fetch_notifications(password):
    conn = pymssql.connect(**DB_CONFIG)
    cursor = conn.cursor(as_dict=True)
    # Запрос для получения данных о предстоящих записях, для которых уведомление еще не отправлено
    query =  f"""
    SELECT 
        a.startDateTime, s.name, p.Text
    FROM 
        Appointments a
    JOIN 
        Clients c ON a.clientId = c.id
    JOIN
        Services s on a.serviceId = s.id   
    JOIN 
        Categories cat ON s.categoryId = cat.id    
    JOIN 
        MessagesTemplates p ON p.categoryId = cat.id    
        WHERE c.password = '{password}'
    """
    try:
        cursor.execute(query)
        notifications = cursor.fetchall()

        cursor.close()
        print(notifications)
        return notifications
    except:
        print(1)
        return None

botTimeWeb.infinity_polling()
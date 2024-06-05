from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram import F
from aiogram.types import CallbackQuery
import pymssql
import datetime

BOT_TOKEN = '7019968682:AAGvOMxDxPLV9Y33TagpSXTexMDws1SNxzU'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_CONFIG = {
    'server': 'sql1',
    'port':'1433',
    'user': 'production',
    'password': 'pP_5647382910',
    'database': 'SKstudio'
}

log = False
query = ""
password = ""

@dp.message(CommandStart())
async def process_start_command(message: Message):
    global log, password, query
    log = False
    query = ""
    password = ""
    button_next = InlineKeyboardButton(text='Продолжить', callback_data='next')
    keyboard_next = InlineKeyboardMarkup(inline_keyboard=[[button_next]])
    await message.answer(
        text = f"{message.from_user.first_name}, привет!\nДля работы с этим ботом, нужно ввести пароль, который вам выдали в салоне SKstudio",
        reply_markup=keyboard_next
)

@dp.callback_query(F.data == 'next')
async def process_button_next(callback: CallbackQuery):
    global log, password, query
    log = True
    query = ""
    password = ""
    await callback.message.edit_text(
        text = f"{callback.message.from_user.first_name}, привет!\nДля работы с этим ботом, нужно ввести пароль, который вам выдали в салоне SKstudio",
        reply_markup=None
    )
    await callback.message.answer(
        text='Введите пароль:'
    )

@dp.message(F.content_type == 'text')
async def send_echo(message: Message):
    global log, query
    if (log):
        password = message.text
        query = fetch_notifications(password)
        if(len(query) > 0):
            button_appointment = InlineKeyboardButton(text='Мои предстоящие записи', callback_data='appointment')
            button_pattern = InlineKeyboardButton(text='Рекомендации перед приемом', callback_data='pattern')   
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_appointment], [button_pattern]])
            log = False
            await message.answer(
                text = "Верный пароль. Выберите информацию, что необходимо узнать:",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                text = "Неверный пароль. Попробуйте еще раз:",
                reply_markup=None
            )


@dp.callback_query(F.data == 'appointment')
async def process_appointments(callback: CallbackQuery):
    global query, password
    query = fetch_notifications(password)
    query_text = 'Вы записны:'
    count = 0
    for mess in query:
        if mess['startDateTime'] > datetime.datetime.now():
            query_text += '\n' + str(mess["startDateTime"]) + ' на ' + mess["name"]
            count += 1
    if count > 0:        
        await callback.message.edit_text(text=query_text,reply_markup=callback.message.reply_markup)
    else:
        await callback.message.edit_text(
            text='Вы не записаны\nЧтобы записаться позвоните по телефону: 8 905 515-81-41',
            reply_markup=callback.message.reply_markup)     


@dp.callback_query(F.data == 'pattern')
async def process_appointments(callback: CallbackQuery):
    global query, password
    query = fetch_notifications(password)
    query_text = ''
    count = 0
    for mess in query:
        if mess['startDateTime'] > datetime.datetime.now() and mess['Text'] is not None:
            query_text += str(mess["name"]) + ':\n' + str(mess["Text"]) + '\n'
            count += 1
    if count > 0:        
        await callback.message.edit_text(text=query_text,reply_markup=callback.message.reply_markup)
    else:
        await callback.message.edit_text(
            text='Рекомендаций не найдено',
            reply_markup=callback.message.reply_markup)
    


def fetch_notifications(password):
    conn = pymssql.connect(**DB_CONFIG)
    cursor = conn.cursor(as_dict=True)
    # Запрос для получения данных о предстоящих записях, для которых уведомление еще не отправлено
    query =  f"""
    SELECT 
        a.startDateTime, s.name, p.Text
    FROM 
        Appointments a
    RIGHT JOIN 
        Clients c ON a.clientId = c.id
    LEFT JOIN
        Services s on a.serviceId = s.id   
    LEFT JOIN 
        Categories cat ON s.categoryId = cat.id    
    LEFT JOIN 
        MessagesTemplates p ON p.categoriesId = cat.id    
    WHERE c.password = {password}
    """
    try:
        cursor.execute(query)
        notifications = cursor.fetchall()
        cursor.close()
        return notifications
    except:
        return ""
    
if __name__ == '__main__':
    dp.run_polling(bot)    

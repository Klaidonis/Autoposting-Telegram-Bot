#---------------------------------------Импорт конфигов-----------------------------------------------------------------#
import config as cg
import insta as inst
import Scrape as sc
#-----------------------------------------УСТАНОВКА--------------------------------------------------------------------#
#pip install --force-reinstall -v "aiogram==2.23.1" - версия aiogram для стабильиьной работы
import psycopg2
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from telethon.sync import TelegramClient, events
from telethon.tl import functions, types
from telethon.tl.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

try:
    connect = psycopg2.connect(user="postgres", password="*****", host="localhost", port="5432", database="Autoposting")
    cursor = connect.cursor()
    print("Успех подключения")
except:
    pass
try:
    cursor.execute("CREATE TABLE IF NOT EXISTS emojis (Id Serial, Message BIGINT PRIMARY KEY, Emoji TEXT, Begdate TEXT, Status TEXT, Group_id TEXT, Buffer BIGINT, WebSite TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS Telegram_channels (Id Serial, Username TEXT, Telegram_id BIGINT PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS Timing (Id INTEGER PRIMARY KEY, Timing BIGINT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS website (Id Serial, post_url TEXT PRIMARY KEY, Caption TEXT, TypePost TEXT, Status TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS User_admin (Id BIGINT Primary Key, User_name TEXT)")
    connect.commit()
    print("Таблицы успешно созданы")
except Exception as ex:
    print(ex)

#----------------------------------------------------------------------------------------------------------------------#
#закомментировать после первого запуска, чтобы не было сбоя со временем
# cursor.execute("INSERT INTO Timing (Id, Timing) VALUES (%s, %s);", (0, 0))
# connect.commit()
#----------------------------------------------------------------------------------------------------------------------#
url = 'http://parse.helperjp.site/'
scheduler = AsyncIOScheduler()
client = TelegramClient(cg.name, api_id=cg.api_id, api_hash=cg.api_hash, system_version="4.16.30-vxCUSTOM", device_model="Android", proxy=None)#.start(bot_token=cg.bot_token)
logging.basicConfig(level=logging.INFO)
bot = Bot(token=cg.bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
loop = asyncio.get_event_loop()

class Telegram(StatesGroup):
    Telegram = State()
    Name_channel = State()
    Delete = State()

class Instagram(StatesGroup):
    Instagram = State()
    Delete = State()

class Timnig(StatesGroup):
    Timnig = State()

class Admins(StatesGroup):
    Admins = State()
    Admin_name = State()
    Delete_admin = State()
#Адекватная пересылка постов из телеграм каналов в close_channel. Id берутся из бд.
async def db_telegram_id():
    cursor.execute("SELECT telegram_id FROM telegram_channels")
    for row in cursor.fetchall():
        @client.on(events.NewMessage(chats=row))
        async def buffer(event):
            if event.message.media and not event.grouped_id:
                await client.send_file(cg.close_channel, file=event.message, caption=event.text, parse_mode='HTML')

        @client.on(events.Album(chats=row))
        async def album(event):
            await client.send_message(entity=cg.close_channel, file=event.messages, message=event.text)

        @client.on(events.NewMessage(chats=row))
        async def text(event):
            if not event.message.media and not event.grouped_id:
                await client.send_message(cg.close_channel, file=None, message=event.text)
    connect.commit()

#Пересылка постов из буфферного канала в close_channel
@client.on(events.NewMessage(chats=cg.instagram_channel))
async def instagram_forward(event):
    if event.message.media and not event.grouped_id:
        await client.send_file(cg.close_channel, file=event.message, caption=event.text, parse_mode='HTML')

@client.on(events.Album(chats=cg.instagram_channel))
async def send_album(event):
    await client.send_message(entity=cg.close_channel, file=event.messages, message=event.text)


@client.on(events.NewMessage(chats=cg.instagram_channel))
async def forward_text_to_close_channel(event):
    # Проверка, что сообщение не содержит медиа и не является частью альбома
    if not event.message.media and not event.grouped_id:
        await client.send_message(cg.close_channel, message=event.message.text)

async def reactions():
    # Авторизация
    await client.start()

    # Подписываемся на события новых сообщений в канале
    @client.on(events.NewMessage(chats=cg.close_channel))
    async def handler(event):
        message = event.message
        message_id = message.id

        # Проверка наличия реакций в сообщении
        if message.reactions and message.out:
            # Обновляем статус emoji
            cursor.execute(f"UPDATE emojis SET Emoji = '1' WHERE Message = {message_id}")
            connect.commit()

        # Добавляем текстовые сообщения в базу данных
        elif not message.media:
            # Проверка, что сообщение не является медиа
            cursor.execute("INSERT INTO emojis (Message, Emoji, Begdate, Status, Group_id) VALUES (%s, %s, %s, %s, %s);", (message_id, "0", datetime.now(), "0", None))
            connect.commit()

    # Запускаем функцию для обработки сообщений с реакциями и текстовых сообщений
    await handle_messages(client)


async def handle_messages(client):
    # Получение ID канала по имени пользователя
    entity = cg.close_channel

    # Отслеживание сообщений в канале
    async for message in client.iter_messages(entity):
        if message.out:
            message_id = message.id
            existing_record = None

            cursor.execute(f"SELECT * FROM emojis WHERE message = {message_id}")
            existing_record = cursor.fetchone()

            if not existing_record:
                Begdate = (datetime.now().strftime('%Y-%m-%d %H-%M'))
                grouped_id = message.grouped_id
                if isinstance(message.media, types.MessageMediaPhoto):
                    try:
                        cursor.execute("BEGIN")  # Начинаем новую транзакцию
                        cursor.execute(f"INSERT INTO emojis (Message, Emoji, Begdate, Status, Group_id) VALUES (%s, %s, %s, %s, %s);", (message_id, "0", Begdate, "0", grouped_id))
                        connect.commit()
                    except Exception as e:
                        connect.rollback()  # Откатываем транзакцию в случае ошибки
                        logging.error(f"Error inserting record into emojis: {str(e)}")
                    finally:
                        cursor.execute("COMMIT")  # Завершаем транзакцию
                else:
                    # Добавляем текстовые сообщения в базу данных
                    cursor.execute("INSERT INTO emojis (Message, Emoji, Begdate, Status, Group_id) VALUES (%s, %s, %s, %s, %s);", (message_id, "0", datetime.now(), "0", None))
                    connect.commit()

        # Вызываем функцию для обработки сообщений с реакциями
        await reactions2(client, message)


async def reactions2(client, message):
    message_id = None  # Инициализируем переменную message_id
    existing_record = None  # Инициализируем переменную existing_record
    if message.out:
        message_id = message.id
        try:
            cursor.execute("COMMIT")  # Завершаем предыдущую транзакцию
            cursor.execute(f"SELECT * FROM emojis WHERE Group_id = '{message_id}' and emoji = '0'")
            existing_record = cursor.fetchone()
        except Exception as e:
            connect.rollback()  # Откатываем транзакцию в случае ошибки
            logging.error(f"Error selecting record from emojis: {str(e)}")

    # Проверка наличия реакций в сообщении и существования записи
    if message.reactions and not existing_record and message.grouped_id:
        if message_id:
            try:
                cursor.execute("BEGIN")  # Начинаем новую транзакцию
                # Запись не существует, поэтому создаем новую
                cursor.execute(f"UPDATE emojis SET emoji = '1' WHERE Group_id = '{message.grouped_id}'")
                connect.commit()
            except Exception as e:
                connect.rollback()  # Откатываем транзакцию в случае ошибки
                logging.error(f"Error updating record in emojis: {str(e)}")
    elif message.reactions and not existing_record and not message.grouped_id:
        if message_id:
            try:
                cursor.execute("BEGIN")
                cursor.execute(f"UPDATE emojis SET emoji = '1' WHERE Message = {message_id}")
                connect.commit()
            except Exception as e:
                connect.rollback()
                logging.error(f"Error updating record in emojis: {str(e)}")


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await bot.send_message(message.from_user.id, "Привет, если ты есть в базе админов, то ты сможешь пользоваться этим ботом:)")
    await bot.send_photo(message.from_user.id, photo="http://parse.helperjp.site/2023/10/09/%d0%b5%d1%89%d1%91-%d0%be%d0%b4%d0%b8%d0%bd-%d1%81%d1%8e%d0%b6%d0%b5%d1%82%d0%bd%d1%8b%d0%b9-%d1%81%d0%b8%d0%bd%d0%b5%d0%bc%d0%b0%d1%82%d0%b8%d0%ba-apex-legends-apexlegends/")


async def is_admin(user_id):
    cursor.execute("SELECT * FROM User_admin WHERE Id = %s", (user_id,))
    return cursor.fetchone() is not None


@dp.message_handler(commands=["Admin"])
async def start(message: types.Message):
    if await is_admin(message.from_user.id):
        markup = ReplyKeyboardMarkup(resize_keyboard=False)
        button1 = KeyboardButton('Добавить телеграмм')
        button2 = KeyboardButton('Добавить инстаграм')
        button3 = KeyboardButton('Добавить админа')
        button4 = KeyboardButton('Удалить админа')
        button5 = KeyboardButton('Изменить время')
        button6 = KeyboardButton('Просмотреть все документы')
        button7 = KeyboardButton('Удалить тг канал')
        button8 = KeyboardButton('Удалить инсту')
        markup.add(button1, button2, button3, button4, button5, button6, button7, button8)
        await bot.send_message(message.from_user.id, "Добро пожаловать в административную панель", reply_markup=markup)

@dp.message_handler(content_types=['text'])
async def text(message: types.Message):
    if await is_admin(message.from_user.id):
        if message.text == "Добавить телеграмм":
            await message.answer("Введите id канала")
            await Telegram.Telegram.set()
        elif message.text == "Добавить инстаграм":
            await message.answer("Введите ник пользователя инстаграм")
            await Instagram.Instagram.set()
        elif message.text == "Просмотреть все документы":
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            button0 = KeyboardButton("Телеграм")
            button1 = KeyboardButton("Инстаграм")
            button2 = KeyboardButton("Админы")
            button3 = KeyboardButton("Назад")
            markup.add(button0, button1, button2, button3)
            await bot.send_message(message.from_user.id, "Выберите список который надо вывести", reply_markup=markup)
        elif message.text == "Назад":
            markup = ReplyKeyboardMarkup(resize_keyboard=False)
            button1 = KeyboardButton('Добавить телеграмм')
            button2 = KeyboardButton('Добавить инстаграм')
            button3 = KeyboardButton('Добавить админа')
            button4 = KeyboardButton('Удалить админа')
            button5 = KeyboardButton('Изменить время')
            button6 = KeyboardButton('Просмотреть все документы')
            button7 = KeyboardButton('Удалить тг канал')
            button8 = KeyboardButton('Удалить инсту')
            markup.add(button1, button2, button3, button4, button5, button6, button7, button8)
            await bot.send_message(message.from_user.id, "Вы перемещены на главную панель", reply_markup=markup)
        elif message.text == "Телеграм":
            await bot.send_message(message.from_user.id, "Вывод всех телеграм каналов")
            cursor.execute("SELECT * FROM telegram_channels")
            for telegram in cursor.fetchall():
                await bot.send_message(message.from_user.id, f"Id: {telegram[0]}\nName channel: {telegram[1]}\nChannel id: {telegram[2]}")
                connect.commit()
        elif message.text == "Инстаграм":
            await bot.send_message(message.from_user.id, "Вывод всех аккаунтов инстаграма")
            await bot.send_message(message.from_user.id, f"{open(cg.path_to_username, encoding='UTf-8').read()}")
        elif message.text == "Удалить тг канал":
            await message.answer("Введите id чтобы удалить")
            await Telegram.Delete.set()
        elif message.text == "Удалить инсту":
            await message.answer("Введите название аккаунта чтобы удалить")
            await Instagram.Delete.set()
        elif message.text == "Изменить время":
            await message.answer("Укажите время для отправки постов в секундах")
            await Timnig.Timnig.set()
        elif message.text == "Добавить админа":
            await message.answer("Укажите id пользователя")
            await Admins.Admins.set()
        elif message.text == "Удалить админа":
            await message.answer("Укажите id админа которого хотите удалить")
            await Admins.Delete_admin.set()
        elif message.text == "Админы":
            cursor.execute("SELECT * FROM User_admin")
            for row in cursor.fetchall():
                await bot.send_message(message.from_user.id, f"Id: {row[0]}\nИмя: {row[1]}")
                connect.commit()

#Удаление
@dp.message_handler(state=Admins.Delete_admin)
async def delete_admin(message: types.Message, state: FSMContext):
    await state.update_data(delete_admin = message.text)
    data = await state.get_data()
    delete_admin = data['delete_admin']
    try:
        cursor.execute(f"DELETE from User_admin WHERE Id = {delete_admin}")
        connect.commit()
        await message.answer("Вы успешно удалил админа")
    except:
        pass
    await state.finish()

@dp.message_handler(state=Admins.Admins)
async def add_admins(message: types.Message, state: FSMContext):
    await state.update_data(add_admins = message.text)
    await message.answer("Укажите имя админа")
    await Admins.next()

@dp.message_handler(state=Admins.Admin_name)
async def add_name_admin(message: types.Message, state: FSMContext):
    await state.update_data(add_name_admin = message.text)
    data = await state.get_data()
    add_admins = data['add_admins']
    add_name_admin =  data['add_name_admin']
    try:
        cursor.execute("INSERT INTO User_admin (Id, User_name) VALUES (%s, %s);", (add_admins, add_name_admin))
        connect.commit()
        await message.answer("Вы успешно добавили админа")
    except Exception as ex:
        print(ex)


@dp.message_handler(state=Telegram.Delete)
async def delete_telegram_channel(message: types.Message, state: FSMContext):
    await state.update_data(delete_telegram_channel = message.text)
    data = await state.get_data()
    delete_telegram_channel = data['delete_telegram_channel']
    try:
        cursor.execute(f"DELETE FROM Telegram_channels WHERE Id = {delete_telegram_channel}")
        await message.answer("Вы успешно удалили телеграм канал")
    except:
        await message.reply(f"Такого Id {delete_telegram_channel} нет, повторите попытку")
    await state.finish()
    connect.commit()

@dp.message_handler(state=Instagram.Delete)
async def delete_instagram_account(message: types.Message, state: FSMContext):
    await state.update_data(delete_instagram_account = message.text)
    data = await state.get_data()
    delete_instagram_account = data['delete_instagram_account']
    with open(cg.path_to_username, 'r') as file:
        text = file.read()
    word_to_remove = delete_instagram_account
    new_text = text.replace(word_to_remove, '')
    with open(cg.path_to_username, 'w') as file:
        file.write(new_text)
    await state.finish()
#----------------------------------------------------------------------------------------------------------------------#
#Время отправки постов
#----------------------------------------------------------------------------------------------------------------------#
@dp.message_handler(state=Telegram.Telegram)
async def add_id_telegram(message: types.Message, state: FSMContext):
    await state.update_data(add_id_telegram = message.text)
    await message.answer("Укажите имя телеграм канала")
    await Telegram.next()

@dp.message_handler(state=Telegram.Name_channel)
async def add_name_channel_telegram(message: types.Message, state: FSMContext):
    await state.update_data(add_name_channel_telegram = message.text)
    data = await state.get_data()
    add_id_telegram = data['add_id_telegram']
    add_name_channel_telegram = data['add_name_channel_telegram']
    try:
        cursor.execute(f"INSERT INTO Telegram_channels (Username, Telegram_id) VALUES (%s, %s);", (add_name_channel_telegram, add_id_telegram))
        await message.answer(f"Вы успешно добавили телеграм канал\nId: {add_id_telegram}\nНазвание: {add_name_channel_telegram}")
    except:
        await message.reply("Такой канал уже есть в бд")
    await state.finish()
    connect.commit()

@dp.message_handler(state=Instagram.Instagram)
async def instagram_username(message: types.Message, state: FSMContext):
    await state.update_data(instagram_username = message.text)
    data = await state.get_data()
    instagram_username = data['instagram_username']
    with open(cg.path_to_username, 'a', encoding='UTF-8') as file:
        file.write(f"{instagram_username}\n")
    await message.answer("Вы успешно добавили инстграм аккаунт")
    await state.finish()

reactions_interval = None
send_message_interval = None

@dp.message_handler(state=Timnig.Timnig)
async def timing(message: types.Message, state: FSMContext):
    global reactions_interval, send_message_interval

    await state.update_data(timing=message.text)
    data = await state.get_data()
    timing = int(data['timing'])  # Преобразуйте значение в целое число

    # Удаляем текущие задачи
    scheduler.remove_job("reactions")
    scheduler.remove_job("send_message")

    # Создаем новые задачи с обновленными интервалами выполнения
    reactions_interval = send_message_interval = timing

    scheduler.add_job(reactions, "interval", seconds=reactions_interval, id="reactions")
    # scheduler.add_job(send_message, "interval", seconds=send_message_interval, id="send_message")
    # Обновите время в базе данных (псевдокод, замените на реальный SQL-запрос)
    try:

        cursor.execute(f"UPDATE Timing SET timing = {timing} WHERE Id = 0")
        await bot.naswer("Вы обновли время отправки постов")
    except:
        pass
        await state.finish()
    connect.commit()

@client.on(events.Album(chats=cg.instagram_channel))
async def handle_album(event):
    for media in event.messages:
        print("Тип медиа:", type(media))
        print("Информация о медиа:", media)

# Подписываемся на события новых сообщений в канале или чате
@client.on(events.NewMessage(chats=cg.close_channel))
async def handler(event):
    await handler(event)

#Send post in open channel
async def send_message():
    cursor.execute("SELECT Message, Group_id FROM emojis WHERE Status = '0' and emoji = '1' LIMIT 1")
    row = cursor.fetchone()
    if row:
        message_id, group_id = row

        # Получение сообщений с заданным group_id
        cursor.execute("SELECT Message FROM emojis WHERE Status = '0' and emoji = '1' AND Group_id = %s", (group_id,))
        messages = cursor.fetchall()

        if messages:
            media = []
            captions = []  # Список для хранения подписей к каждой фотографии

            for msg_id_tuple in messages:
                msg_id = msg_id_tuple[0]  # Получаем msg_id из кортежа
                channel = await client.get_entity(cg.close_channel)
                message = await client.get_messages(channel, ids=msg_id)

                if isinstance(message, Message):
                    # Если получено одно сообщение
                    if message.media:
                        media.append(message.media)
                        captions.append(message.text)  # Добавляем текст сообщения как подпись

            # Отправка сообщений как альбом
            if media:
                await client.send_file(cg.open_channel, media, caption=captions, reply_to=message_id)

            # Обновление статуса сообщений в БД
            cursor.execute("UPDATE emojis SET Status = '1' WHERE Group_id = %s", (group_id,))
            connect.commit()
        else:
            # Если не было сообщений с group_id, отправляем исходное сообщение
            channel = await client.get_entity(cg.close_channel)
            message = await client.get_messages(channel, ids=message_id)
            if message:
                await client.send_message(cg.open_channel, message)

            cursor.execute("UPDATE emojis SET Status = '1' WHERE Message = %s", (message_id,))
            connect.commit()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(db_telegram_id())
        cursor.execute("SELECT * FROM Timing")
        for timing in cursor.fetchall():
#Таймер отправки сообщений заменить время reactions_interval в send_message
            reactions_interval = send_message_interval = timing[1]
            scheduler.add_job(reactions, "interval", seconds=2, id="reactions") #Таймер чтобы отслеживать реакции на сообщениях в закрытом канале
            scheduler.add_job(send_message, "interval", seconds=reactions_interval, id="send_message") #Таймер для отправки сообщений из закрытого в открытый
            connect.commit()
#Парсинг инсты и сайта, таймер поставить на  > 5 минут
        scheduler.add_job(inst.save_post, "interval", seconds=1) #Таймер для сохранения постов из инсты в бд
        scheduler.add_job(inst.process_and_send_posts, "interval", seconds=1)#Таймер для отправки постов инстаграмма в буфферный канал
        #scheduler.add_job(sc.parse_and_send_to_telegram, "interval", seconds=30)#Таймер парсинга постов с сайта, первый запуск, пропарсит все посты, а затем будет парсить только новые.
        scheduler.start()
        client.start()
        executor.start_polling(dp, skip_updates=True)
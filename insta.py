import asyncio
import instaloader
import config as cg
import psycopg2
import asyncpg
from instaloader import Post, Profile
from aiogram import Bot, types, Dispatcher, executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import InputMediaPhoto, InputMediaDocument
#
try:
    connect = psycopg2.connect(user="postgres", password="*****", host="localhost", port="5432", database="Autoposting")
    cursor = connect.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS posts (Id Serial, Url TEXT Primary key, Typepost TEXT, Graph TEXT, Status TEXT, Caption TEXT, Shortcode TEXT)")
    connect.commit()
    print("Успех")
except Exception as ex:
    print(ex)

token = cg.bot_token
username = cg.insta_login
password = cg.insta_password
channel_id = cg.instagram_channel

bot = Bot(token=token)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

L = instaloader.Instaloader()
lock = asyncio.Lock()  # Создаем асинхронную блокировку

async def insert_post(pool, media_url, post_caption, post_type, shortcode):
    try:
        typepost = "Photo" if post_type == "GraphImage" or post_type == "GraphSidecar" else "Video"
        Graph = post_type
        Status = "0"

        async with pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "INSERT INTO posts (Url, Caption, Typepost, Graph, Status, Shortcode) VALUES ($1, $2, $3, $4, $5, $6);", media_url, post_caption, typepost, Graph, Status, shortcode)

    except Exception as ex:
        pass


async def save_post():
    try:
        async with lock:  # Устанавливаем блокировку
            # Подключение к базе данных
            pool = await asyncpg.create_pool(database="Autoposting", user="postgres", password="WorldWar1945",
                                             host="localhost", port=5432)

            with open(cg.path_to_username, 'r') as file:
                for username in file:
                    username = username.strip()  # Удаляем лишние пробелы и символы переноса строки
                    profile = instaloader.Profile.from_username(L.context, username)
                    posts = profile.get_posts()
                    latest_post = next(posts, None)  # Получаем последний пост

                    if latest_post:
                        shortcode = latest_post.shortcode
                        media_url = None

                        # Проверяем, является ли пост GraphSidecar (содержит ли несколько изображений/видео)
                        if latest_post.typename == "GraphSidecar":
                            for sidecar_post in latest_post.get_sidecar_nodes():
                                media_url = sidecar_post.display_url if not sidecar_post.is_video else sidecar_post.video_url
                                await insert_post(pool, media_url, latest_post.caption, "GraphSidecar", shortcode)
                        else:
                            # Для отдельных изображений/видео
                            media_url = latest_post.url if not latest_post.is_video else latest_post.video_url
                            await insert_post(pool, media_url, latest_post.caption, latest_post.typename, shortcode)

                        # После сохранения вызываем функцию отправки
                        cursor.execute("SELECT * FROM User_admin")
                        for row in cursor.fetchall():
                            await bot.send_message(row[0], f"Ошибка с instagram, API дало сбой: ")
                            connect.commit()
    except Exception as ex:
        cursor.execute("SELECT Id FROM User_admin")
        for row in cursor.fetchall():
            await bot.send_message(row, f"Ошибка с instagram, API дало сбой: {ex}")
            connect.commit()


async def process_and_send_posts():
    try:
        async with lock:  # Устанавливаем блокировку
            # Выбираем все уникальные shortcode из базы данных
            cursor.execute("SELECT DISTINCT Shortcode FROM posts WHERE Status='0';")
            unique_shortcodes = [record[0] for record in cursor.fetchall()]

            for shortcode in unique_shortcodes:
                # Выбираем все посты с заданным shortcode
                cursor.execute("SELECT * FROM posts WHERE Shortcode=%s AND Status='0';", (shortcode,))
                posts = cursor.fetchall()

                media_list = []  # Список для хранения медиа-объектов

                for post in posts:
                    caption = post[5] if post[5] else None
                    if post[2] == 'Photo':
                        media_list.append(InputMediaPhoto(media=post[1], caption=caption))
                    elif post[2] == 'Video':
                        media_list.append(InputMediaDocument(media=post[1], caption=caption))
                    elif post[2] == 'GraphSidecar':
                        # Обработка постов типа "GraphSidecar" (содержащих фотографии и/или видео)
                        profile = instaloader.Profile.from_username(L.context, username)
                        post = Post.from_shortcode(L.context, post[6])
                        for sidecar_post in post.get_sidecar_nodes():
                            if sidecar_post.is_video:
                                media_list.append(InputMediaDocument(media=sidecar_post.video_url, caption=caption))
                            else:
                                media_list.append(InputMediaPhoto(media=sidecar_post.display_url, caption=caption))

                # Отправляем медиа-объекты в виде медиа-группы
                if media_list:
                    await bot.send_media_group(chat_id=cg.instagram_channel, media=media_list)

                # Обновляем статус и меняем его на "1" для всех постов с данным shortcode
                cursor.execute("UPDATE posts SET Status='1' WHERE Shortcode=%s;", (shortcode,))
                connect.commit()
    except Exception as ex:
        cursor.execute("SELECT Id FROM User_admin")
        for row in cursor.fetchall():
            await bot.send_message(row, f"Ошибка с instagram, API дало сбой: {ex}")
            connect.commit()
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher
import logging
import config
import psycopg2
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.contrib.fsm_storage.memory import MemoryStorage

try:
    connect = psycopg2.connect(user="postgres", password="*****", host="localhost", port="5432", database="Autoposting")
    cursor = connect.cursor()
    print("Успех подключения")
    connect.commit()
except:
    pass

# Замените 'YOUR_BOT_TOKEN' на ваш токен бота
bot = Bot(token=config.bot_token)
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

scheduler = AsyncIOScheduler()
# Замените 'YOUR_CHANNEL_ID' на идентификатор вашего канала
channel_id = config.instagram_channel
# URL вашего сайта для парсинга
url = 'http://parse.helperjp.site/'

# Время задержки между отправкой постов (в секундах)
delay_between_posts = 10  # Например, 60 секунд (1 минута)

processed_posts = set()

async def parse_and_send_to_telegram():
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = soup.find_all('li')

        for post in posts:
            post_link = post.find('a', href=True)

            if post_link:
                post_url = post_link['href']

                if post_url not in processed_posts:
                    post_text = post.get_text()
                    post_image = post.find('img', src=True)
                    if post_image:
                        media_url = post_image['src']
                        post_type = 'gif' if media_url.endswith('.gif') else 'image'
                    else:
                        post_type = 'text'
                    try:
                        # Проверка наличия записи с таким ключом
                        cursor.execute('SELECT COUNT(*) FROM website WHERE post_url = %s', (post_url,))
                        count = cursor.fetchone()[0]

                        if count == 0:
                            # Если записи с таким ключом нет, то выполняем вставку
                            cursor.execute('''
                                INSERT INTO website (post_url, Caption, Typepost, Status)
                                VALUES (%s, %s, %s, %s)
                            ''', (post_url, post_text, post_type, '0'))
                            connect.commit()
                            processed_posts.add(post_url)
                        else:
                            # Если запись с таким ключом уже существует, пропускаем вставку
                            print(f'Запись с ключом {post_url} уже существует, пропускаем вставку.')
                    except Exception as ex:
                        print(ex)
    else:
        print('Ошибка при запросе к веб-сайту')

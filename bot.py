import os
import datetime
import random
import telebot
import requests
from bs4 import BeautifulSoup
from telebot import apihelper  # <-- Добавили этот импорт


TOKEN = '8856605303:AAHypRaCz2c23v9ORFcLB_6U7usdTFxVqsE'
bot = telebot.TeleBot(TOKEN)


def log_dialogue(user_id, role, text):
    """
    Выполняет требование по логированию (4 балла).
    Записывает лог в файл {ID}.log в кодировке UTF-8.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{user_id}.log"

    # Записываем строку лога: Время | Кто сказал | Текст
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {role}: {text}\n")


# === КОМАНДА 1: Базовое приветствие (Текстовая механика) ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)  # Логируем входящее сообщение

    reply = (
        "📚 Привет! Я твой Книжный Скаут.\n\n"
        "У меня реализовано 4 абсолютно разных механизма работы:\n"
        "1. /start или /help — Вызов этой справки.\n"
        "2. /book <название> — Поиск книги через внешнее HTTP-API.\n"
        "3. /quote — Парсинг случайной цитаты с сайта (HTML-скрапинг).\n"
        "4. /mylog — Чтение твоего персонального файла логов из системы."
    )

    bot.reply_to(message, reply)
    log_dialogue(user_id, "Bot", reply)  # Логируем ответ бота


# === КОМАНДА 2: Работа с HTTP-API (4 балла) ===
@bot.message_handler(commands=['book'])
def search_book(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)

    # Отделяем команду от самого названия книги
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        reply = "⚠️ Пожалуйста, укажи название книги.\nПример: `/book Мастер и Маргарита`"
        bot.reply_to(message, reply, parse_mode="Markdown")
        log_dialogue(user_id, "Bot", reply)
        return

    book_title = parts[1]
    bot.send_chat_action(user_id, 'typing')  # Визуальный эффект "Бот печатает..."

    try:
        # Используем бесплатное Open Library API (не требует ключей)
        url = "https://openlibrary.org/search.json"
        response = requests.get(url, params={'title': book_title}, timeout=10)

        # Проверяем успешность HTTP-запроса
        if response.status_code == 200:
            data = response.json()

            if data.get('docs'):
                # Берем самый первый результат поиска
                first_book = data['docs'][0]
                title = first_book.get('title', 'Данные отсутствуют')
                authors = ", ".join(first_book.get('author_name', ['Неизвестный автор']))
                year = first_book.get('first_publish_year', 'Не указан')

                reply = (
                    f"📖 *Результат поиска через API:*\n\n"
                    f"📌 *Название:* {title}\n"
                    f"✍️ *Автор(ы):* {authors}\n"
                    f"📅 *Год первого издания:* {year}"
                )
            else:
                reply = "❌ К сожалению, книга с таким названием не найдена в базе API."
        else:
            reply = f"❌ Ошибка сервера API (Код: {response.status_code})"

    except Exception as e:
        reply = f"❌ Не удалось получить данные по API. Ошибка: {e}"

    bot.reply_to(message, reply, parse_mode="Markdown")
    log_dialogue(user_id, "Bot", reply)


# === КОМАНДА 3: HTML-Скрапинг (4 балла) ===
@bot.message_handler(commands=['quote'])
def get_quote(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)

    bot.send_chat_action(user_id, 'typing')

    try:
        # Скрапим полигон для тренировки парсинга Quotes to Scrape
        url = "https://quotes.toscrape.com/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем все блоки с цитатами на странице
        quotes = soup.find_all('div', class_='quote')

        if quotes:
            # Выбираем случайную цитату из найденных на странице
            chosen_quote = random.choice(quotes)
            text = chosen_quote.find('span', class_='text').text
            author = chosen_quote.find('small', class_='author').text

            reply = f"💭 *Случайная цитата (добыта скрапингом HTML):*\n\n{text}\n\n— __{author}__"
        else:
            reply = "❌ Ошибка скрапинга: не удалось найти блоки цитат на странице."

    except Exception as e:
        reply = f"❌ Ошибка при парсинге сайта: {e}"

    bot.reply_to(message, reply, parse_mode="Markdown")
    log_dialogue(user_id, "Bot", reply)


# === КОМАНДА 4: Работа с локальной файловой системой ===
@bot.message_handler(commands=['mylog'])
def show_log(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)

    filename = f"{user_id}.log"

    try:
        # Открываем файл лога текущего пользователя на чтение
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Берем последние 7 строк, чтобы сообщение не было слишком гигантским
        last_lines = lines[-7:]
        log_content = "".join(last_lines)

        reply = f"📋 *Последние записи из твоего файла лога ({filename}):*\n\n```\n{log_content}```"

    except FileNotFoundError:
        reply = "📂 Твой файл лога еще не создан. Странно, ведь этот запрос уже должен был записаться!"
    except Exception as e:
        reply = f"❌ Ошибка чтения файла лога: {e}"

    bot.reply_to(message, reply, parse_mode="Markdown")
    log_dialogue(user_id, "Bot", reply)


if __name__ == '__main__':
    print("🚀 Бот успешно запущен и слушает команды...")
    bot.infinity_polling()

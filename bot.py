import os
import datetime
import random
import telebot
import requests
from bs4 import BeautifulSoup



TOKEN = '8856605303:AAHypRaCz2c23v9ORFcLB_6U7usdTFxVqsE'
bot = telebot.TeleBot(TOKEN)


def log_dialogue(user_id, role, text):
    """Логирование в файл {ID}.log"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{user_id}.log"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {role}: {text}\n")


# === КОМАНДА 1: Справка ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)

    reply = (
        "📚 Привет! Я твой Книжный Скаут.\n\n"
        "Доступные команды:\n"
        "1. /start или /help — Справка.\n"
        "2. /book <название> — Поиск книги через API.\n"
        "3. /quote — Случайная цитата (HTML-скрапинг).\n"
        "4. /mylog — Чтение твоего файла логов."
    )
    bot.reply_to(message, reply)
    log_dialogue(user_id, "Bot", reply)


# === КОМАНДА 2: Работа с HTTP-API ===
@bot.message_handler(commands=['book'])
def search_book(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        reply = "⚠️ Укажи название книги. Пример: `/book Капитанская дочка`"
        bot.reply_to(message, reply, parse_mode="Markdown")
        log_dialogue(user_id, "Bot", reply)
        return

    book_title = parts[1]
    bot.send_chat_action(user_id, 'typing')

    try:
        url = "https://openlibrary.org/search.json"
        response = requests.get(url, params={'title': book_title}, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('docs'):
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
                reply = "❌ Книга не найдена в базе API."
        else:
            reply = f"❌ Ошибка сервера API (Код: {response.status_code})"
    except Exception as e:
        reply = f"❌ Ошибка API: {e}"

    bot.reply_to(message, reply, parse_mode="Markdown")
    log_dialogue(user_id, "Bot", reply)


# === КОМАНДА 3: HTML-Скрапинг ===
@bot.message_handler(commands=['quote'])
def get_quote(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)
    bot.send_chat_action(user_id, 'typing')

    try:
        url = "https://quotes.toscrape.com/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        quotes = soup.find_all('div', class_='quote')

        if quotes:
            chosen_quote = random.choice(quotes)
            text = chosen_quote.find('span', class_='text').text
            author = chosen_quote.find('small', class_='author').text
            reply = f"💭 *Случайная цитата (HTML-скрапинг):*\n\n{text}\n\n— __{author}__"
        else:
            reply = "❌ Ошибка скрапинга."
    except Exception as e:
        reply = f"❌ Ошибка парсинга: {e}"

    bot.reply_to(message, reply, parse_mode="Markdown")
    log_dialogue(user_id, "Bot", reply)


# === КОМАНДА 4: Чтение логов ===
@bot.message_handler(commands=['mylog'])
def show_log(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)
    filename = f"{user_id}.log"

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        last_lines = lines[-7:]
        log_content = "".join(last_lines)
        reply = f"📋 *Последние записи из твоего файла лога:* \n\n```\n{log_content}```"
    except FileNotFoundError:
        reply = "📂 Твой файл лога еще не создан."
    except Exception as e:
        reply = f"❌ Ошибка чтения файла: {e}"

    bot.reply_to(message, reply, parse_mode="Markdown")
    log_dialogue(user_id, "Bot", reply)


if __name__ == '__main__':
    print("🚀 Бот запущен напрямую на сервере PythonAnywhere...")
    bot.infinity_polling()

import os
import datetime
import random
import telebot
import requests
from bs4 import BeautifulSoup

TOKEN = '8856605303:AAHypRaCz2c23v9ORFcLB_6U7usdTFxVqsE'
bot = telebot.TeleBot(TOKEN)

def log_dialogue(user_id, role, text):
    """Логирование в файл {ID}.log (Механизм работы с ФС)"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{user_id}.log"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {role}: {text}\n")


# === КОМАНДА 1: Базовое приветствие ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)
    
    reply = (
        "📚 Привет! Я твой Книжный Скаут.\n\n"
        "Вот 4 твоих главных функциональных механизма:\n"
        "1. /book <название> — Поиск книги через внешнее HTTP-API.\n"
        "2. /quote — Парсинг цитаты с сайта (HTML-скрапинг).\n"
        "3. /quiz — Интерактивная викторина (Механизм Inline-кнопок).\n"
        "4. /mylog — Чтение твоего файла логов (Работа с файловой системой)."
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


# === КОМАНДА 4: Интерактивный Квиз (НОВЫЙ МЕХАНИЗМ КНОПОК) ===
@bot.message_handler(commands=['quiz'])
def book_quiz(message):
    user_id = message.from_user.id
    log_dialogue(user_id, "User", message.text)
    
    # Создаем клавиатуру с кнопками прямо в сообщении
    markup = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(text="Александр Пушкин", callback_data="quiz_wrong")
    btn2 = telebot.types.InlineKeyboardButton(text="Михаил Булгаков", callback_data="quiz_correct")
    btn3 = telebot.types.InlineKeyboardButton(text="Николай Гоголь", callback_data="quiz_wrong")
    
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    
    reply = "❓ *Книжная викторина:*\n\nКто написал знаменитый роман «Мастер и Маргарита»?"
    bot.send_message(message.chat.id, reply, reply_markup=markup, parse_mode="Markdown")
    log_dialogue(user_id, "Bot", reply)

# Обработчик кликов по кнопкам викторины
@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz_'))
def callback_quiz(call):
    user_id = call.from_user.id
    
    if call.data == "quiz_correct":
        # Показываем всплывающее уведомление
        bot.answer_callback_query(call.id, text="🎉 Правильно! Отличные знания!", show_alert=True)
        # Редактируем сообщение, убирая кнопки и фиксируя победу
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text="❓ *Книжная викторина:*\n\nКто написал «Мастер и Маргарита»?\n\n✅ *Ваш ответ:* Михаил Булгаков (Правильно!)", 
            parse_mode="Markdown"
        )
        log_dialogue(user_id, "Quiz_Result", "Correct Answer")
    else:
        # Показываем подсказку без закрытия окна
        bot.answer_callback_query(call.id, text="❌ Неверно! Попробуй вспомнить еще раз.", show_alert=False)
        log_dialogue(user_id, "Quiz_Result", "Wrong Answer")


# === КОМАНДА 5: Чтение логов (Работа с ФС) ===
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
    print("🚀 Бот запущен.")
    bot.infinity_polling()

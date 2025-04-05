

import telebot
from telebot import types
import os


import weather_handler
import currency_handler
import other_functions_handler


API_TOKEN = '7586371533:AAHvcVQRf2ybvCG69RNP20cEOnhC4wlAWRY'


bot = telebot.TeleBot(API_TOKEN)



movies_db = {
    "Комедія": [
        {"photo": "comedy1.png", "name": "Суперперці", "description": "Двоє нерозлучних друзів-старшокласників намагаються вразити дівчат перед випуском, потрапляючи у безліч кумедних ситуацій.", "rating": 7.6, "price": 60},
        {"photo": "comedy2.png", "name": "Мачо і Ботан", "description": "Двоє невдалих поліцейських під прикриттям повертаються до школи, щоб викрити наркомережу, і знову переживають підліткові проблеми.", "rating": 7.2, "price": 60},
    ],
    "Драма": [
        {"photo": "drama1.png", "name": "Втеча з Шоушенка", "description": "Несправедливо засуджений банкір проводить роки у в'язниці, зберігаючи надію та плануючи неймовірну втечу.", "rating": 9.3, "price": 60},
        {"photo": "drama2.png", "name": "Зелена миля", "description": "Історія наглядача в блоці смертників в'язниці та його стосунків з незвичайним ув'язненим, що володіє дивовижними здібностями.", "rating": 8.6, "price": 60},
    ],
    "Бойовик": [
        {"photo": "action1.png", "name": "Темний лицар", "description": "Бетмен протистоїть хаотичному генію злочинності - Джокеру, який прагне занурити Готем у анархію.", "rating": 9.0, "price": 60},
        {"photo": "action2.png", "name": "Джон Вік", "description": "Легендарний колишній найманий вбивця повертається зі спокою, щоб помститися гангстерам, які забрали у нього найдорожче.", "rating": 7.4, "price": 60},
    ]
}

user_data = {}


STATE_AWAITING_EMAIL = 'awaiting_email'




def get_movie_details(movie_name):
    for genre_movies in movies_db.values():
        for movie in genre_movies:
            if movie['name'] == movie_name:
                return movie
    return None



@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    continue_button = types.InlineKeyboardButton("Продовжити", callback_data='continue_welcome')
    markup.add(continue_button)
    bot.send_message(chat_id,
                     "Вітаю в нашому магазині відеопродукції. Я тут, для того, щоб допомогти вам створити замовлення 😉",
                     reply_markup=markup)
    if chat_id in user_data: del user_data[chat_id]



def show_main_menu(chat_id, message_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    genre_button = types.InlineKeyboardButton("🎬 Обрати жанр", callback_data='select_genre')
    other_button = types.InlineKeyboardButton("⚙️ Інші функції", callback_data='other_functions')
    markup.add(genre_button, other_button)
    caption = "Що вас цікавить?"
    photo_path = 'menu.png'
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"[Помилка видалення повідомлення {message_id}]: {e}")
    try:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                 bot.send_photo(chat_id, photo, caption=caption, reply_markup=markup)
        else:
             print(f"[Попередження]: Файл {photo_path} не знайдено. Надсилаю текст.")
             bot.send_message(chat_id, caption, reply_markup=markup)
    except Exception as e:
         print(f"[Помилка надсилання головного меню]: {e}")
         bot.send_message(chat_id, "Не вдалося завантажити меню. " + caption, reply_markup=markup)

def show_genre_selection(chat_id, message_id):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(genre, callback_data=f'genre_{genre}') for genre in movies_db.keys()]
    markup.add(*buttons)
    back_button = types.InlineKeyboardButton("⬅️ Головне меню", callback_data='back_to_main_menu')
    markup.add(back_button)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"[Помилка видалення повідомлення {message_id} перед показом жанрів]: {e}")
    bot.send_message(chat_id, "Наразі ми маємо фільми таких жанрів:", reply_markup=markup)
    if chat_id in user_data:
        user_data[chat_id].pop('selected_movie_name', None)
        user_data[chat_id].pop('price', None)

def show_movies_in_genre(chat_id, message_id, genre):
    if genre in movies_db:
        markup = types.InlineKeyboardMarkup(row_width=1)
        buttons = [types.InlineKeyboardButton(movie['name'], callback_data=f'movie_{movie["name"]}') for movie in movies_db[genre]]
        markup.add(*buttons)
        back_button = types.InlineKeyboardButton("⬅️ Обрати інший жанр", callback_data='select_genre')
        markup.add(back_button)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"[Помилка видалення повідомлення {message_id} перед показом фільмів]: {e}")
        bot.send_message(chat_id, f"Фільми жанру '{genre}':", reply_markup=markup)
    else:
         print(f"[Помилка]: Спроба показати фільми для неіснуючого жанру '{genre}' для {chat_id}")
         try: bot.delete_message(chat_id, message_id)
         except: pass
         bot.send_message(chat_id, "Виникла помилка: Жанр не знайдено. Будь ласка, спробуйте ще раз.")

def show_movie_details(chat_id, message_id, movie_name):
    movie = get_movie_details(movie_name)
    if movie:
        if chat_id not in user_data: user_data[chat_id] = {}
        user_data[chat_id]['selected_movie_name'] = movie['name']
        user_data[chat_id]['price'] = movie['price']
        markup = types.InlineKeyboardMarkup(row_width=1)
        confirm_button = types.InlineKeyboardButton("Так, оформлюємо!", callback_data=f'order_confirm_{movie_name}')
        change_genre_button = types.InlineKeyboardButton("Вибрати інший жанр", callback_data='select_genre')
        current_genre = user_data.get(chat_id, {}).get('selected_genre')
        if current_genre:
             change_movie_button = types.InlineKeyboardButton("Вибрати інший фільм", callback_data=f'genre_{current_genre}')
             markup.add(confirm_button, change_genre_button, change_movie_button)
        else:
             markup.add(confirm_button, change_genre_button)
             print(f"[Попередження]: Не вдалося визначити поточний жанр для {chat_id} при показі деталей '{movie_name}'")
        caption = f"*{movie['name']}*\n\n{movie['description']}\n\nРейтинг IMDB: {movie['rating']}\nЦіна: {movie['price']} грн\n\n*Оформлюємо замовлення?*"
        photo_path = movie['photo']
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"[Помилка видалення повідомлення {message_id} перед показом деталей]: {e}")
        try:
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=caption, reply_markup=markup, parse_mode='Markdown')
            else:
                 print(f"[Попередження]: Файл {photo_path} не знайдено. Надсилаю текст.")
                 bot.send_message(chat_id, caption, reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
             print(f"[Помилка надсилання деталей фільму]: {e}")
             bot.send_message(chat_id, f"Не вдалося завантажити фото.\n{caption}", reply_markup=markup, parse_mode='Markdown')
    else:
        print(f"[Помилка]: Не знайдено деталі для фільму '{movie_name}' для {chat_id}")
        try: bot.delete_message(chat_id, message_id)
        except: pass
        bot.send_message(chat_id, "Вибачте, інформація про цей фільм недоступна. Спробуйте обрати інший.")

def ask_final_confirmation(chat_id, message_id):
    movie_name = user_data.get(chat_id, {}).get('selected_movie_name', 'Невідомий фільм')
    if movie_name == 'Невідомий фільм':
         print(f"[Помилка]: Спроба підтвердити замовлення без вибраного фільму для {chat_id}")
         try: bot.delete_message(chat_id, message_id)
         except: pass
         bot.send_message(chat_id, "Помилка: фільм не вибрано. Будь ласка, почніть спочатку з /start")
         return
    markup = types.InlineKeyboardMarkup(row_width=2)
    yes_button = types.InlineKeyboardButton("Так!", callback_data='final_confirm_yes')
    no_button = types.InlineKeyboardButton("Ні, хочу змінити вибір", callback_data='final_confirm_no')
    markup.add(yes_button, no_button)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"[Помилка видалення повідомлення {message_id} перед фінальним підтвердженням]: {e}")
    bot.send_message(chat_id, f"Ви обрали фільм \"{movie_name}\"?", reply_markup=markup)

#  ЛОГІКА ОБРОБКИ ДІЙ КОРИСТУВАЧА  

def handle_order_choice(chat_id, message_id, callback_data):
    action_parts = callback_data.split('_')
    if len(action_parts) > 1 and action_parts[1] == 'confirm':
        ask_final_confirmation(chat_id, message_id)

def handle_final_confirmation(chat_id, message_id, callback_data):
    if callback_data == 'final_confirm_yes':
        try:
            bot.edit_message_text("Будь ласка, напишіть вашу електронну пошту для отримання посилання на фільм:",
                                  chat_id, message_id, reply_markup=None)
            if chat_id not in user_data: user_data[chat_id] = {}
            user_data[chat_id]['state'] = STATE_AWAITING_EMAIL
        except Exception as e:
            print(f"[Помилка редагування повідомлення {message_id} для запиту email]: {e}")
            try: bot.delete_message(chat_id, message_id)
            except: pass
            bot.send_message(chat_id, "Будь ласка, напишіть вашу електронну пошту для отримання посилання на фільм:")
            if chat_id not in user_data: user_data[chat_id] = {}
            user_data[chat_id]['state'] = STATE_AWAITING_EMAIL
    elif callback_data == 'final_confirm_no':
        if chat_id in user_data:
            user_data[chat_id].pop('selected_movie_name', None)
            user_data[chat_id].pop('price', None)
        show_genre_selection(chat_id, message_id)


#  РЕЄСТРАЦІЯ ОБРОБНИКІВ З ІНШИХ МОДУЛІВ 

other_functions_handler.register_handlers(bot, user_data) #
weather_handler.register_handlers(bot, user_data)         
currency_handler.register_handlers(bot, user_data)        


# ГОЛОВНИЙ ОБРОБНИК НАТИСКАННЯ Inline КНОПОК 

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """Обробляє решту натискань Inline кнопок."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    if chat_id not in user_data: user_data[chat_id] = {}
    parts = call.data.split('_')
    callback_action = parts[0]
    callback_value = '_'.join(parts[1:]) if len(parts) > 1 else None
    try:
       
        if call.data == 'continue_welcome':
            bot.answer_callback_query(call.id)
            show_main_menu(chat_id, message_id)
        elif call.data == 'select_genre':
            bot.answer_callback_query(call.id)
            show_genre_selection(chat_id, message_id)
     
        elif call.data == 'back_to_main_menu': 
             bot.answer_callback_query(call.id)
             show_main_menu(chat_id, message_id)
        elif callback_action == 'genre':
            bot.answer_callback_query(call.id)
            if callback_value:
                user_data[chat_id]['selected_genre'] = callback_value
                show_movies_in_genre(chat_id, message_id, callback_value)
            else:
                 print(f"[Помилка]: Отримано callback 'genre_' без значення для {chat_id}")
                 bot.send_message(chat_id, "Сталася помилка при виборі жанру.")
        elif callback_action == 'movie':
            bot.answer_callback_query(call.id)
            if callback_value:
                show_movie_details(chat_id, message_id, callback_value)
            else:
                 print(f"[Помилка]: Отримано callback 'movie_' без значення для {chat_id}")
                 bot.send_message(chat_id, "Сталася помилка при виборі фільму.")
        elif callback_action == 'order':
             
             handle_order_choice(chat_id, message_id, call.data)
        elif callback_action == 'final':
             
             handle_final_confirmation(chat_id, message_id, call.data)
        else:
             
             print(f"[Попередження]: Невідомий callback_data '{call.data}' в головному обробнику від {chat_id}")
             bot.answer_callback_query(call.id) 

    except Exception as e:
        print(f"[Критична помилка в handle_callback_query]: {e}")
        try: bot.answer_callback_query(call.id, "Сталася помилка!")
        except: pass
        try: bot.send_message(chat_id, "Ой! Щось пішло не так. 😥 Будь ласка, спробуйте почати з /start")
        except Exception as send_error: print(f"[Помилка надсилання повідомлення про критичну помилку]: {send_error}")




@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_AWAITING_EMAIL)
def get_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    if '@' in email and '.' in email.split('@')[-1] and len(email.split('@')[-1]) > 1:
        user_data[chat_id]['email'] = email
        user_data[chat_id]['state'] = None
        movie_name = user_data.get(chat_id, {}).get('selected_movie_name', 'Невідомий фільм')
        price = user_data.get(chat_id, {}).get('price', 'N/A')
        final_text = f"🎉 Вітаю з замовленням!\n\nВаше замовлення:\n\n🎬 *Вибраний фільм:* {movie_name}\n💰 *Ціна:* {price} грн\n📧 *Пошта:* {email}\n\nПісля перевірки з вами зв'яжеться наш менеджер 😊"
        bot.send_message(chat_id, final_text, parse_mode='Markdown')
    else:
        bot.reply_to(message, "Хм, це не схоже на правильну адресу електронної пошти. 🤔 Будь ласка, введіть ще раз:")


@bot.message_handler(content_types=['text'])
def handle_other_text(message):
    """Відповідає на незрозумілі текстові команди."""
    
    if user_data.get(message.chat.id, {}).get('state') is None:
         bot.send_message(message.chat.id, "Не розумію цю команду. 😕 Будь ласка, скористайтесь кнопками або почніть з команди /start.")


# ЗАПУСК 
if __name__ == '__main__':
    print("Запуск основного бота (movie_bot.py)...")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"[Критична помилка при запуску polling]: {e}")
    print("Бот зупинено.")
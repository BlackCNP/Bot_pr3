
import telebot
from telebot import types

def show_other_functions_menu(chat_id, message_id, bot):
    """Показує меню погоди та конвертації валют."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    weather_button = types.InlineKeyboardButton("🌦️ Погода", callback_data='weather_start')
    currency_button = types.InlineKeyboardButton("💱 Конвертація валют", callback_data='currency_start')
    
    back_button = types.InlineKeyboardButton("⬅️ Головне меню", callback_data='back_to_main_menu')
    markup.add(weather_button, currency_button, back_button)

    text = "Тут ви можете дізнатись погоду або конвертувати валюту:"

    try:
        
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"[OtherFunc] Помилка видалення повідомлення {message_id}: {e}")

    
    bot.send_message(chat_id, text, reply_markup=markup)


def register_handlers(bot, user_data): 
    """Реєструє обробники для меню 'Інші функції'."""

    @bot.callback_query_handler(func=lambda call: call.data == 'other_functions')
    def handle_other_functions_callback(call):
        bot.answer_callback_query(call.id)
        show_other_functions_menu(call.message.chat.id, call.message.message_id, bot)

    print("Обробник меню 'Інші функції' зареєстровано.")


import requests
import json
import telebot
from telebot import types
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation 


OER_API_KEY = '4f01cf48100f4291b65b837efbb7d4da'
OER_API_URL = f"https://openexchangerates.org/api/latest.json?app_id={OER_API_KEY}"


RATES_CACHE = {'timestamp': 0, 'data': None}
CACHE_DURATION = 3600 


STATE_AWAITING_CONVERSION_REQUEST = 'awaiting_conversion_request'


def get_exchange_rates():
    """Отримує актуальні курси валют з OER, використовує кеш."""
    import time
    current_time = time.time()

   
    if RATES_CACHE['data'] and (current_time - RATES_CACHE['timestamp'] < CACHE_DURATION):
        print("[Currency] Використання кешованих курсів.")
        return RATES_CACHE['data']

    print("[Currency] Оновлення курсів валют з API...")
    try:
        response = requests.get(OER_API_URL)
        response.raise_for_status() 
        data = response.json()

        if 'rates' not in data:
             print(f"[Помилка API валют] Відсутній ключ 'rates' у відповіді: {data}")
             return None 

       
        RATES_CACHE['data'] = data['rates']
        RATES_CACHE['timestamp'] = current_time
        print("[Currency] Курси успішно оновлені та закешовані.")
        return data['rates']

    except requests.exceptions.RequestException as e:
        print(f"[Помилка API валют - RequestException]: {e}")
        
        return RATES_CACHE['data']
    except json.JSONDecodeError as e:
         print(f"[Помилка API валют - JSONDecodeError]: {e}")
         return RATES_CACHE['data'] 
    except Exception as e:
        print(f"[Помилка API валют - Загальна]: {e}")
        return RATES_CACHE['data'] 


def convert_currency(amount_str, from_curr, to_curr):
    """Конвертує валюту, використовуючи отримані курси."""
    rates = get_exchange_rates()
    if not rates:
        return "Помилка: Не вдалося отримати актуальні курси валют."

    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

    
    try:
        amount = Decimal(amount_str.replace(',', '.')) 
        if amount <= 0:
            return "Сума для конвертації має бути позитивною."
    except InvalidOperation:
        return "Невірний формат суми. Введіть число."

   
    if from_curr != 'USD' and from_curr not in rates:
        return f"Помилка: Валюта '{from_curr}' не підтримується або відсутня в курсах."
    if to_curr != 'USD' and to_curr not in rates:
        return f"Помилка: Валюта '{to_curr}' не підтримується або відсутня в курсах."

    try:
        
        if from_curr == 'USD':
            amount_in_usd = amount
        else:
            rate_from_usd = Decimal(str(rates[from_curr])) #
            amount_in_usd = amount / rate_from_usd

      
        if to_curr == 'USD':
            final_amount = amount_in_usd
        else:
            rate_to_usd = Decimal(str(rates[to_curr])) 
            final_amount = amount_in_usd * rate_to_usd

        
        quantizer = Decimal("0.01")
        rounded_amount = final_amount.quantize(quantizer, rounding=ROUND_HALF_UP)

        return f"{amount_str} {from_curr} = {rounded_amount} {to_curr}"

    except KeyError as e:
        return f"Помилка: Валюта '{e}' не знайдена в поточних курсах."
    except Exception as e:
        print(f"[Помилка конвертації]: {e}")
        return "Сталася помилка під час конвертації."


#  Функції для взаємодії з користувачем 
def show_conversion_prompt(chat_id, message_id, bot, user_data):
    """Запитує у користувача дані для конвертації."""
    text = ("Будь ласка, введіть запит для конвертації у форматі:\n"
            "`Сума Валюта_З Валюта_В`\n\n"
            "Наприклад: `100 USD UAH` або `50.5 EUR USD`")
    try:
        # Видалання попереднє повідомлення 
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"[Currency] Помилка видалення повідомлення {message_id}: {e}")

    bot.send_message(chat_id, text, parse_mode='Markdown')
    if chat_id not in user_data: user_data[chat_id] = {}
    user_data[chat_id]['state'] = STATE_AWAITING_CONVERSION_REQUEST



def register_handlers(bot, user_data):
    """Реєструє обробники для функціоналу конвертації валют."""

   
    @bot.callback_query_handler(func=lambda call: call.data == 'currency_start')
    def handle_currency_start_callback(call):
        bot.answer_callback_query(call.id)
        show_conversion_prompt(call.message.chat.id, call.message.message_id, bot, user_data)

   
    @bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_AWAITING_CONVERSION_REQUEST)
    def handle_conversion_input(message):
        chat_id = message.chat.id
        parts = message.text.strip().split()

        if len(parts) != 3:
            bot.reply_to(message,
                         "Невірний формат запиту. Будь ласка, введіть у форматі: `Сума Валюта_З Валюта_В`\n"
                         "(Наприклад: `100 USD UAH`)", parse_mode='Markdown')
            
            return

        amount_str, from_curr, to_curr = parts

        
        if chat_id in user_data:
            user_data[chat_id]['state'] = None

        
        result = convert_currency(amount_str, from_curr, to_curr)

        
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("⬅️ Інші функції", callback_data='other_functions')
        markup.add(back_btn)

        bot.send_message(chat_id, result, reply_markup=markup)

    print("Обробники валют зареєстровані.")
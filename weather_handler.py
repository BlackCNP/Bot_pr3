
import requests
import json
from datetime import datetime
import telebot
from telebot import types


WEATHER_API_KEY = '837b69b2fd6f3e781972f83bd4470fbe' 


STATE_AWAITING_CITY = 'awaiting_city'


def get_weather_data(city_name):
    """Отримує та форматує дані про погоду з OpenWeatherMap."""
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
   
    current_date_str = datetime.now().strftime("%d.%m.%Y") 

    complete_url = base_url + "appid=" + WEATHER_API_KEY + "&q=" + city_name + "&units=metric&lang=uk"
    try:
        response = requests.get(complete_url)
        response.raise_for_status() 
        data = response.json()

        if data.get("cod") == 200 or data.get("cod") == "200": 
            main_data = data.get("main", {})
            weather_data_list = data.get("weather", [{}])
            weather_data = weather_data_list[0] if weather_data_list else {}
            wind_data = data.get("wind", {})
            temp = main_data.get("temp")
            description = weather_data.get("description", "Невідомо").capitalize()
            wind_speed = wind_data.get("speed")
            city_display_name = data.get("name", city_name) 

            
            if temp is None or wind_speed is None:
                 print(f"[Помилка даних погоди]: Відсутні 'temp' або 'wind_speed' для {city_name}. Відповідь: {data}")
                 return f"Вибачте, не вдалося отримати повні дані про погоду для міста '{city_display_name}'."

            # Форматує відповідь згідно з прикладом користувача
            weather_report = (
                f"*{city_display_name}*: Погода на {current_date_str}\n\n" 
                f"🌡️ Температура: {temp:.0f}°C\n" # Округлення до цілого
                f"📝 Опис: {description}\n"
                f"💨 Швидкість вітру: {wind_speed:.1f} м/с" # Округлення до одного знаку
            )
            return weather_report
        elif str(data.get("cod")) == "404": 
             return f"Вибачте, місто '{city_name}' не знайдено. 😕 Спробуйте іншу назву."
        else:
           
            error_message = data.get("message", "Невідома помилка API")
            print(f"[Помилка API погоди]: Код {data.get('cod')}, Повідомлення: {error_message}")
            return f"Вибачте, сталася помилка API при запиті погоди ({error_message})."

    except requests.exceptions.HTTPError as http_err:
        print(f"[Помилка API погоди - HTTPError]: {http_err}")
        try: 
            error_data = http_err.response.json()
            error_message = error_data.get("message", str(http_err))
        except: error_message = str(http_err)
        return f"Вибачте, сталася помилка при отриманні даних про погоду ({error_message}). Спробуйте пізніше."
    except requests.exceptions.RequestException as e:
        print(f"[Помилка API погоди - RequestException]: {e}")
        return "Вибачте, сталася помилка мережі при отриманні даних про погоду. Спробуйте пізніше."
    except json.JSONDecodeError as e:
         print(f"[Помилка API погоди - JSONDecodeError]: {e}")
         return "Вибачте, отримана некоректна відповідь від сервісу погоди."
    except KeyError as e:
        print(f"[Помилка обробки погоди - KeyError]: Не знайдено ключ {e}")
        return "Вибачте, сталася помилка при обробці даних про погоду."
    except Exception as e:
        print(f"[Помилка обробки погоди - Загальна]: {e}")
        return "Вибачте, сталася невідома помилка при обробці погоди. Спробуйте пізніше."


# --- Функції для взаємодії з користувачем ---
def show_weather_prompt(chat_id, message_id, bot, user_data):
    """Запитує назву міста для прогнозу погоди, видаляючи попереднє повідомлення."""
    text = "Будь ласка, введіть назву міста для прогнозу погоди:"
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"[Weather] Помилка видалення повідомлення {message_id}: {e}")

    # Надсилає нове повідомлення із запитом
    bot.send_message(chat_id, text)
    # Встановлює стан очікування
    if chat_id not in user_data: user_data[chat_id] = {}
    user_data[chat_id]['state'] = STATE_AWAITING_CITY


# --- Функція реєстрації обробників для цього модуля ---
def register_handlers(bot, user_data):
    """Реєструє обробники для функціоналу погоди."""

    
    @bot.callback_query_handler(func=lambda call: call.data == 'weather_start')
    def handle_weather_start_callback(call):
        """Обробляє натискання кнопки 'Погода'."""
        bot.answer_callback_query(call.id)
        # Викликає функцію, яка запитає назву міста
        show_weather_prompt(call.message.chat.id, call.message.message_id, bot, user_data)

    # Обробник текстового повідомлення, коли очікується назва міста
    @bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == STATE_AWAITING_CITY)
    def handle_city_input(message):
        """Отримує назву міста та надсилає прогноз погоди."""
        chat_id = message.chat.id
        city = message.text.strip()

        if not city: # Перевірка на порожній ввід
            bot.reply_to(message, "Назва міста не може бути порожньою. Спробуйте ще раз.")
            
            return

        # Скидаємо стан очікування
        if chat_id in user_data:
            user_data[chat_id]['state'] = None

        # Повідомлення про завантаження 
        loading_message = bot.send_message(chat_id, f"⏳ Шукаю погоду для міста *{city}*...", parse_mode='Markdown')

        
        weather_report = get_weather_data(city)

       
        markup = types.InlineKeyboardMarkup()
      
        back_btn = types.InlineKeyboardButton("⬅️ Інші функції", callback_data='other_functions')
        markup.add(back_btn)

      
        bot.send_message(chat_id, weather_report, reply_markup=markup, parse_mode='Markdown')

    print("Обробники погоди зареєстровані.")
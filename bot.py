import os
import random
import logging
from flask import Flask, request, jsonify
import telebot
from telebot import types

# ==========================================
# КОНФИГУРАЦИЯ (прямое указание данных)
# ==========================================
TELEGRAM_TOKEN = '7523520150:AAGMPibPAl8D0I0E6ZeNR3zuIp0qKcshXN0'
WEBHOOK_SECRET = 'l97EqzQhw2lhSb3Ci2e-zg-nk9y4vG3-NLWA3ebnFpQ'
VERCEL_URL = 'https://pystzarabotaet.vercel.app'

# ==========================================
# ИНИЦИАЛИЗАЦИЯ
# ==========================================
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# ИГРОВЫЕ НАСТРОЙКИ
# ==========================================
SLOT_SYMBOLS = ['🍒', '🍋', '🍇', '🍉', '🔔', '💎', '7️⃣', '🐶']
INITIAL_BALANCE = 1000
MIN_BET = 10
MAX_BET = 500

# База данных в памяти
users_db = {}

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            'balance': INITIAL_BALANCE,
            'bet': 100,
            'last_spin': None
        }
    return users_db[user_id]

# ==========================================
# ВЕБ-ЭНДПОИНТЫ
# ==========================================
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot": "Dog House Slots",
        "version": "1.0"
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "ok",
        "telegram": "connected",
        "webhook": "active"
    })

@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# ==========================================
# КОМАНДЫ БОТА
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        user = get_user(message.from_user.id)
        bot.send_message(
            message.chat.id,
            f"🎰 Добро пожаловать в Dog House Slots!\n\n"
            f"💰 Баланс: {user['balance']} монет\n"
            f"🪙 Ставка: {user['bet']} монет\n\n"
            "Доступные команды:\n"
            "/spin - Крутить слоты\n"
            "/bet - Изменить ставку",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Start command error: {e}")

@bot.message_handler(commands=['spin'])
def spin(message):
    try:
        user = get_user(message.from_user.id)
        
        if user['balance'] < user['bet']:
            return bot.send_message(message.chat.id, "❌ Недостаточно средств!")
        
        # Генерация результата
        result = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
        win = 100 if len(set(result)) == 1 else 0
        
        # Обновление баланса
        user['balance'] += win - user['bet']
        user['last_spin'] = {'result': result, 'win': win}
        
        # Отправка результата
        bot.send_message(
            message.chat.id,
            f"🎰 Результат: {' '.join(result)}\n\n"
            f"💎 Выигрыш: {win} монет\n"
            f"💰 Баланс: {user['balance']} монет\n\n"
            "Ещё раз? /spin",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Spin error: {e}")

@bot.message_handler(commands=['bet'])
def change_bet(message):
    try:
        user = get_user(message.from_user.id)
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("-10", callback_data="bet_down"),
            types.InlineKeyboardButton(f"{user['bet']}", callback_data="bet_current"),
            types.InlineKeyboardButton("+10", callback_data="bet_up")
        )
        
        bot.send_message(
            message.chat.id,
            f"⚙️ Текущая ставка: {user['bet']} монет\n"
            f"Минимум: {MIN_BET}, Максимум: {MAX_BET}\n\n"
            "Используйте кнопки для изменения:",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Change bet error: {e}")

# ==========================================
# CALLBACK-ОБРАБОТЧИКИ
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('bet_'))
def bet_callback(call):
    try:
        user = get_user(call.from_user.id)
        action = call.data.split('_')[1]
        
        if action == 'up':
            user['bet'] = min(user['bet'] + 10, MAX_BET)
        elif action == 'down':
            user['bet'] = max(user['bet'] - 10, MIN_BET)
        
        # Обновляем сообщение
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⚙️ Новая ставка: {user['bet']} монет",
            reply_markup=None
        )
        bot.answer_callback_query(call.id, f"Ставка изменена: {user['bet']}")
    except Exception as e:
        logger.error(f"Bet callback error: {e}")

# ==========================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ==========================================
def setup_webhook():
    try:
        bot.remove_webhook()
        bot.set_webhook(
            url=f"{VERCEL_URL}/api/webhook",
            secret_token=WEBHOOK_SECRET
        )
        logger.info(f"✅ Вебхук установлен на {VERCEL_URL}/api/webhook")
    except Exception as e:
        logger.error(f"Webhook setup error: {e}")

if __name__ == '__main__':
    # Локальный режим (без вебхука)
    bot.remove_webhook()
    bot.polling(none_stop=True)
else:
    # Режим Vercel (с вебхуком)
    setup_webhook()

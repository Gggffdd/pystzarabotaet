import os
import random
import logging
from flask import Flask, request, jsonify
import telebot
from telebot import types

# ==========================================
# НАСТРОЙКА ПРИЛОЖЕНИЯ
# ==========================================
app = Flask(__name__)

# Конфигурация
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
WEBHOOK_SECRET = os.environ['WEBHOOK_SECRET']
VERCEL_URL = os.environ.get('VERCEL_URL', 'https://pystzarabotaet.vercel.app')

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# ИГРОВАЯ ЛОГИКА
# ==========================================
SLOT_SYMBOLS = ['🍒', '🍋', '🍇', '🍉', '🔔', '💎', '7️⃣', '🐶']
INITIAL_BALANCE = 1000
MIN_BET = 10
MAX_BET = 500

# Временное хранилище (в продакшене используйте БД)
users_db = {}

def get_user(user_id):
    """Получение или создание пользователя"""
    if user_id not in users_db:
        users_db[user_id] = {
            'balance': INITIAL_BALANCE,
            'bet': 100
        }
    return users_db[user_id]

# ==========================================
# ВЕБ-ЭНДПОИНТЫ
# ==========================================
@app.route('/')
def home():
    """Проверочная страница"""
    return jsonify({
        "status": "running",
        "bot": "Dog House Slots",
        "domain": VERCEL_URL
    })

@app.route('/api/health')
def health_check():
    """Проверка работоспособности API"""
    return jsonify({
        "status": "ok",
        "telegram": "connected",
        "webhook": "active"
    })

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхука от Telegram"""
    # Проверка секретного ключа
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != WEBHOOK_SECRET:
        logger.warning("Неавторизованный запрос вебхука")
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return jsonify({"error": "Internal server error"}), 500

# ==========================================
# КОМАНДЫ БОТА
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команды /start"""
    try:
        user = get_user(message.from_user.id)
        bot.send_message(
            message.chat.id,
            f"🎰 Добро пожаловать в Dog House Slots!\n\n"
            f"💰 Баланс: {user['balance']} монет\n"
            f"🪙 Текущая ставка: {user['bet']} монет\n\n"
            "Используйте команды:\n"
            "/spin - Крутить слоты\n"
            "/bet - Изменить ставку",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка в send_welcome: {e}")

@bot.message_handler(commands=['spin'])
def spin(message):
    """Обработчик игры"""
    try:
        user = get_user(message.from_user.id)
        
        if user['balance'] < user['bet']:
            return bot.send_message(message.chat.id, "❌ Недостаточно средств!")
        
        # Генерация результата
        result = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
        win = 100 if len(set(result)) == 1 else 0  # Упрощенная логика выигрыша
        
        # Обновление баланса
        user['balance'] += win - user['bet']
        
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
        logger.error(f"Ошибка в spin: {e}")

@bot.message_handler(commands=['bet'])
def change_bet(message):
    """Изменение ставки"""
    try:
        user = get_user(message.from_user.id)
        markup = types.InlineKeyboardMarkup()
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
        logger.error(f"Ошибка в change_bet: {e}")

# ==========================================
# CALLBACK-ОБРАБОТЧИКИ
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('bet_'))
def bet_callback(call):
    """Обработчик изменения ставки"""
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
        logger.error(f"Ошибка в bet_callback: {e}")

# ==========================================
# НАСТРОЙКА ВЕБХУКА
# ==========================================
def setup_webhook():
    """Установка вебхука при запуске"""
    try:
        bot.remove_webhook()
        bot.set_webhook(
            url=f"{VERCEL_URL}/api/webhook",
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )
        logger.info(f"✅ Вебхук установлен на {VERCEL_URL}/api/webhook")
    except Exception as e:
        logger.error(f"Ошибка настройки вебхука: {e}")

# Автоматическая настройка при запуске на Vercel
if os.environ.get('VERCEL') == '1':
    setup_webhook()
else:
    # Локальный режим для разработки
    if __name__ == '__main__':
        bot.remove_webhook()
        bot.polling(none_stop=True)

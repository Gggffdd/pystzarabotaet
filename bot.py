from flask import Flask, request, jsonify
import os
import telebot
import logging

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])

# Проверочный эндпоинт
@app.route('/')
def home():
    return "🎰 Слот-бот готов к работе! Домен: pystzarabotaet.vercel.app"

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok", "domain": "pystzarabotaet.vercel.app"})

# Вебхук для Telegram
@app.route('/api/webhook', methods=['POST'])
def webhook():
    try:
        # Проверка секретного ключа
        if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != os.environ['WEBHOOK_SECRET']:
            logger.warning("Неавторизованный запрос вебхука")
            return jsonify({"error": "Unauthorized"}), 403
        
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_message(
            message.chat.id,
            "🎉 Бот успешно работает на Vercel!\n"
            f"Домен: pystzarabotaet.vercel.app\n\n"
            "Отправьте /spin для теста игры"
        )
    except Exception as e:
        logger.error(f"Ошибка команды start: {e}")

# Команда /spin (тестовая)
@bot.message_handler(commands=['spin'])
def spin(message):
    try:
        symbols = ['🍒', '🍋', '💎', '7️⃣']
        result = random.choices(symbols, k=3)
        win = "100 (тест)" if len(set(result)) == 1 else "0 (тест)"
        
        bot.send_message(
            message.chat.id,
            f"🎰 Результат: {' '.join(result)}\n"
            f"💰 Выигрыш: {win}\n\n"
            "Бот работает корректно!"
        )
    except Exception as e:
        logger.error(f"Ошибка команды spin: {e}")

# Настройка вебхука при деплое
if __name__ == '__main__':
    bot.remove_webhook()
    bot.polling(none_stop=True)
else:
    bot.remove_webhook()
    bot.set_webhook(
        url=f"https://pystzarabotaet.vercel.app/api/webhook",
        secret_token=os.environ['WEBHOOK_SECRET']
    )
    logger.info("Вебхук установлен для Vercel")

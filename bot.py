from flask import Flask, request, jsonify
import telebot
import logging

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telebot.TeleBot('7523520150:AAGMPibPAl8D0I0E6ZeNR3zuIp0qKcshXN0')

# Проверочный эндпоинт
@app.route('/')
def home():
    return "Главная страница бота работает!"

# Эндпоинт для проверки
@app.route('/ping')
def ping():
    return jsonify({"status": "ok", "message": "pong"})

# Вебхук для Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бот работает! Это ответ на /start")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
else:
    # Конфигурация для Vercel
    bot.remove_webhook()
    bot.set_webhook(url='https://pystzarabotaet.vercel.app/webhook')

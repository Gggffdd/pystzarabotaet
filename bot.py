from flask import Flask, request, jsonify
import os
import telebot

app = Flask(__name__)
bot = telebot.TeleBot(os.environ['7523520150:AAGMPibPAl8D0I0E6ZeNR3zuIp0qKcshXN0'])

# Тестовый маршрут для проверки
@app.route('/test')
def test():
    return jsonify({"status": "ok", "message": "API работает"}), 200

# Основной маршрут для вебхука
@app.route('/api/webhook', methods=['POST'])
def webhook():
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != os.environ['WEBHOOK_SECRET']:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот успешно подключен!")

# Инициализация вебхука
def setup_webhook():
    bot.remove_webhook()
    webhook_url = f"{os.environ['VERCEL_URL']}/api/webhook"
    bot.set_webhook(
        url=webhook_url,
        secret_token=os.environ['WEBHOOK_SECRET']
    )
    print(f"Webhook установлен на: {webhook_url}")

# Для локального тестирования
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
else:
    setup_webhook()

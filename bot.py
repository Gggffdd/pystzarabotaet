from flask import Flask, request
import os
import telebot

app = Flask(__name__)
bot = telebot.TeleBot(os.environ['7523520150:AAGMPibPAl8D0I0E6ZeNR3zuIp0qKcshXN0'])

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != os.environ['WEBHOOK_SECRET']:
        return "Unauthorized", 403
    
    json_data = request.get_json()
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бот работает! Тест вебхука пройден")

if __name__ == '__main__':
    app.run()
else:
    # Конфигурация для Vercel
    bot.remove_webhook()
    bot.set_webhook(
        url=os.environ['VERCEL_URL'] + '/webhook',
        secret_token=os.environ['WEBHOOK_SECRET']
    )
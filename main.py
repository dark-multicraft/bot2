import os
import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession
# from googletrans import Translator # googletransは不要になるのでコメントアウトまたは削除
from dotenv import load_dotenv
from flask import Flask, request
import asyncio
import threading
import sys

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数から設定を読み込む
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
TELEGRAM_CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
STRING_SESSION = os.getenv('STRING_SESSION', None)

# ★ここから追加・変更★
# GAS Web AppのURLを環境変数から読み込む
GAS_TRANSLATION_URL = os.getenv('GAS_TRANSLATION_URL')
if not GAS_TRANSLATION_URL:
    print("Error: GAS_TRANSLATION_URL environment variable is not set.")
    print("Please set GAS_TRANSLATION_URL with your deployed GAS Web App URL.")
    sys.exit(1)
# ★ここまで追加・変更★

# Google翻訳の初期化 (不要になるのでコメントアウトまたは削除)
# translator = Translator()

# Telethonクライアントの初期化
if not STRING_SESSION:
    print("Error: STRING_SESSION environment variable is not set.")
    print("Please set STRING_SESSION with your Telegram session string.")
    sys.exit(1)

session_object = StringSession(STRING_SESSION)
client = TelegramClient(session_object, API_ID, API_HASH)

# Flaskアプリの初期化
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Bot is running!', 200

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def send_discord_message(message):
    """Discordにメッセージを送信するヘルパー関数"""
    try:
        payload = {'content': message}
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Successfully sent message to Discord: {message}")
    except Exception as e:
        print(f"Failed to send message to Discord: {e}")

# ★ここから変更★
def translate_and_send_to_discord(message_text):
    """メッセージを翻訳し、Discordに送信する"""
    if not message_text:
        return

    try:
        # GAS Web Appを呼び出して翻訳
        params = {
            'text': message_text,
            'targetLang': 'ja' # 日本語に翻訳
        }
        response = requests.get(GAS_TRANSLATION_URL, params=params)
        response.raise_for_status() # HTTPエラーがあれば例外を発生

        translated_text = response.text
        
        if translated_text:
            print(f"Original: {message_text}")
            print(f"Translated (via GAS): {translated_text}")

            # Discord Webhookに送信
            payload = {'content': translated_text}
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            response.raise_or_status() # エラーがあれば例外を発生させる
            print("Successfully sent to Discord.")
        else:
            print("Translation failed via GAS.")

    except Exception as e:
        print(f"An error occurred during translation or sending to Discord: {e}")
# ★ここまで変更★

@client.on(events.NewMessage(chats=TELEGRAM_CHANNEL_ID))
async def handler(event):
    """新しいメッセージを検知して処理する"""
    print("New message received!")
    await client.send_read_acknowledge(event.message.peer_id, event.message)
    translate_and_send_to_discord(event.message.message)

async def main():
    """メインの実行関数"""
    # 接続し、準備ができるまで待つ
    await client.start()
    print("Client Created and Connected!")
    
    # ボット起動時にDiscordにメッセージを送信
    send_discord_message("Telegram bot has started!")

    # Flaskアプリを別スレッドで起動
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # 接続が切れないように待機
    await client.run_until_disconnected()

if __name__ == '__main__':
    # イベントループを開始
    asyncio.run(main())
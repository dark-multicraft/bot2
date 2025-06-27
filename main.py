
import os
import requests
from telethon import TelegramClient, events
from googletrans import Translator
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数から設定を読み込む
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
TELEGRAM_CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')

# Google翻訳の初期化
translator = Translator()

# Telethonクライアントの初期化
# Renderで実行する場合、セッションファイルは永続化されない可能性があるため、
# 起動のたびに電話番号やパスワードの入力が必要になる場合があります。
# 初回実行時にローカルで.sessionファイルを生成し、それをRenderにアップロードする方法もあります。
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

def translate_and_send_to_discord(message_text):
    """メッセージを翻訳し、Discordに送信する"""
    if not message_text:
        return

    try:
        # メッセージを日本語に翻訳
        translated = translator.translate(message_text, dest='ja')
        
        if translated and translated.text:
            print(f"Original: {message_text}")
            print(f"Translated: {translated.text}")

            # Discord Webhookに送信
            payload = {'content': translated.text}
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            response.raise_for_status() # エラーがあれば例外を発生させる
            print("Successfully sent to Discord.")
        else:
            print("Translation failed.")

    except Exception as e:
        print(f"An error occurred: {e}")

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
    
    # 接続が切れないように待機
    await client.run_until_disconnected()

if __name__ == '__main__':
    # イベントループを開始
    import asyncio
    asyncio.run(main())

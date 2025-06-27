import os
import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession # 追加
from googletrans import Translator
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数から設定を読み込む
API_ID = int(os.getenv('API_ID')) # intに変換
API_HASH = os.getenv('API_HASH')
TELEGRAM_CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
# SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session') # 削除またはコメントアウト
STRING_SESSION = os.getenv('STRING_SESSION', None) # 追加

# Google翻訳の初期化
translator = Translator()

# Telethonクライアントの初期化
if STRING_SESSION:
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
else:
    # 初回実行時やStringSessionがない場合、通常のセッション名で起動
    # この場合、ローカルで一度実行してセッション文字列を取得する必要があります
    client = TelegramClient('telegram_session', API_ID, API_HASH)


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
    
    # StringSessionが設定されていない場合、セッション文字列を表示
    if not STRING_SESSION:
        print("Please save this string as STRING_SESSION environment variable:")
        print(client.session.export_string())

    # 接続が切れないように待機
    await client.run_until_disconnected()

if __name__ == '__main__':
    # イベントループを開始
    import asyncio
    asyncio.run(main())
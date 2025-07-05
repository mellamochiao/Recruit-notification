import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# 載入 .env 環境變數
load_dotenv()

URL = 'https://www.stat.ncku.edu.tw/ssc/'
KEYWORD = '徵電訪員'
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

def send_discord_message(content):
    if not WEBHOOK_URL:
        print("找不到 Webhook URL，請檢查 .env 檔案")
        return
    data = {"content": content}
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("✅ 已發送 Discord 通知")
    else:
        print(f"❌ 傳送失敗：{response.status_code}\n{response.text}")

def check_site():
    print("正在檢查網站內容...")
    try:
        response = requests.get(URL, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        if KEYWORD in soup.text:
            print("偵測到關鍵字出現")
            send_discord_message(f"📢 『{KEYWORD}』出現！\n👉 {URL}")
        else:
            print("沒有發現關鍵字")
    except Exception as e:
        print(f"發生錯誤：{e}")

if __name__ == '__main__':
    check_site()

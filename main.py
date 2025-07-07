import certifi
import os
from dotenv import load_dotenv
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 建立不驗證 SSL 的 requests session
class UnsafeAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = ssl._create_unverified_context()
        return super().init_poolmanager(*args, **kwargs)

requests_session = requests.Session()
requests_session.mount('https://', UnsafeAdapter())

load_dotenv()

URL = 'https://www.stat.ncku.edu.tw/ssc/'
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

def send_discord_message(content):
    if not WEBHOOK_URL:
        print("❌ 沒有設定 DISCORD_WEBHOOK")
        return
    response = requests_session.post(WEBHOOK_URL, json={"content": content}, verify=certifi.where())
    if response.status_code == 204:
        print("✅ 通知已發送")
    else:
        print(f"❌ 通知失敗：{response.status_code}\n{response.text}")

def check_news():
    print("🔍 正在檢查網站最新消息...")
    try:
        res = requests_session.get(URL, timeout=10, verify=certifi.where())
        soup = BeautifulSoup(res.text, 'html.parser')

        items = soup.select('.inews-w li')
        print(f"📝 共抓到 {len(items)} 筆公告")

        today = datetime.today().date()
        threshold = today - timedelta(days=2)
        new_count = 0  # 統計幾筆符合條件的公告

        for item in items:
            date_block = item.select_one('.news-day')
            if not date_block:
                continue

            span = date_block.select_one('span')
            if not span:
                continue

            try:
                month_day = span.text.strip()  # 例如 "06.03"
                year_text = date_block.get_text(strip=True).replace(month_day, '')
                year = int(year_text)
                month, day = map(int, month_day.split('.'))
                post_date = datetime(year, month, day).date()
            except:
                continue  # 跳過無法解析的

            if post_date >= threshold:
                title_tag = item.select_one('.news-title a')
                title = title_tag.text.strip() if title_tag else "(無標題)"
                link = title_tag['href'] if title_tag and 'href' in title_tag.attrs else URL

                message = (
                    f"📢 有新公告！（發布日：{post_date.strftime('%m/%d')})\n\n"
                    f"🔹 標題：{title}\n"
                    f"🔗 查看連結：{link}"
                )
                send_discord_message(message)
                new_count += 1

        if new_count == 0:
            print("📭 沒有三天內的新公告")
        else:
            print(f"📬 本次發送了 {new_count} 筆通知")

    except Exception as e:
        print(f"⚠️ 發生錯誤：{e}")

if __name__ == '__main__':
    check_news()


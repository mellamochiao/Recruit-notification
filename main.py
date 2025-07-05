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

# 關閉警告
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

        # 抓所有最新消息區塊
        items = soup.select('.inews-w li')

        # 今天日期 & 範圍
        today = datetime.today().date()
        threshold = today - timedelta(days=2)  # 三天內都通知

        for item in items:
            # 取日期（.news-day 中 span 為月日，尾部為年）
            date_block = item.select_one('.news-day')
            if not date_block: continue

            span = date_block.select_one('span')
            if not span: continue

            try:
                month_day = span.text.strip()  # 例如 "06.03"
                year_text = date_block.get_text(strip=True).replace(month_day, '')
                year = int(year_text)
                month, day = map(int, month_day.split('.'))
                post_date = datetime(year, month, day).date()
            except:
                continue  # 無法解析日期就跳過

            if post_date >= threshold:
                # 抓標題與連結
                title_tag = item.select_one('.news-title a')
                title = title_tag.text.strip() if title_tag else "(無標題)"
                link = title_tag['href'] if title_tag and 'href' in title_tag.attrs else URL

                message = (
                    f"📢 有新公告！（發布日：{post_date.strftime('%m/%d')})\n\n"
                    f"🔹 標題：{title}\n"
                    f"🔗 查看連結：{link}"
                )
                send_discord_message(message)

    except Exception as e:
        print(f"⚠️ 發生錯誤：{e}")

if __name__ == '__main__':
    check_news()
import schedule
import time
import requests
from colorama import init, Fore
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import jdatetime
import os

init(autoreset=True)

Base = declarative_base()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "bot.db")
os.makedirs(BASE_DIR, exist_ok=True)
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

class Request(Base):
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer)
    user_id = Column(Integer)
    currency = Column(String)
    amount = Column(String)
    price = Column(String)
    created_date = Column(String)
    post_id = Column(Integer)

class RequestsDB:
    def __init__(self):
        self.session = Session()

    def get_requets_by_currency(self, currency, type):
        return [request.__dict__ for request in self.session.query(Request).filter_by(currency=currency).all()]

def generate_euro_daily_report():
    return generate_currency_daily_report("💶 یورو", "یورو")

def generate_tether_daily_report():
    return generate_currency_daily_report("💎 تتر", "تتر")

def generate_currency_daily_report(currency_name, currency_nickname):
    requests_db = RequestsDB()
    today = jdatetime.date.today().strftime("%Y-%m-%d")
    currency_requests = [
        req for req in requests_db.get_requets_by_currency(currency_name, None)
        if req['created_date'].startswith(today)
    ]
    
    if not currency_requests:
        return f"No {currency_nickname} transactions today."
    
    prices = []
    for req in currency_requests:
        if req['price'] != "توافقی🤝" and req['price'] is not None:
            try:
                prices.append(float(req['price']))
            except ValueError:
                print(Fore.RED + f"Could not convert price '{req['price']}' to float for request {req['request_id']}.")
                continue
    
    if not prices:
        return f"No valid prices for {currency_nickname} transactions today."
    
    start_price = prices[0]
    start_request = next((req for req in currency_requests if req['price'] is not None and req['price'] != "توافقی🤝" and  float(req['price']) >= 30000 and float(req['price']) == start_price), None)
    start_post_id = start_request['post_id'] if start_request else None

    max_price = max(prices)
    max_request = next((req for req in currency_requests if req['price'] is not None and req['price'] != "توافقی🤝" and float(req['price']) >= 30000 and float(req['price']) == max_price), None)
    max_post_id = max_request['post_id'] if max_request else None

    min_price = min(prices)
    min_request = next((req for req in currency_requests if req['price'] is not None and req['price'] != "توافقی🤝" and float(req['price']) >= 30000 and float(req['price']) == min_price), None)
    min_post_id = min_request['post_id'] if min_request else None

    end_price = prices[-1]
    end_request = next((req for req in currency_requests if req['price'] is not None and req['price'] != "توافقی🤝" and float(req['price']) >= 30000 and float(req['price']) == end_price), None)
    end_post_id = end_request['post_id'] if end_request else None
    
    if currency_nickname == "یورو":
        link = "https://t.me/TabadolArz_Trades/"
    else:
        link = "https://t.me/TabadolArz_Trades/"

    report = f"""📌 گزارش معاملات {currency_name}

تاریخ: {jdatetime.date.today().strftime("%Y/%m/%d")}
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــ

◾️ شروع قیمت: <a href="{link}{start_post_id}">{start_price:,.0f}</a>
◾️ بیشترین قیمت: <a href="{link}{max_post_id}">{max_price:,.0f}</a>
◾️ کمترین قیمت: <a href="{link}{min_post_id}">{min_price:,.0f}</a>
◾️ پایان قیمت: <a href="{link}{end_post_id}">{end_price:,.0f}</a>

<a href="https://t.me/TabadolArz_Robot">💎 درگاه امن معاملات ارزی</a>"""

    return report

def send_telegram_message(message):
    bot_token = "7142012125:AAHlSGZiO40Mu6v2X4LcCSJqFcLFqNk4rpM"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": "-1002075798363",
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    return response.json()

def send_daily_report():
    euro_report = generate_euro_daily_report()
    tether_report = generate_tether_daily_report()
    
    send_telegram_message(euro_report)
    send_telegram_message(tether_report)
    
    print(Fore.GREEN + "Daily reports sent successfully!")

def send_tether_daily_report():
    tether_report = generate_tether_daily_report()
    send_telegram_message(tether_report)
    print(Fore.GREEN + "Tether daily report sent successfully!")

schedule.every().day.at("23:59").do(send_daily_report)
schedule.every().day.at("21:00").do(send_tether_daily_report)
# schedule.every(4).seconds.do(send_daily_report)


if __name__ == "__main__":
    print(Fore.CYAN + "Bot started. Waiting for scheduled time to send daily report...")
    while True:
        schedule.run_pending()
        time.sleep(60)
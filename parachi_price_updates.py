import arabic_reshaper
from bidi.algorithm import get_display
import os
import requests
import json
import jdatetime
import pytz
import time
import sys
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from colorama import init, Fore, Style
import re
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

init(autoreset=True)

TELEGRAM_TOKEN = "8456056506:AAFrKONGT5WeXVye6u6nvsJ_rAl3BFnx3Ic"
TEST_TELEGRAM_ID = "5361491365"

TELEGRAM_CHAT_IDS = [
    "-1002656752612",
    "-1003366343939",
    "-1003359360164",
    "-1004445644725",
    "-1004352787198",
    "-1004243655967",
    "-1004492583899",
    "-1003850122326",
    "-1003797637924",
    "-1003342367363",
    "-1004496736485",
    "-1003815641753"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

FONT_PATH = os.path.join(FONTS_DIR, "AbarMidFaNum-Bold.ttf")
TEMPLATE_PATH = os.path.join(IMAGES_DIR, "new_banner_v2.png")
OUTPUT_PATH = os.path.join(IMAGES_DIR, "output.jpg")

API_URL = "https://navasan.milaadfarzian.workers.dev/"
TEHRAN_TZ = pytz.timezone('Asia/Tehran')

ORDERED_CURRENCIES = [
    ("eur", "یورو", "🇪🇺"),
    ("gbp", "پوند انگلیس", "🇬🇧"),
    ("try", "لیر ترکیه", "🇹🇷"),
    ("rub", "روبل روسیه", "🇷🇺"),
    ("cny", "یوآن چین", "🇨🇳"),
    ("cad", "دلار کانادا", "🇨🇦"),
    ("aed", "درهم امارات", "🇦🇪"),
    ("dkk", "کرون دانمارک", "🇩🇰"),
    ("sek", "کرون سوئد", "🇸🇪"),
    ("nok", "کرون نروژ", "🇳🇴"),
    ("nzd", "دلار نیوزلند", "🇳🇿")
]

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

def to_persian_numbers(s):
    s = str(s).replace(",", "٬")
    return "".join(PERSIAN_DIGITS[int(c)] if c.isdigit() else c for c in str(s))

def format_number(currency_key, data):
    try:
        val = data.get(currency_key, {}).get("value", 0)
        num_val = int(float(val)) if val else 0
        return to_persian_numbers(f"{num_val:,}")
    except:
        return to_persian_numbers("--")

def format_number_with_commas(num):
    try:
        if isinstance(num, str):
            num = float(num.replace(',', ''))
        if num >= 1000000:
            num = 999999
        return f"{int(num):,}"
    except (ValueError, TypeError):
        return str(num)

def format_time(time_str):
    try:
        if re.match(r'^\d{1,2}:\d{2}$', str(time_str)):
            return str(time_str)
        if str(time_str).isdigit():
            hours = int(time_str) // 60
            minutes = int(time_str) % 60
            return f"{hours:02d}:{minutes:02d}"
        return str(time_str)
    except:
        return str(time_str)

def format_date(date_str):
    try:
        if re.match(r'^\d{4}/\d{2}/\d{2}$', str(date_str)):
            return str(date_str)
        if str(date_str).isdigit():
            date_str = str(date_str)
            if len(date_str) == 8:
                return f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:8]}"
        return str(date_str)
    except:
        return str(date_str)

def print_currency_table(data):
    print(Fore.YELLOW + "\n================ CURRENCY TABLE ================\n")
    for i, (key, label, emoji) in enumerate(ORDERED_CURRENCIES):
        value = format_number(key, data)
        color = [Fore.CYAN, Fore.GREEN, Fore.MAGENTA, Fore.BLUE][i % 4]
        print(color + f"{emoji} {label} → {value} تومان")
    print(Fore.YELLOW + "\n===============================================\n")

def create_caption(data):
    now_j = jdatetime.datetime.now(TEHRAN_TZ)
    date_str = to_persian_numbers(now_j.strftime("%Y/%m/%d"))
    time_label = "ظهر" if 11 <= now_j.hour <= 16 else "عصر"
    if now_j.hour >= 19 or now_j.hour < 5:
        time_label = "شب"
    lines = [f"<b>اعلام نرخ ارز - {time_label} {date_str}</b>", ""]
    lines.append("")
    lines.append('<a href="https://t.me/Parachi_Exchange">📢 پاراچی | دروازه بانکداری جهانی</a>')
    return "\n".join(lines)

def get_buttons():
    return json.dumps({
        "inline_keyboard": [[
            {"text": "📞 02191031557", "callback_data": "phone"},
            {"text": "📱 ورود به پلتفرم", "url": "https://app.parachi.com"}
        ]]
    })

_font_cache = {}

def get_font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(FONT_PATH, size)
    return _font_cache[size]

def stamp_text(draw, x, y, text, size, color="#ffffff", is_rtl=False, anchor="mm"):
    font = get_font(size)
    text_str = str(text)
    
    # Check if string is explicitly RTL or contains Persian/Arabic characters
    has_arabic = is_rtl or any('\u0600' <= c <= '\u06FF' for c in text_str)
    
    if has_arabic:
        draw.text(
            xy=(x, y),
            text=text_str,
            font=font,
            fill=color,
            anchor=anchor,
            direction="rtl",  # Handled natively by libraqm
            language="fa"     # Persian rules for shaping
        )
    else:
        draw.text(
            xy=(x, y),
            text=text_str,
            font=font,
            fill=color,
            anchor=anchor
        )

def fetch_currency_data_with_retry(max_retries=10):
    for attempt in range(max_retries):
        try:
            print(Fore.CYAN + f"📡 Fetching data from API (Attempt {attempt + 1}/{max_retries})...")
            res = requests.get(API_URL, timeout=10)
            data = res.json()
            
            has_zero = False
            zero_currencies = []
            for key, _, _ in ORDERED_CURRENCIES:
                val = data.get(key, {}).get("value", 0)
                if val == 0 or val is None:
                    has_zero = True
                    zero_currencies.append(key)
            
            if has_zero:
                print(Fore.YELLOW + f"⚠️ Zero values detected for: {', '.join(zero_currencies)}")
                if attempt < max_retries - 1:
                    print(Fore.YELLOW + f"🔄 Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2)
                    continue
                else:
                    print(Fore.RED + f"❌ Zero values still present after {max_retries} attempts. Using last available data.")
                    return data
            else:
                print(Fore.GREEN + f"✅ All currency values are valid (Attempt {attempt + 1})")
                return data
                
        except Exception as e:
            print(Fore.RED + f"❌ Fetch attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(Fore.YELLOW + f"🔄 Retrying... ({attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                print(Fore.RED + f"❌ All {max_retries} attempts failed")
                return None
    
    return None

def has_zero_values(data):
    if not data:
        return True
    for key, _, _ in ORDERED_CURRENCIES:
        val = data.get(key, {}).get("value", 0)
        if val == 0 or val is None:
            return True
    return False

def generate_image(data):
    try:
        img = Image.open(TEMPLATE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)
        now_j = jdatetime.datetime.now(TEHRAN_TZ)
        
        current_hour = now_j.strftime("%H:%M")
        persian_date = to_persian_numbers(now_j.strftime("%Y/%m/%d"))

        nodes_map = {
            "text_1": {"x": 1084, "y": 354, "size": 40, "color": "#ffffff", "rtl": False, "anchor": "mm"},
            "text_2": {"x": 1146, "y": 537, "size": 40, "color": "#ffffff", "rtl": False, "anchor": "mm"},
            "text_3": {"y": 150, "size": 56, "color": "#ffffff"},
            "text_4": {"y": 250, "size": 56, "color": "#ffffff"},
            "text_5": {"y": 345, "size": 56, "color": "#ffffff"},
            "text_6": {"y": 449, "size": 56, "color": "#ffffff"},
            "text_7": {"y": 540, "size": 56, "color": "#ffffff"},
            "text_8": {"y": 650, "size": 56, "color": "#ffffff"},
            "text_9": {"y": 750, "size": 56, "color": "#ffffff"},
            "text_10": {"y": 850, "size": 56, "color": "#ffffff"},
            "text_11": {"y": 940, "size": 56, "color": "#ffffff"},
            "text_12": {"y": 1039, "size": 56, "color": "#ffffff"},
            "text_13": {"y": 1142, "size": 56, "color": "#ffffff"},
        }

        currency_to_node = {
            "eur": "text_3",
            "gbp": "text_4",
            "try": "text_5",
            "rub": "text_6",
            "cny": "text_7",
            "cad": "text_8",
            "aed": "text_9",
            "dkk": "text_10",
            "sek": "text_11",
            "nok": "text_12",
            "nzd": "text_13"
        }

        for currency_key, node_key in currency_to_node.items():
            cfg = nodes_map[node_key]
            value = format_number(currency_key, data)
            y_center = cfg["y"] + 6
            
            stamp_text(
                draw, 
                250, 
                y_center, 
                value,
                cfg["size"], 
                cfg["color"],
                is_rtl=False,
                anchor="lm"
            )
            
            stamp_text(
                draw,
                230,
                y_center,
                "تومان",
                40,
                cfg["color"],
                is_rtl=True,
                anchor="rm"
            )

        cfg_time = nodes_map["text_1"]
        stamp_text(draw, cfg_time["x"], cfg_time["y"], current_hour, cfg_time["size"], cfg_time["color"], is_rtl=cfg_time["rtl"], anchor=cfg_time["anchor"])
        
        cfg_date = nodes_map["text_2"]
        stamp_text(draw, cfg_date["x"], cfg_date["y"], persian_date, cfg_date["size"], cfg_date["color"], is_rtl=cfg_date["rtl"], anchor=cfg_date["anchor"])

        img.save(OUTPUT_PATH, quality=95)
        print(Fore.GREEN + f"Image generated successfully ✔ {OUTPUT_PATH}")
        return OUTPUT_PATH
    except Exception as e:
        print(Fore.RED + f"Image Error: {e}")
        return None

def send_message_and_get_id(chat_id, image_path=None, caption=""):
    buttons = get_buttons()
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML", "reply_markup": buttons}
    try:
        with open(image_path, 'rb') as photo:
            res = requests.post(url, data=payload, files={'photo': photo}, timeout=30)
        if res.ok:
            result = res.json()
            message_id = result.get('result', {}).get('message_id')
            print(Fore.GREEN + f"Sent successfully ✔ | Chat: {chat_id} | Message ID: {message_id} | Status: {res.status_code}")
            return message_id
        else:
            print(Fore.RED + f"Send failed ✖ | Chat: {chat_id} | Status: {res.status_code} | Response: {res.text}")
            return None
    except Exception as e:
        print(Fore.RED + f"Send Error: {e}")
        return None

def delete_message_after_delay(chat_id, message_id, delay_seconds=20):
    time.sleep(delay_seconds)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
    payload = {"chat_id": chat_id, "message_id": message_id}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.ok:
            print(Fore.YELLOW + f"Message {message_id} deleted from {chat_id} after {delay_seconds} seconds ✔")
        else:
            print(Fore.RED + f"Failed to delete message {message_id}: {res.status_code} - {res.text}")
    except Exception as e:
        print(Fore.RED + f"Delete error: {e}")

def send_telegram(chat_id, image_path=None, caption=""):
    buttons = get_buttons()
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML", "reply_markup": buttons}
    try:
        with open(image_path, 'rb') as photo:
            res = requests.post(url, data=payload, files={'photo': photo}, timeout=30)
        if res.ok:
            print(Fore.GREEN + f"Sent successfully ✔ | Chat: {chat_id} | Status: {res.status_code}")
        else:
            print(Fore.RED + f"Send failed ✖ | Chat: {chat_id} | Status: {res.status_code} | Response: {res.text}")
    except Exception as e:
        print(Fore.RED + f"Send Error: {e}")

def send_test_telegram(image_path, caption):
    print(Fore.CYAN + "\n🔵 Sending TEST message to Telegram...")
    message_id = send_message_and_get_id(TEST_TELEGRAM_ID, image_path, caption)
    if message_id:
        print(Fore.YELLOW + f"⏳ Will delete message in 20 seconds...")
        threading.Thread(target=delete_message_after_delay, args=(TEST_TELEGRAM_ID, message_id, 20), daemon=True).start()
    else:
        print(Fore.RED + "❌ Failed to send test message to Telegram")

def send_to_all_channels(image_path, caption):
    for chat_id in TELEGRAM_CHAT_IDS:
        print(Fore.CYAN + f"Sending to Telegram destination: {chat_id}...")
        send_telegram(chat_id, image_path, caption)

def run_job(target_type="all"):
    # Log the exact Tehran time when the job fires
    now_tehran = datetime.now(TEHRAN_TZ)
    print(Fore.GREEN + f"🕒 Job triggered at Tehran time: {now_tehran.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        data = fetch_currency_data_with_retry(max_retries=10)  # Now uses 10 retries
        
        if not data:
            print(Fore.RED + "❌ Failed to fetch data after 10 attempts. Skipping job.")
            return
        
        if has_zero_values(data):
            print(Fore.RED + f"❌ Zero values detected at {datetime.now(TEHRAN_TZ).strftime('%Y-%m-%d %H:%M:%S')} – skipping send to avoid invalid data.")
            return
        
        img_path = generate_image(data)
        if not img_path:
            print(Fore.RED + "Skipping send due to image failure")
            return
        
        print_currency_table(data)
        caption = create_caption(data)
        
        if target_type == "test-telegram":
            send_test_telegram(img_path, caption)
        elif target_type == "test":
            print(Fore.YELLOW + "Legacy test mode: sending to Telegram test ID")
            send_telegram(TEST_TELEGRAM_ID, img_path, caption)
        else:
            send_to_all_channels(img_path, caption)
            
    except Exception as e:
        print(Fore.RED + f"Job failed: {e}")

# ========== MAIN ==========
if __name__ == "__main__":
    if "--testtelegram" in sys.argv:
        print(Fore.CYAN + "🚀 Running Telegram test mode (will delete after 20 seconds)...")
        run_job("test-telegram")
    elif "--test" in sys.argv:
        print(Fore.YELLOW + "🚀 Running legacy test mode...")
        run_job("test")
    elif "--now" in sys.argv:
        print(Fore.GREEN + "🚀 Running immediate job...")
        run_job("all")
    else:
        print(Fore.GREEN + "🤖 Bot Active. Scheduled for 12:00 and 20:00 Tehran time.")
        print(Fore.CYAN + "Available commands:")
        print(Fore.CYAN + "  --testtelegram  : Send test to Telegram (auto-delete after 20s)")
        print(Fore.CYAN + "  --test          : Legacy test mode")
        print(Fore.CYAN + "  --now           : Run immediately to Telegram channel")

        # Use APScheduler with explicit Tehran timezone
        scheduler = BlockingScheduler(timezone="Asia/Tehran")
        
        # Schedule daily at 12:00 and 20:00
        scheduler.add_job(lambda: run_job("all"), CronTrigger(hour=12, minute=0, timezone="Asia/Tehran"))
        scheduler.add_job(lambda: run_job("all"), CronTrigger(hour=20, minute=0, timezone="Asia/Tehran"))
        
        # Optional heartbeat every hour to prove the scheduler is running
        scheduler.add_job(
            lambda: print(Fore.CYAN + f"⏳ Scheduler heartbeat at {datetime.now(TEHRAN_TZ).strftime('%Y-%m-%d %H:%M:%S')}"),
            CronTrigger(minute=0, timezone="Asia/Tehran")
        )
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print(Fore.YELLOW + "Scheduler stopped.")
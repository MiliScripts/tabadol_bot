import arabic_reshaper
from bidi.algorithm import get_display
import requests
import json
import jdatetime
import pytz
import time
import sys
import os
import traceback
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import re

# --- APScheduler imports ---
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Added for polling ---
import asyncio
import aiohttp

BOT_TOKEN = "8591031707:AAFbgQIG8n-xXYttTQBp5VrzOvktX2gz0_A"
ADMIN_IDS = [51998101, 7352988550, 5361491365, 210178334, 982290123]

BASE_URL = "https://navasan.milaadfarzian.workers.dev/"
ENDPOINT = "last_currencies"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

FONT_PATH = os.path.join(FONTS_DIR, "AbarMidFaNum-Bold.ttf")
STORY_TEMPLATE = os.path.join(IMAGES_DIR, "new_story_v2.png")
STORY_OUTPUT = os.path.join(IMAGES_DIR, "output.jpg")

TEHRAN_TZ = pytz.timezone('Asia/Tehran')

LAST_SENT_DATE = None
LAST_SENT_PERIOD = None

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

_font_cache = {}

def get_font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(FONT_PATH, size)
    return _font_cache[size]

def stamp_text(draw, x, y, text, size, color="#ffffff", anchor="mm"):
    font = get_font(size)
    text_str = str(text)

    # Check if there are Persian/Arabic characters
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in text_str)

    if has_arabic:
        draw.text(
            (x, y),
            text_str,
            font=font,
            fill=color,
            anchor=anchor,
            direction="rtl",  # RAQM handles this natively now
            language="fa",    # Tells RAQM to use Persian shaping rules
        )
    else:
        draw.text(
            (x, y),
            text_str,
            font=font,
            fill=color,
            anchor=anchor,
        )

def fetch_data_with_retry(max_retries=10):
    """Fetch data with retry logic for zero values"""
    for attempt in range(max_retries):
        try:
            print(f"⏳ Fetching data from API (Attempt {attempt + 1}/{max_retries})...")
            response = requests.get(f"{BASE_URL}?endpoint={ENDPOINT}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if any currency has zero value
            has_zero = False
            zero_currencies = []
            for key, _, _ in ORDERED_CURRENCIES:
                val = data.get(key, {}).get("value", 0)
                if val == 0 or val is None:
                    has_zero = True
                    zero_currencies.append(key)
            
            if has_zero:
                print(f"⚠️ Zero values detected for: {', '.join(zero_currencies)}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2)
                    continue
                else:
                    print(f"❌ Zero values still present after {max_retries} attempts. Using last available data.")
                    return data
            else:
                print(f"✅ All currency values are valid (Attempt {attempt + 1})")
                return data
                
        except Exception as e:
            print(f"❌ Fetch attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying... ({attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"❌ All {max_retries} attempts failed")
                return None
    
    return None

def has_zero_values(data):
    """Check if any currency has zero value"""
    if not data:
        return True
    for key, _, _ in ORDERED_CURRENCIES:
        val = data.get(key, {}).get("value", 0)
        if val == 0 or val is None:
            return True
    return False

def create_story_image(data):
    try:
        print("🖌️ Checking files for image creation...")
        if not os.path.exists(STORY_TEMPLATE):
            print(f"❌ Template NOT FOUND: {STORY_TEMPLATE}")
            return None
        if not os.path.exists(FONT_PATH):
            print(f"❌ Font NOT FOUND: {FONT_PATH}")
            return None

        print("🖌️ Generating image...")
        img = Image.open(STORY_TEMPLATE).convert("RGB")
        draw = ImageDraw.Draw(img)

        nodes_map = {
            "text_1":  {"x": 282, "y": 535, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_2":  {"x": 282, "y": 623, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_3":  {"x": 282, "y": 708, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_4":  {"x": 282, "y": 792, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_5":  {"x": 282, "y": 878, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_6":  {"x": 282, "y": 960, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_7":  {"x": 282, "y": 1048, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_8":  {"x": 282, "y": 1133, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_9":  {"x": 282, "y": 1216, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_10": {"x": 282, "y": 1303, "size": 49, "color": "#ffffff", "anchor": "lm"},
            "text_11": {"x": 282, "y": 1389, "size": 49, "color": "#ffffff", "anchor": "lm"},
        }

        # Larger font for "تومان" (was 28, now 34)
        TOMAN_FONT_SIZE = 34
        # More space between "تومان" and the price (was 5, now 20)
        GAP = 20

        for i, (key, _, _) in enumerate(ORDERED_CURRENCIES):
            if i < 11:
                cfg = nodes_map[f"text_{i+1}"]
                price_text = format_number(key, data)
                color = cfg.get("color", "#ffffff")
                y = cfg["y"]
                x_price = cfg["x"]

                # 1) Draw "تومان" with larger font, anchored right, with a gap
                stamp_text(draw, x_price - GAP, y, "تومان", TOMAN_FONT_SIZE, color, "rm")

                # 2) Draw the price with original font, anchored left at the original x
                stamp_text(draw, x_price, y, price_text, cfg["size"], color, "lm")

        img.save(STORY_OUTPUT, quality=95)
        print(f"✅ Image saved successfully as {STORY_OUTPUT}")
        return STORY_OUTPUT

    except Exception as e:
        print(f"❌ Image generation error: {e}")
        traceback.print_exc()
        return None

def send_to_telegram(endpoint, admin_id, image_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}"
    print(f"🚀 Sending {endpoint} to ID: {admin_id}...")
    try:
        with open(image_path, "rb") as f:
            if endpoint == "sendPhoto":
                files = {"photo": f}
            else:
                files = {"document": f}
            
            data = {
                "chat_id": admin_id,
                "caption": caption,
                "parse_mode": "HTML",
            }
            res = requests.post(url, data=data, files=files, timeout=30)
            if res.status_code == 200:
                print(f"✅ Successfully sent {endpoint} to {admin_id}")
            else:
                print(f"❌ Telegram Error [{res.status_code}]: {res.text}")
    except Exception as e:
        print(f"❌ Exception in sending to Telegram: {e}")

def send_to_admin(admin_id, image_path, caption):
    send_to_telegram("sendPhoto", admin_id, image_path, caption)
    time.sleep(1)
    send_to_telegram("sendDocument", admin_id, image_path, caption)

def job():
    global LAST_SENT_DATE, LAST_SENT_PERIOD
    
    print("\n🔄 Starting job process...")
    tehran_now = datetime.now(TEHRAN_TZ)
    today = tehran_now.strftime("%Y-%m-%d")
    hour = tehran_now.hour
    period = "AM" if hour < 12 else "PM"

    if LAST_SENT_DATE == today and LAST_SENT_PERIOD == period:
        print("⏭️ Notice: Already sent for this period, skipping.")
        return

    # Fetch data with 10 retries
    data = fetch_data_with_retry(max_retries=10)
    
    if not data:
        print("❌ Failed to fetch data after 10 attempts. Aborting process.")
        return
    
    # Check if any zero values still exist
    if has_zero_values(data):
        print("❌ Zero values detected after retries. Skipping send to avoid showing invalid data.")
        print("⚠️ Not sending to admins to prevent showing zero prices.")
        return

    image = create_story_image(data)
    if not image:
        print("❌ Image creation failed, aborting process.")
        return

    date_str = tehran_now.strftime("%Y/%m/%d")
    period_txt = "صبح" if period == "AM" else "عصر"
    
    caption = f"📊 <b>نرخ ارز - {to_persian_numbers(date_str)} ({period_txt})</b>\n\n"
    for key, label, emoji in ORDERED_CURRENCIES:
        caption += f" {emoji} {label}: {format_number(key, data)} تومان\n"
    
    caption += "\n📱 @Parachi_Exchange"

    print(f"📬 Ready to send messages to {len(ADMIN_IDS)} admins...")
    for admin in ADMIN_IDS:
        send_to_admin(admin, image, caption)
        time.sleep(2)

    LAST_SENT_DATE = today
    LAST_SENT_PERIOD = period
    print("🎉 Job process finished completely.")

# ========== POLLING WITH AIOHTTP ==========
async def tg_api_request(method: str, payload: dict, files: dict = None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with aiohttp.ClientSession() as session:
        try:
            if files:
                data = aiohttp.FormData()
                for k, v in payload.items():
                    data.add_field(k, str(v))
                for fname, fobj in files.items():
                    data.add_field(fname, fobj, filename=os.path.basename(fobj.name))
                async with session.post(url, data=data, timeout=30) as resp:
                    return await resp.json()
            else:
                async with session.post(url, json=payload, timeout=30) as resp:
                    return await resp.json()
        except Exception as e:
            print(f"❌ TG API error: {e}")
            return None

async def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    await tg_api_request("sendMessage", payload)

async def answer_callback(callback_id, text=None):
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    await tg_api_request("answerCallbackQuery", payload)

# ---------- Handlers ----------
async def handle_start(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "📸 دریافت استوری الآن", "callback_data": "get_story"}]
        ]
    }
    await send_message(chat_id, "👋 سلام! برای دریافت آخرین نرخ‌ها، دکمه زیر را بزنید:", keyboard)

async def handle_get_story(callback_query):
    query_id = callback_query["id"]
    chat_id = callback_query["message"]["chat"]["id"]
    user_id = callback_query["from"]["id"]

    # Only admins can use this
    if user_id not in ADMIN_IDS:
        await answer_callback(query_id, "⛔ شما دسترسی ندارید.")
        return
    await answer_callback(query_id)  # acknowledge

    # 1. Fetch data (same as job)
    data = fetch_data_with_retry(max_retries=5)
    if not data or has_zero_values(data):
        await send_message(chat_id, "❌ خطا در دریافت داده‌ها. لطفاً بعداً تلاش کنید.")
        return

    # 2. Generate image (exact same function)
    image_path = create_story_image(data)
    if not image_path:
        await send_message(chat_id, "❌ خطا در ساخت تصویر.")
        return

    # 3. Build caption (same as job)
    tehran_now = datetime.now(TEHRAN_TZ)
    date_str = tehran_now.strftime("%Y/%m/%d")
    hour = tehran_now.hour
    period_txt = "صبح" if hour < 12 else "عصر"
    caption = f"📊 <b>نرخ ارز - {to_persian_numbers(date_str)} ({period_txt})</b>\n\n"
    for key, label, emoji in ORDERED_CURRENCIES:
        caption += f" {emoji} {label}: {format_number(key, data)} تومان\n"
    caption += "\n📱 @Parachi_Exchange"

    # 4. Send to the requester only (photo + document)
    # Use asyncio.to_thread to avoid blocking the event loop with the synchronous send function
    await asyncio.to_thread(send_to_telegram, "sendPhoto", chat_id, image_path, caption)
    await asyncio.sleep(1)
    await asyncio.to_thread(send_to_telegram, "sendDocument", chat_id, image_path, caption)

# ---------- Polling Loop ----------
async def poll_updates():
    offset = 0
    print("🤖 Starting polling for updates...")
    while True:
        try:
            result = await tg_api_request("getUpdates", {
                "offset": offset,
                "timeout": 30,
                "allowed_updates": ["message", "callback_query"]
            })
            if result and result.get("ok"):
                for update in result.get("result", []):
                    offset = update["update_id"] + 1
                    # Process each update in a separate task
                    asyncio.create_task(process_update(update))
            await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            await asyncio.sleep(5)

async def process_update(update):
    try:
        if "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            if text == "/start":
                await handle_start(chat_id)
        elif "callback_query" in update:
            cb = update["callback_query"]
            if cb["data"] == "get_story":
                await handle_get_story(cb)
    except Exception as e:
        print(f"❌ Error processing update: {e}")
        traceback.print_exc()

# ========== MAIN ==========
if __name__ == "__main__":
    if "--test" in sys.argv or "-t" in sys.argv:
        print("\n🧪 STARTING TEST MODE")
        data = fetch_data_with_retry(max_retries=3)
        if data and not has_zero_values(data):
            image = create_story_image(data)
            if image:
                send_to_telegram("sendPhoto", 5361491365, image, "🧪 Test Story")
        else:
            print("❌ Test failed: Invalid data with zero values")
        print("🏁 TEST MODE FINISHED\n")
    elif "--once" in sys.argv:
        print("\n🏃 STARTING RUN ONCE MODE")
        job()
    else:
        # Run the scheduler and polling together inside an async main
        async def main():
            scheduler = AsyncIOScheduler(timezone="Asia/Tehran")
            scheduler.add_job(job, CronTrigger(hour=0, minute=0, timezone="Asia/Tehran"))
            scheduler.add_job(job, CronTrigger(hour=12, minute=0, timezone="Asia/Tehran"))
            scheduler.add_job(job, CronTrigger(hour=20, minute=0, timezone="Asia/Tehran"))
            scheduler.add_job(
                lambda: print(f"⏳ Heartbeat at {datetime.now(TEHRAN_TZ).strftime('%Y-%m-%d %H:%M:%S')} Tehran time"),
                CronTrigger(minute=0, timezone="Asia/Tehran")
            )
            scheduler.start()
            try:
                await poll_updates()
            except (KeyboardInterrupt, SystemExit):
                print("⏹️ Shutting down...")
                scheduler.shutdown()

        asyncio.run(main())
import os
import requests
import json
import time
import sys
import random
from datetime import datetime
import pytz
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
SEEN_ORDERS_FILE = os.path.join(DATA_DIR, "seen_orders.json")
API_HEADERS = {
    "Content-Type": "application/json",
    "api-key": "ea1d9d33-b000-492f-8fcd-faa6378c76e8",
    "api-secret": "qAGjiJJAMYskSPXmy5C1"
}

URL = "https://api.parachi.com/api/order-book"

# Main bot token
BOT_TOKEN = "8456056506:AAFrKONGT5WeXVye6u6nvsJ_rAl3BFnx3Ic"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Main group chat ID (Iran Group / Parachi_Group)
MAIN_CHAT_ID = "-1003366343939"

# Mapping currency symbols to their respective country group IDs
CURRENCY_GROUPS = {
    "CAD": [-1003359360164],  # Canada Group
    "TRY": [-1003815641753],  # Turkey Group (Lira)
    "RUB": [-1004496736485],  # Russia Group (Ruble)
    "DKK": [-1003850122326],  # Denmark Group
    "SEK": [-1003797637924],  # Sweden Group
    "EUR": [
        -1004445644725,  # Italy Group
        -1004352787198,  # Germany Group
        -1004243655967,  # Spain Group
        -1004492583899,  # France Group
        -1003342367363   # Belgium Group
    ]
}

# Localized Display Names and Hashtags for formatting Persian messages
FIAT_METADATA = {
    "CAD": {"display": "دلار کانادا", "hashtag": "دلار_کانادا"},
    "TRY": {"display": "لیر ترکیه", "hashtag": "لیر_ترکیه"},
    "RUB": {"display": "روبل روسیه", "hashtag": "روبل_روسیه"},
    "DKK": {"display": "کرون دانمارک", "hashtag": "کرون_دانمارک"},
    "SEK": {"display": "کرون سوئد", "hashtag": "کرون_سوئد"},
    "EUR": {"display": "یورو", "hashtag": "یورو"},
    "USD": {"display": "دلار آمریکا", "hashtag": "دلار_آمریکا"},
    "GBP": {"display": "پوند بریتانیا", "hashtag": "پوند_بریتانیا"},
    "IRT": {"display": "تومان ایران", "hashtag": "تومان_ایران"}
}

seen_order_ids = set()
running = True

persian_numbers = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
}

def escape_html_text(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def to_persian_number(number):
    return ''.join(persian_numbers.get(ch, ch) for ch in str(number))

def format_number_clean(number):
    if isinstance(number, str):
        number = float(number)
    
    if number.is_integer():
        int_number = int(number)
        formatted = f"{int_number:,}"
        return to_persian_number(formatted)
    else:
        formatted = f"{number:,.2f}".rstrip('0').rstrip('.')
        return to_persian_number(formatted)

def convert_to_jalali(date_string):
    """Convert ISO date string to Jalali (Persian) calendar date"""
    try:
        import jdatetime
        
        if 'Z' in date_string:
            date_string = date_string.replace('Z', '+00:00')
        
        dt = datetime.fromisoformat(date_string)
        jalali_date = jdatetime.datetime.fromgregorian(datetime=dt)
        
        return f"{jalali_date.year}/{jalali_date.month:02d}/{jalali_date.day:02d}"
    except Exception as e:
        print(f"⚠️ Error converting date {date_string}: {str(e)}")
        return date_string

def get_currency_info(order):
    """Extract currency information and target chat IDs from order"""
    currency_symbol = order['currency']['symbol'].upper()
    currency_name = order['currency']['name']
    
    # Retrieve metadata with fallbacks if not defined in local mapping
    meta = FIAT_METADATA.get(currency_symbol, {
        "display": currency_name,
        "hashtag": currency_symbol
    })
    
    # chat_ids = [MAIN_CHAT_ID]
    chat_ids = [] #removed feedback channel
    
    # Append currency-specific country group chats
    extra_chats = CURRENCY_GROUPS.get(currency_symbol, [])
    for chat_id in extra_chats:
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)
            
    return {
        'type': currency_symbol.lower(),
        'hashtag': meta['hashtag'],
        'display': meta['display'],
        'chat_ids': chat_ids
    }

def format_order_text(order):
    try:
        order_type_text = "فروش" if order['type'] == 'sell' else "خرید"
        order_type_hashtag = "#فروش" if order['type'] == 'sell' else "#خرید"
        
        currency_info = get_currency_info(order)
        currency_hashtag = currency_info['hashtag']
        
        order_id = order['id']
        trade_rate = to_persian_number(order['user']['trade_rate'])
        volume = float(order['volume'])
        volume_persian = format_number_clean(volume)
        price = f"{int(float(order['price'])):,}"
        price_persian = ''.join(persian_numbers.get(ch, ch) for ch in price)
        payment_method = escape_html_text(order['payment_method']['title_fa'])
        
        created_at = order.get('created_at')
        if created_at:
            jalali_date = convert_to_jalali(created_at)
            date_display = f"‏📆 {jalali_date}"
        else:
            date_display = ""
        
        text_lines = [
            f"🔖 حواله {order_id}# | {order_type_hashtag}_{currency_hashtag}",
            "",
            f"⭐️ امتیاز فروشنده: {trade_rate} / ۵",
            f"📦 تعداد: {volume_persian} #{currency_hashtag}",
            f"💰 قیمت پیشنهادی: {price_persian} تومان",
            f"💳 روش پرداخت: {payment_method}",
        ]
        
        if date_display:
            text_lines.append(f"{date_display}")
        
        notes = order.get('notes')
        if notes and notes is not None and str(notes).strip():
            notes_text = escape_html_text(str(notes))
            text_lines.append("")
            text_lines.append("✍️ <b>توضیحات:</b>")
            text_lines.append(f"<blockquote>{notes_text}</blockquote>")
        
        text_lines.extend([
            "\n",
            "",
            "📞 <b>021-91031557</b>",
            "💬 <a href='http://t.me/Parachi_Exchange'>Telegram</a> | <a href='https://ble.ir/parachi'>Bale</a>",
            "🖥 <a href='https://parachi.com'>Parachi.com</a>"
        ])
        
        return "\n".join(text_lines)
    except Exception as e:
        print(f"❌ Error formatting text for order {order.get('id', 'unknown')}: {str(e)}")
        return None

def send_telegram_message(order, chat_id, message_thread_id=None):
    """Send a message to a specific chat ID"""
    try:
        text = format_order_text(order)
        if text is None:
            print(f"  ❌ Skipping order {order['id']} due to text formatting error")
            return False
        
        order_url = order.get('url', f"https://parachi.com/order/{order['id']}")
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "📤 ارسال پیشنهاد",
                        "url": order_url
                    }
                ]
            ]
        }
        
        link_preview_options = {
            "is_disabled": True
        }
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": link_preview_options,
            "reply_markup": json.dumps(inline_keyboard)
        }
        
        if message_thread_id:
            payload["message_thread_id"] = message_thread_id
        
        response = requests.post(TELEGRAM_API_URL, json=payload, timeout=30)
        print(f"  📡 Telegram Response Status for chat {chat_id}: {response.status_code}")
        
        response_data = response.json()
        if not response_data.get('ok'):
            print(f"  📡 Telegram Response Body: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        response.raise_for_status()
        
        if response_data.get('ok'):
            print(f"  ✅ Order {order['id']} sent successfully to chat {chat_id}")
            return True
        else:
            print(f"  ❌ Telegram returned error for chat {chat_id}: {response_data.get('description', 'Unknown error')}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  ⏰ Timeout error sending order {order['id']} to chat {chat_id}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request error sending order {order['id']} to chat {chat_id}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"  📡 Error Response: {e.response.text}")
            except:
                print(f"  📡 Could not read error response")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error sending order {order['id']} to chat {chat_id}: {str(e)}")
        return False

def send_order_to_all_chats(order):
    """Send order to all relevant chat groups"""
    currency_info = get_currency_info(order)
    chat_ids = currency_info['chat_ids']
    
    print(f"  📤 Sending order {order['id']} to {len(chat_ids)} chat group(s)")
    
    success_count = 0
    for chat_id in chat_ids:
        # Check if the chat is the main chat group to optionally set thread ID
        message_thread_id = 1027 if str(chat_id) == str(MAIN_CHAT_ID) else None
        
        print(f"    ➡️ Sending to chat: {chat_id}")
        if send_telegram_message(order, chat_id, message_thread_id):
            success_count += 1
        
        if len(chat_ids) > 1 and chat_id != chat_ids[-1]:
            time.sleep(1)
    
    return success_count == len(chat_ids)

def get_last_seen_id():
    """Get the highest order ID from seen_order_ids"""
    if seen_order_ids:
        return max(seen_order_ids)
    return None

def fetch_orders_with_offset(offset=None):
    """Fetch orders with optional offset parameter"""
    try:
        payload = {
            "currency_ids": [],
            "offset": offset
        }
        
        print(f"📡 Fetching orders from API with offset: {offset if offset else 'None'}...")
        response = requests.post(URL, headers=API_HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('success') and 'data' in data and 'items' in data['data']:
            items = data['data']['items']
            if items:
                order_ids = [order['id'] for order in items[:10]]
                print(f"📡 Retrieved {len(items)} orders from API - First 10 IDs: {order_ids}")
            else:
                print(f"📡 Retrieved 0 orders from API")
            return items
        else:
            print(f"⚠️ Unexpected API response format: {data.get('message', 'No message')}")
            return []
            
    except requests.exceptions.Timeout:
        print(f"⚠️ API request timeout")
        return []
    except requests.exceptions.RequestException as e:
        print(f"⚠️ API request error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"📡 API Error Response: {e.response.text[:500]}")
            except:
                print(f"📡 Could not read API error response")
        return []
    except Exception as e:
        print(f"⚠️ Unexpected error fetching orders: {str(e)}")
        return []

def process_new_orders():
    global seen_order_ids
    
    last_id = get_last_seen_id()
    orders = fetch_orders_with_offset(last_id)
    
    if not orders:
        print("📭 No orders retrieved from API")
        return
    
    new_orders = []
    for order in orders:
        if order['id'] not in seen_order_ids:
            new_orders.append(order)
            seen_order_ids.add(order['id'])
    
    new_orders_sorted = sorted(new_orders, key=lambda x: x['id'])
    
    if new_orders_sorted:
        print(f"\n🆕 Found {len(new_orders_sorted)} new order(s)")
        
        for i, order in enumerate(new_orders_sorted, 1):
            print(f"\n--- Processing order {i}/{len(new_orders_sorted)} ---")
            print(f"  🆔 Order ID: {order['id']}")
            print(f"  📝 Type: {order['type']} - {order['currency']['symbol']}")
            print(f"  📅 Created at: {order.get('created_at', 'N/A')}")
            
            currency_info = get_currency_info(order)
            print(f"  💱 Currency: {currency_info['display']} (sending to {len(currency_info['chat_ids'])} groups)")
            
            if order.get('notes'):
                print(f"  📝 Notes: {order['notes'][:100]}...")
            
            success = send_order_to_all_chats(order)
            
            if success:
                print(f"  ✅ Order {order['id']} completed successfully")
            else:
                print(f"  ❌ Order {order['id']} had issues - some sends may have failed")
            
            if i < len(new_orders_sorted):
                delay_seconds = random.randint(120, 420)
                delay_minutes = delay_seconds / 60
                print(f"  ⏰ Waiting {delay_minutes:.1f} minutes ({delay_seconds} seconds) before next order...")
                time.sleep(delay_seconds)
        
        save_seen_orders()
    else:
        seen_ids_list = sorted(list(seen_order_ids))[-10:]
        print(f"✅ No new orders found - Last 10 seen IDs: {seen_ids_list}")
        if last_id:
            print(f"📌 Last offset used: {last_id}")

def poll_orders():
    global running
    
    print("=" * 60)
    print("🚀 ORDER POLLING SERVICE STARTED")
    print("=" * 60)
    print(f"📡 Polling interval: 10 seconds")
    print(f"🔄 Fetch method: Offset-based (using last seen order ID)")
    print(f"⏱️  Delay between multiple orders: Random 2 to 7 minutes")
    print(f"🤖 Telegram bot: Active")
    print(f"💬 Main Chat ID: {MAIN_CHAT_ID}")
    print(f"🛑 Press Ctrl+C to stop the service")
    print("=" * 60)
    
    loop_count = 0
    
    while running:
        try:
            loop_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'='*50}")
            print(f"🔄 Polling cycle #{loop_count} at {current_time}")
            print(f"{'='*50}")
            
            process_new_orders()
            
            if running:
                print(f"\n⏳ Waiting 10 seconds before next poll...")
                for remaining in range(10, 0, -1):
                    if not running:
                        break
                    print(f"  ⏱️  Next poll in {remaining} seconds...", end='\r')
                    time.sleep(1)
                print(" " * 50, end='\r')
                
        except KeyboardInterrupt:
            print(f"\n⚠️ Keyboard interrupt detected in polling loop")
            break
        except Exception as e:
            print(f"❌ Critical error in polling loop: {str(e)}")
            print(f"⏳ Waiting 30 seconds before retry...")
            time.sleep(30)

def load_seen_orders():
    global seen_order_ids
    try:
        with open(SEEN_ORDERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            seen_order_ids = set(data.get('order_ids', []))
            if seen_order_ids:
                print(f"📁 Loaded {len(seen_order_ids)} previously seen orders from file")
                print(f"📌 Last order ID: {max(seen_order_ids)}")
                print(f"📌 First order ID: {min(seen_order_ids)}")
            else:
                print("📁 No orders found in file - starting fresh")
    except FileNotFoundError:
        print("📁 No previous orders file found - starting fresh")
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing seen_orders.json: {str(e)} - starting fresh")
    except Exception as e:
        print(f"⚠️ Error loading seen orders: {str(e)} - starting fresh")

def save_seen_orders():
    try:
        with open(SEEN_ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'order_ids': sorted(list(seen_order_ids))}, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved {len(seen_order_ids)} seen orders to file")
        if seen_order_ids:
            print(f"📌 Latest saved ID: {max(seen_order_ids)}")
    except Exception as e:
        print(f"⚠️ Error saving seen orders: {str(e)}")

def signal_handler(signum, frame):
    global running
    print("\n" + "=" * 60)
    print(f"⚠️ Received signal {signum} - preparing to shut down...")
    print("=" * 60)
    running = False

def graceful_shutdown():
    print("\n" + "=" * 60)
    print("🛑 GRACEFUL SHUTDOWN INITIATED")
    print("=" * 60)
    
    print("💾 Saving seen orders...")
    save_seen_orders()
    
    print("📁 Closing files...")
    print("🤖 Bot disconnected")
    print("=" * 60)
    print("👋 Goodbye!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        import jdatetime
    except ImportError:
        print("📦 Installing jdatetime for Persian calendar support...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'jdatetime'])
            import jdatetime
            print("✅ jdatetime installed successfully")
        except Exception as e:
            print(f"❌ Failed to install jdatetime: {str(e)}")
            print("⚠️ Continuing without Persian date conversion...")
    
    try:
        import pytz
    except ImportError:
        print("📦 Installing pytz for timezone support...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytz'])
            import pytz
            print("✅ pytz installed successfully")
        except Exception as e:
            print(f"❌ Failed to install pytz: {str(e)}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🔧 ORDER MONITOR BOT INITIALIZING")
    print("=" * 60)
    
    load_seen_orders()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("✅ Signal handlers registered")
    print("🎯 Bot is ready to start\n")
    
    try:
        poll_orders()
    except KeyboardInterrupt:
        print("\n⚠️ Keyboard interrupt received")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
    finally:
        graceful_shutdown()
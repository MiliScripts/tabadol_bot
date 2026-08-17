import asyncio
import json
import logging
import random
import re
import sqlite3
import sys
from typing import Dict

import requests
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatType, ContentType, ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from colorama import Fore, Style, init

init(autoreset=True)

# ==========================================
# تنظیمات ربات و سرور
# ==========================================
BOT_TOKEN = "8456056506:AAFrKONGT5WeXVye6u6nvsJ_rAl3BFnx3Ic"
BACKEND_URL = "https://api.parachi.com/api/telegram/init"
BOT_USERNAME = "Parachi_Bot"
ADMIN_IDS = [5361491365, 691004442]

# ==========================================
# تنظیمات بررسی عضویت‌ها و اعتبارسنجی (Flags)
# ==========================================
ONLY_ACCEPT_IRAN_MOBILE = True         # فقط شماره‌های ایران قبول شوند
MUST_JOIN_MANDATORY = True             # اجبار به عضویت در کانال‌های پوشه در شروع استارت
MUST_JOIN_COUNTRY_CHANNEL = False       # اجبار به عضویت در گروه مربوط به کشور انتخابی

# لینک پوشه و آیدی کانال‌های اجباری استارت
MANDATORY_CHANNELS = [-1002656752612, -1003366343939]
MANDATORY_JOIN_LINK = "https://t.me/addlist/vG6wjtl9EdU5ZTM0"

COUNTRIES = {
    "IR": {"id": 1, "name": "ایران", "code": "IR", "mobile_code": "+98", "flag": "🇮🇷", "channel": "Parachi_Group", "chat_id": -1003366343939},
    "CA": {"id": 3, "name": "کانادا", "code": "CA", "mobile_code": "+1", "flag": "🇨🇦", "channel": "Parachi_ca", "chat_id": -1003359360164},
    "IT": {"id": 61, "name": "ایتالیا", "code": "IT", "mobile_code": "+39", "flag": "🇮🇹", "channel": "Parachi_it", "chat_id": -1004445644725},
    "DE": {"id": 59, "name": "آلمان", "code": "DE", "mobile_code": "+49", "flag": "🇩🇪", "channel": "Parachi_de", "chat_id": -1004352787198},
    "ES": {"id": 62, "name": "اسپانیا", "code": "ES", "mobile_code": "+34", "flag": "🇪🇸", "channel": "Parachi_es", "chat_id": -1004243655967},
    "FR": {"id": 60, "name": "فرانسه", "code": "FR", "mobile_code": "+33", "flag": "🇫🇷", "channel": "Parachi_fr", "chat_id": -1004492583899},
    "DK": {"id": 44, "name": "دانمارک", "code": "DK", "mobile_code": "+45", "flag": "🇩🇰", "channel": "Parachi_dk", "chat_id": -1003850122326},
    "SE": {"id": 43, "name": "سوئد", "code": "SE", "mobile_code": "+46", "flag": "🇸🇪", "channel": "Parachi_se", "chat_id": -1003797637924},
    "BE": {"id": 67, "name": "بلژیک", "code": "BE", "mobile_code": "+32", "flag": "🇧🇪", "channel": "Parachi_BE", "chat_id": -1003342367363},
    "RU": {"id": 15, "name": "روسیه", "code": "RU", "mobile_code": "+7", "flag": "🇷🇺", "channel": "Parachi_ru", "chat_id": -1004496736485},
    "TR": {"id": 6, "name": "ترکیه", "code": "TR", "mobile_code": "+90", "flag": "🇹🇷", "channel": "Parachi_tr", "chat_id": -1003815641753}
}

MONITOR_GROUP_IDS = [
    -1003366343939, -1003359360164, -1004445644725, -1004352787198, 
    -1004243655967, -1004492583899, -1003850122326, -1003797637924, 
    -1003342367363, -1004496736485, -1003815641753
]

API_BASE_URL = "https://api.parachi.com"
API_HEADERS = {
    "Content-Type": "application/json",
    "api-key": "ea1d9d33-b000-492f-8fcd-faa6378c76e8",
    "api-secret": "qAGjiJJAMYskSPXmy5C1"
}

UNREGISTERED_IMAGE = "https://files.imeow.ir/dl/default/not_registered_parachi_bot.png"
KYC_INCOMPLETE_IMAGE = "https://files.imeow.ir/dl/default/kyc_not.png"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)
dp.include_router(router)

BANNERS = {
    "join": "https://files.imeow.ir/dl/default/pending_parachi_auth.jpg",
    "welcome": "https://files.imeow.ir/dl/default/welcome_parachi.jpg",
    "phone": "https://files.imeow.ir/dl/default/pending_parachi_auth.jpg",
    "processing": "https://files.imeow.ir/dl/default/pending_parachi_auth.jpg",
    "success": "https://files.imeow.ir/dl/default/parachi_auth_sucess.jpg",
    "expired": "https://files.imeow.ir/dl/default/parachi_auth_failed.jpg",
    "error": "https://files.imeow.ir/dl/default/parachi_auth_failed.jpg",
    "newlink": "https://files.imeow.ir/dl/default/pending_parachi_auth.jpg"
}

messages_to_expire: Dict[int, Dict[str, int]] = {}

DB_FILE = "bot_users.db"

class UserState(StatesGroup):
    needs_mandatory_join = State()
    waiting_for_country = State()
    waiting_for_contact = State()
    needs_join = State()

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                username TEXT,
                mobile TEXT,
                country_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logging.info("Database initiated successfully.")
    except Exception as e:
        logging.error(f"Error initializing SQLite database: {e}")

def save_user(chat_id: int, username: str, mobile: str, country_code: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (chat_id, username, mobile, country_code)
            VALUES (?, ?, ?, ?)
        """, (chat_id, username, mobile, country_code))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving user data: {e}")

def should_ignore_user(user_first_name: str = "", mobile: str = "", user_id: int = 0) -> bool:
    if user_first_name.lower() == "telegram":
        return True
    if mobile and mobile.strip() == "42777":
        return True
    if user_id == 7352988550:
        return True
    return False

def check_telegram_auth(user_id: int) -> dict:
    try:
        url = f"{API_BASE_URL}/tgadmin/is_authenticated"
        payload = {"uid": str(user_id)}
        response = requests.post(url, headers=API_HEADERS, data=json.dumps(payload), timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                return {
                    "registered": data.get("registered", False),
                    "kyc_level": data.get("kyc_level", 0)
                }
        return {"registered": False, "kyc_level": 0}
    except Exception as e:
        logging.error(f"Error in check_telegram_auth: {e}")
        return {"registered": False, "kyc_level": 0}

async def safe_execute(coro, user_chat=None, context=""):
    try:
        return await coro
    except Exception as e:
        logging.error(f"Execution failed in {context}: {e}")
        if user_chat:
            try:
                deep_link = f"https://t.me/{BOT_USERNAME}?start=login"
                error_text = "❌ خطایی رخ داد. لطفا مجددا تلاش کنید."
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 شروع مجدد", url=deep_link)]
                ])
                await bot.send_photo(user_chat, BANNERS["error"], caption=error_text, reply_markup=keyboard)
            except:
                pass
        return None

def is_valid_number(mobile: str, expected_prefix: str, only_iran: bool = False) -> bool:
    try:
        mobile = mobile.replace(" ", "").replace("-", "").replace("+", "")
        
        is_iran = mobile.startswith('98') or mobile.startswith('0')
        if only_iran:
            return is_iran
            
        clean_expected = expected_prefix.replace("+", "") if expected_prefix else ""
        return is_iran or (clean_expected and mobile.startswith(clean_expected))
    except Exception as e:
        logging.error(f"Error checking valid number: {e}")
        return False

def parse_phone_number(phone: str):
    phone = phone.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        if phone.startswith("00"):
            phone = "+" + phone[2:]
        elif phone.startswith("98"):
            phone = "+98" + phone[2:]
        elif phone.startswith("0"):
            phone = "+98" + phone[1:]
        else:
            phone = "+" + phone
    
    prefixes = sorted([c["mobile_code"] for c in COUNTRIES.values() if c["mobile_code"]], key=len, reverse=True)
    if "+98" not in prefixes:
        prefixes.append("+98")
        
    for prefix in prefixes:
        if phone.startswith(prefix):
            national = phone[len(prefix):]
            if national.startswith("0"):
                national = national[1:]
            return prefix, national
    return "+98", phone

def extract_url_from_message(message: str) -> str:
    try:
        match = re.search(r'(https?://[^\s]+)', message)
        return match.group(0) if match else "#"
    except Exception as e:
        logging.error(f"Error extracting URL: {e}")
        return "#"

async def delete_after_delay(chat_id: int, message_id: int, delay: int = 60):
    try:
        await asyncio.sleep(delay)
        try:
            await bot.delete_message(chat_id, message_id)
        except:
            pass
    except Exception as e:
        logging.error(f"Error in delete_after_delay: {e}")

async def expire_activation_link(chat_id: int, message_id: int, delay: int = 1200):
    try:
        await asyncio.sleep(delay)
        try:
            expired_text = "❌ لینک ورود منقضی شده است\n\n🔻برای دریافت لینک جدید، روی دکمه زیر کلیک کنید:"
            deep_link = f"https://t.me/{BOT_USERNAME}?start=login"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 دریافت لینک جدید", url=deep_link)]
            ])
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media={"type": "photo", "media": BANNERS["expired"], "caption": expired_text, "parse_mode": "HTML"},
                reply_markup=keyboard
            )
            messages_to_expire.pop(chat_id, None)
        except Exception as e:
            logging.error(f"Error editing message for link expiry: {e}")
    except Exception as e:
        logging.error(f"Error in expire_activation_link: {e}")

async def check_channel_membership(user_id: int, chat_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Membership verification failed for chat {chat_id}: {e}")
        return False

async def send_group_warning_auto_delete(chat_id: int, photo: str, caption: str, keyboard: InlineKeyboardMarkup, delay: int = 10):
    try:
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        asyncio.create_task(delete_after_delay(chat_id, msg.message_id, delay))
    except Exception as e:
        logging.error(f"Error in send_group_warning_auto_delete: {e}")

@dp.message(
    F.chat.id.in_(MONITOR_GROUP_IDS),
    F.content_type.in_({
        ContentType.NEW_CHAT_MEMBERS,
        ContentType.LEFT_CHAT_MEMBER,
        ContentType.NEW_CHAT_TITLE,
        ContentType.NEW_CHAT_PHOTO,
        ContentType.DELETE_CHAT_PHOTO,
        ContentType.GROUP_CHAT_CREATED,
        ContentType.PINNED_MESSAGE,
    })
)
async def delete_service_messages(message: Message):
    try:
        await message.delete()
    except Exception as e:
        logging.error(f"Error deleting service message: {e}")

@dp.message(
    F.chat.id.in_(MONITOR_GROUP_IDS),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})
)
async def monitor_group_messages(message: Message):
    if message.from_user is None or message.from_user.id == bot.id:
        return

    first_name = message.from_user.first_name or ""
    if should_ignore_user(user_first_name=first_name):
        return

    allowed_content_types = {
        ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO,
        ContentType.DOCUMENT, ContentType.AUDIO, ContentType.VOICE,
        ContentType.ANIMATION, ContentType.STICKER, ContentType.VIDEO_NOTE
    }

    if message.content_type not in allowed_content_types:
        return

    try:
        user = message.from_user
        user_id = user.id
        chat_id = message.chat.id
        user_mention = f'<a href="tg://user?id={user_id}">{user.full_name}</a>'
        
        auth_status = check_telegram_auth(user_id)

        if not auth_status.get("registered") and user_id != 7352988550:
            await message.delete()

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🤖 ثبت‌نام در ربات", url=f"https://t.me/{BOT_USERNAME}")]
            ])
            warning_text = (
                f"⚠️ کاربر {user_mention} شما در پاراچی ثبت‌نام نکرده‌اید!\n\n"
                "لطفا ابتدا در ربات ثبت‌نام کنید و سپس مجدداً در این گروه پیام ارسال کنید.\n\n"
                "پیام شما به دلیل عدم ثبت‌نام حذف شد."
            )

            await send_group_warning_auto_delete(
                chat_id, UNREGISTERED_IMAGE, warning_text, keyboard, delay=30
            )

            try:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=UNREGISTERED_IMAGE,
                    caption=warning_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
            return

        if auth_status.get("kyc_level") == 0 and user_id != 7352988550:
            await message.delete()

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 تکمیل پروفایل", url="https://app.parachi.com")]
            ])
            warning_text = (
                f"⚠️ کاربر {user_mention} سطح احراز هویت شما کامل نیست!\n\n"
                "لطفا وارد سایت شوید و پروفایل خود را تکمیل کنید (احراز هویت سطح 1).\n\n"
                "پس از تکمیل احراز هویت، می‌توانید در این گروه پیام ارسال کنید.\n\n"
                "پیام شما به دلیل عدم تکمیل احراز هویت حذف شد."
            )

            await send_group_warning_auto_delete(
                chat_id, KYC_INCOMPLETE_IMAGE, warning_text, keyboard, delay=10
            )

            try:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=KYC_INCOMPLETE_IMAGE,
                    caption=warning_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
            return

        user_name = user.full_name or user.username or f"User_{user.id}"
        if message.text:
            message_content = message.text
        elif message.caption:
            message_content = f"[Media with caption]: {message.caption}"
        else:
            message_content = f"[{message.content_type.title()} message]"

        logging.info(f"Group message accepted in {chat_id} from {user_name} ({user_id}): {message_content}")

    except Exception as e:
        logging.error(f"Error in monitor_group_messages: {e}")

async def send_country_selection_menu(chat_id: int, state: FSMContext):
    keyboard_buttons = []
    country_list = list(COUNTRIES.values())
    for i in range(0, len(country_list), 2):
        row = []
        c1 = country_list[i]
        row.append(KeyboardButton(text=f"{c1['flag']} {c1['name']}"))
        if i + 1 < len(country_list):
            c2 = country_list[i+1]
            row.append(KeyboardButton(text=f"{c2['flag']} {c2['name']}"))
        keyboard_buttons.append(row)
        
    markup = ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True, one_time_keyboard=True)
    
    await bot.send_photo(
        chat_id, 
        "https://files.imeow.ir/dl/default/no_country_bro.png", 
        caption="لطفا ابتدا کشور محل اقامت خود را از دکمه‌های زیر انتخاب کنید:", 
        reply_markup=markup
    )
    await state.set_state(UserState.waiting_for_country)

@router.message(CommandStart(deep_link=True))
@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, command: CommandStart = None):
    if message.from_user.id == bot.id:
        return
    
    first_name = message.from_user.first_name or ""
    if should_ignore_user(user_first_name=first_name):
        return
    
    await state.clear()
    
    if command and command.args:
        args = command.args
        if args.startswith("invite_"):
            referrer = args[7:]
            await state.update_data(referrer=referrer)
            
    # بررسی عضویت اجباری در کانال‌ها (در صورت فعال بودن فلگ)
    if MUST_JOIN_MANDATORY:
        user_id = message.from_user.id
        is_member_all = True
        for ch_id in MANDATORY_CHANNELS:
            if not await check_channel_membership(user_id, ch_id):
                is_member_all = False
                break

        if not is_member_all:
            join_text = (
                "سلام، به پاراچی خوش آمدید! 🌸\n\n"
                "جهت استفاده از خدمات ربات، لطفا ابتدا از طریق لینک زیر در کانال‌های رسمی ما عضو شوید و سپس روی دکمه «✅ بررسی عضویت» کلیک کنید:"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="عضویت در کانال‌ها", url=MANDATORY_JOIN_LINK)],
                [InlineKeyboardButton(text="✅ بررسی عضویت", callback_data="check_mandatory_membership")]
            ])
            await bot.send_photo(message.chat.id, BANNERS["join"], caption=join_text, reply_markup=keyboard)
            await state.set_state(UserState.needs_mandatory_join)
            return

    await send_country_selection_menu(message.chat.id, state)

@router.callback_query(lambda c: c.data == "check_mandatory_membership")
async def check_mandatory_membership_callback(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.from_user.id == bot.id:
        return
        
    await callback_query.answer("در حال بررسی عضویت...")
    user_id = callback_query.from_user.id
    
    if MUST_JOIN_MANDATORY:
        is_member_all = True
        for ch_id in MANDATORY_CHANNELS:
            if not await check_channel_membership(user_id, ch_id):
                is_member_all = False
                break

        if is_member_all:
            try:
                await callback_query.message.delete()
            except:
                pass
            await send_country_selection_menu(callback_query.message.chat.id, state)
        else:
            await callback_query.answer("❌ شما هنوز در تمامی کانال‌ها عضو نشده‌اید! لطفا وارد لینک شده و عضو شوید.", show_alert=True)
    else:
        try:
            await callback_query.message.delete()
        except:
            pass
        await send_country_selection_menu(callback_query.message.chat.id, state)

@router.message(UserState.waiting_for_country)
async def handle_country_selection(message: Message, state: FSMContext):
    text = message.text or ""
    selected_country = None
    for code, data in COUNTRIES.items():
        if data["name"] in text:
            selected_country = data
            break
            
    if not selected_country:
        await message.reply("⚠️ لطفا یکی از کشورهای لیست زیر را انتخاب کنید.")
        return

    await state.update_data(selected_country_code=selected_country["code"])
    await state.set_state(UserState.waiting_for_contact)

    welcome_text = f"""با سلام
کشور انتخاب شده: {selected_country['flag']} {selected_country['name']}

در صورتی که خارج از ایران سکونت دارید و امکان دریافت کد پیامکی برای ورود به وب اپلیکیشن پاراچی برایتان مقدور نیست، از طریق این ربات می‌توانید بدون نیاز به دریافت پیامک وارد حساب کاربری خود شوید.

لطفا برای ادامه، روی دکمه «📱 ارسال شماره موبایل» کلیک کنید تا شماره سیم‌کارت شما ارسال شود."""

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 ارسال شماره موبایل", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await bot.send_photo(message.chat.id, BANNERS["welcome"], caption=welcome_text, reply_markup=keyboard)

@router.message(F.contact)
async def handle_contact(message: Message, state: FSMContext):
    if message.from_user.id == bot.id:
        return

    first_name = message.from_user.first_name or ""
    mobile = message.contact.phone_number if message.contact else ""

    if should_ignore_user(user_first_name=first_name, mobile=mobile):
        return

    current_state = await state.get_state()
    if current_state != UserState.waiting_for_contact.state:
        return

    state_data = await state.get_data()
    country_code = state_data.get("selected_country_code")
    if not country_code or country_code not in COUNTRIES:
        await message.reply("⚠️ خطا: لطفا ابتدا کشور خود را انتخاب کنید.")
        await state.set_state(UserState.waiting_for_country)
        return

    country_data = COUNTRIES[country_code]
    expected_prefix = country_data["mobile_code"]

    if not is_valid_number(mobile, expected_prefix, ONLY_ACCEPT_IRAN_MOBILE):
        deep_link = f"https://t.me/{BOT_USERNAME}?start=login"
        error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 شروع مجدد", url=deep_link)]
        ])
        
        error_caption = "❌ شماره وارد شده نامعتبر است. لطفا فقط از شماره موبایل ایرانی (98+) استفاده کنید."

        await bot.send_photo(
            message.chat.id, BANNERS["error"],
            caption=error_caption,
            reply_markup=error_keyboard
        )
        return

    prefix, national_number = parse_phone_number(mobile)

    await state.update_data(
        mobile_national=national_number,
        mobile_prefix=prefix
    )

    user_id = message.from_user.id
    chat_id_to_check = country_data["chat_id"]
    channel_name = country_data["channel"]

    # بررسی عضویت در گروه کشور
    if MUST_JOIN_COUNTRY_CHANNEL:
        is_member = await check_channel_membership(user_id, chat_id_to_check)
        if is_member:
            await register_user_on_backend(message.chat.id, message.from_user, state, national_number, prefix, country_data)
        else:
            join_text = f"لطفا ابتدا در گروه کشور خود عضو شوید، سپس بر روی دکمه زیر کلیک کنید:\n\n🌐 گروه کشور شما: @{channel_name}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="عضویت در گروه", url=f"https://t.me/{channel_name}")],
                [InlineKeyboardButton(text="✅ بررسی مجدد عضویت", callback_data="check_membership")]
            ])
            msg = await bot.send_photo(message.chat.id, BANNERS["join"], caption=join_text, reply_markup=keyboard)
            asyncio.create_task(delete_after_delay(message.chat.id, msg.message_id))
            await state.set_state(UserState.needs_join)
    else:
        # اگر اجبار گروه غیرفعال بود مستقیماً ثبت‌نام انجام شود
        await register_user_on_backend(message.chat.id, message.from_user, state, national_number, prefix, country_data)

@router.callback_query(lambda c: c.data == "check_membership")
async def check_membership_callback(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.from_user.id == bot.id:
        return
    
    first_name = callback_query.from_user.first_name or ""
    if should_ignore_user(user_first_name=first_name):
        return
    
    await callback_query.answer("در حال بررسی عضویت...")
    
    state_data = await state.get_data()
    country_code = state_data.get("selected_country_code")
    mobile = state_data.get("mobile_national")
    prefix = state_data.get("mobile_prefix")

    if not country_code or country_code not in COUNTRIES:
        await callback_query.message.reply("⚠️ اطلاعات نامعتبر است. لطفا ربات را با دستور /start مجدداً راه اندازی کنید.")
        return

    country_data = COUNTRIES[country_code]
    user_id = callback_query.from_user.id
    chat_id_to_check = country_data["chat_id"]

    if MUST_JOIN_COUNTRY_CHANNEL:
        is_member = await check_channel_membership(user_id, chat_id_to_check)
        if is_member:
            try:
                await callback_query.message.delete()
            except:
                pass
            await register_user_on_backend(callback_query.message.chat.id, callback_query.from_user, state, mobile, prefix, country_data)
        else:
            await callback_query.answer("شما هنوز عضو گروه کشور خود نشده‌اید!", show_alert=True)
    else:
        try:
            await callback_query.message.delete()
        except:
            pass
        await register_user_on_backend(callback_query.message.chat.id, callback_query.from_user, state, mobile, prefix, country_data)

async def register_user_on_backend(chat_id: int, user, state: FSMContext, mobile: str, prefix: str, country_data: dict):
    username = user.username or ""
    
    wait_msg = await bot.send_photo(chat_id, BANNERS["processing"], caption="⏳ در حال پردازش...")

    state_data = await state.get_data()
    referrer = state_data.get("referrer")

    payload = {
        "chat_id": str(chat_id),
        "username": username,
        "mobile": mobile,
        "mobile_country_code": prefix,
        "location_id": country_data["id"]
    }
    if referrer:
        payload["referrer"] = referrer

    print(Fore.CYAN + "\n========== SENDING REQUEST TO /init ==========")
    print(Fore.YELLOW + f"URL: {BACKEND_URL}")
    print(Fore.YELLOW + "Payload:")
    print(json.dumps(payload, indent=4, ensure_ascii=False))
    print(Fore.CYAN + "=============================================")

    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=60)

        print(Fore.CYAN + "\n========== RESPONSE FROM /init ==========")
        print(Fore.GREEN + f"Status Code: {response.status_code}")
        try:
            resp_json = response.json()
            print(Fore.GREEN + "Response JSON:")
            print(json.dumps(resp_json, indent=4, ensure_ascii=False))
        except:
            print(Fore.GREEN + "Response text:")
            print(response.text)
        print(Fore.CYAN + "=========================================\n")

        data = response.json()

        if not data.get("success"):
            deep_link = f"https://t.me/{BOT_USERNAME}?start=login"
            error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 تلاش مجدد", url=deep_link)]
            ])
            await wait_msg.edit_caption(caption="⚠️ خطا در احراز هویت")
            await wait_msg.edit_reply_markup(reply_markup=error_keyboard)
            return

        activation_link = data.get("data", {}).get("message", "")
        if activation_link:
            url = extract_url_from_message(activation_link)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚪 ورود به وب اپلیکیشن", url=url)]
            ])
            await wait_msg.edit_media(
                media={
                    "type": "photo",
                    "media": BANNERS["success"],
                    "caption": "✅ورود موفق\n\n🔻لینک اختصاصی شما جهت ورود به وب اپلیکیشن پاراچی",
                    "parse_mode": "HTML"
                },
                reply_markup=keyboard
            )
            
            save_user(chat_id, username, f"{prefix}{mobile}", country_data["code"])
            
            task = asyncio.create_task(expire_activation_link(chat_id, wait_msg.message_id))
            messages_to_expire[chat_id] = {"message_id": wait_msg.message_id, "expiry_task": task}
            await state.clear()
        else:
            deep_link = f"https://t.me/{BOT_USERNAME}?start=login"
            error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 تلاش مجدد", url=deep_link)]
            ])
            await wait_msg.edit_caption(caption="❌ لینک ورود یافت نشد")
            await wait_msg.edit_reply_markup(reply_markup=error_keyboard)

    except requests.exceptions.Timeout:
        deep_link = f"https://t.me/{BOT_USERNAME}?start=login"
        error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 تلاش مجدد", url=deep_link)]
        ])
        await wait_msg.edit_caption(caption="❌ زمان درخواست به سرور به پایان رسید. لطفا دوباره تلاش کنید.")
        await wait_msg.edit_reply_markup(reply_markup=error_keyboard)
    except requests.exceptions.RequestException as e:
        deep_link = f"https://t.me/{BOT_USERNAME}?start=login"
        error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 تلاش مجدد", url=deep_link)]
        ])
        await wait_msg.edit_caption(caption="❌ خطا در ارتباط با سرور")
        await wait_msg.edit_reply_markup(reply_markup=error_keyboard)

@router.message()
async def handle_other_messages(message: Message, state: FSMContext):
    if message.from_user.id == bot.id:
        return
    
    first_name = message.from_user.first_name or ""
    if should_ignore_user(user_first_name=first_name):
        return
    
    try:
        chat_id = message.chat.id
        current_state = await state.get_state()
        deep_link = f"https://t.me/{BOT_USERNAME}?start=login"
        
        if current_state == UserState.needs_mandatory_join.state:
            join_text = (
                "سلام، به پاراچی خوش آمدید! 🌸\n\n"
                "جهت استفاده از خدمات ربات، لطفا ابتدا از طریق لینک زیر در کانال‌های رسمی ما عضو شوید و سپس روی دکمه «✅ بررسی عضویت» کلیک کنید:"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="عضویت در کانال‌ها", url=MANDATORY_JOIN_LINK)],
                [InlineKeyboardButton(text="✅ بررسی عضویت", callback_data="check_mandatory_membership")]
            ])
            await bot.send_photo(
                chat_id, BANNERS["join"],
                caption=join_text,
                reply_markup=keyboard
            )
        elif current_state == UserState.waiting_for_country.state:
            await message.reply("⚠️ لطفا ابتدا کشور خود را از منوی پایین انتخاب کنید.")
        elif current_state == UserState.waiting_for_contact.state:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 ارسال شماره موبایل", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await bot.send_photo(
                chat_id, BANNERS["phone"],
                caption="⚠️ لطفا برای ادامه، شماره موبایل خود را با استفاده از دکمه «📱 ارسال شماره موبایل» ارسال کنید.",
                reply_markup=keyboard
            )
        elif current_state == UserState.needs_join.state:
            state_data = await state.get_data()
            country_code = state_data.get("selected_country_code")
            country_data = COUNTRIES.get(country_code)
            channel_name = country_data["channel"] if country_data else ""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="عضویت در گروه", url=f"https://t.me/{channel_name}")],
                [InlineKeyboardButton(text="✅ بررسی مجدد عضویت", callback_data="check_membership")]
            ])
            await bot.send_photo(
                chat_id, BANNERS["join"],
                caption=f"⚠️ ابتدا باید در گروه مربوط به کشور خود عضو شوید و سپس روی دکمه بررسی مجدد کلیک کنید.\n\n🌐 گروه کشور شما: @{channel_name}",
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 شروع ربات", url=deep_link)]
            ])
            await bot.send_photo(
                chat_id, BANNERS["welcome"],
                caption="⚠️ لطفا دستور /start را ارسال کنید یا روی دکمه زیر کلیک کنید.",
                reply_markup=keyboard
            )
    except Exception as e:
        logging.error(f"Error in handle_other_messages: {e}")

async def main():
    print("🤖 Bot is starting...")
    init_db()
    print("👀 Monitored groups loaded.")
    print("============================================================")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error in main polling loop: {e}")

def run_test_mode():
    test_phones = ["9922998407", "9200952500"]
    country = random.choice(list(COUNTRIES.values()))
    mobile = random.choice(test_phones)
    
    payload = {
        "chat_id": "5361491365",
        "username": "test_user",
        "mobile": mobile,
        "mobile_country_code": "+98",
        "location_id": country["id"]
    }
    
    print(Fore.CYAN + "\n================ TEST MODE ================")
    print(Fore.BLUE + f"Target URL: {BACKEND_URL}")
    print(Fore.YELLOW + f"Payload:\n{json.dumps(payload, indent=4)}")
    print(Fore.CYAN + "-------------------------------------------")
    
    try:
        response = requests.post(BACKEND_URL, json=payload, headers=API_HEADERS, timeout=60)
        
        if response.status_code == 200:
            print(Fore.GREEN + f"Status Code: {response.status_code}")
            print(Fore.GREEN + f"Response Data:\n{json.dumps(response.json(), indent=4, ensure_ascii=False)}")
        else:
            print(Fore.RED + f"Status Code: {response.status_code}")
            print(Fore.RED + f"Response Data:\n{response.text}")
            
    except Exception as e:
        print(Fore.RED + f"Request Failed: {e}")
        
    print(Fore.CYAN + "===========================================\n")
    sys.exit(0)

if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test_mode()
    else:
        try:
            asyncio.run(main())
        except Exception as e:
            logging.error(f"Fatal startup error: {e}")
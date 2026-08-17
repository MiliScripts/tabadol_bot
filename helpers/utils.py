import jdatetime
import locale
import emoji
import re
import urllib.parse
import os
import json
import pandas as pd
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from configs.config import cchannels
from pyrogram import Client 
import requests

def get_current_jalali_date():
    jalali_now = jdatetime.datetime.now()
    day = jalali_now.day
    month = jalali_now.month
    year = jalali_now.year
    return f"{day} {month} {year}"

def format_number(number):
    try:
        number = int(number)
        locale.setlocale(locale.LC_ALL, '')
        return locale.format_string('%d', number, grouping=True)
    except ValueError:
        return number

def clean_string(text):
    cleaned_text = re.sub(r'[^\u0600-\u06FFa-zA-Z\s]', '', text)
    cleaned_text = cleaned_text.replace(' ', '_')
    return cleaned_text

def remove_emoji(text):
    return emoji.replace_emoji(text, replace='')

def generate_telegram_share_url(base_url, text):
    encoded_url = urllib.parse.quote(base_url)
    encoded_text = urllib.parse.quote(text)
    return f"http://t.me/share/url?url={encoded_url}&text={encoded_text}"

def get_jalali_date():
    persian_months = {
        'Farvardin': 'فروردین',
        'Ordibehesht': 'اردیبهشت',
        'Khordad': 'خرداد',
        'Tir': 'تیر',
        'Mordad': 'مرداد',
        'Shahrivar': 'شهریور',
        'Mehr': 'مهر',
        'Aban': 'آبان',
        'Azar': 'آذر',
        'Dey': 'دی',
        'Bahman': 'بهمن',
        'Esfand': 'اسفند'
    }
    jalali_date = jdatetime.datetime.now()
    day = jalali_date.day
    month = jalali_date.strftime('%B')
    persian_month = persian_months.get(month, month)
    persian_numbers = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    persian_day = str(day).translate(persian_numbers)
    return f'{persian_day} {persian_month}'

def create_tmp_dir():
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

def get_users_excel(excel_file):
    from helpers.db import Session, User
    session = Session()
    try:
        users_list = session.query(User).all()
        data = []
        for index, user in enumerate(users_list, start=1):
            data.append({
                "index": index,
                "id": user.id,
                "user_id": user.user_id,
                "phone_number": user.phone_number,
                "telegram_first_name": user.telegram_first_name,
                "telegram_last_name": user.telegram_last_name,
                "username": user.username,
                "country": user.country,
                "name": user.name,
                "joined_date": user.joined_date,
                "successfull_transactions": user.successfull_transactions,
                "failed_transactions": user.failed_transactions,
                "refrals": user.refrals,
                "invited_by": user.invited_by,
                "wallet": user.wallet
            })
        df = pd.DataFrame(data)
        df.to_excel(excel_file, index=False)
        return len(data)
    except Exception as e:
        print(f"Error creating users excel: {e}")
        return 0
    finally:
        session.close()

async def send_excel_file(client, chat_id, file_path, caption):
    await client.send_document(chat_id, file_path, caption=caption)

async def send_users(client, chat_id):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_file = os.path.join(BASE_DIR, "users.xlsx")
    u = get_users_excel(excel_file)
    if os.path.exists(excel_file):
        await send_excel_file(client, chat_id, excel_file, caption=f"تعداد کاربران : ({u}) نفر")
        os.remove(excel_file)
    else:
        await client.send_message(chat_id, f"❌ خطا در ایجاد فایل اکسل کاربران. تعداد: {u}")

async def send_to_custom_channels(client: Client, currency: str, message_text: str, kb):
    if "دانمارک" in currency or "نروژ" in currency:
        channels_to_send = cchannels.kron_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "سوئد" in currency:
        channels_to_send = cchannels.swedn_kron.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "کانادا" in currency:
        channels_to_send = cchannels.usd_canada_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "دلار" in currency:
        channels_to_send = cchannels.usd_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "تتر" in currency:
        channels_to_send = cchannels.thether_Channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "یورو" in currency:
        channels_to_send = cchannels.euro_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "یوان" in currency:
        channels_to_send = cchannels.cny_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "درهم" in currency:
        channels_to_send = cchannels.aed_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "پوند" in currency:
        channels_to_send = cchannels.pond_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "لیر" in currency:
        channels_to_send = cchannels.lir_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)
    elif "روبل" in currency:
        channels_to_send = cchannels.rub_channels.values()
        for channel in channels_to_send:
            try:
                await client.send_message(chat_id=channel, text=message_text, reply_markup=kb)
            except Exception as e:
                print(e)

def get_currency_price(currency_name):
    try:
        if "کرون" in currency_name:
            r = requests.get("https://open-arz.milaadfarzian.workers.dev/?get=arz", timeout=10)
            r.raise_for_status()
            for item in r.json():
                title = item.get("title", "").strip()
                if currency_name in title or title in currency_name:
                    return int(item.get("price", "0").replace(",", ""))
            return None
        response = requests.get("https://navasan.milaadfarzian.workers.dev/", timeout=10)
        response.raise_for_status()
        data = response.json()
        currency_map = {
            "دلار": "usd",
            "یورو": "eur",
            "تتر": "usdt",
            "پوند": "gbp",
            "درهم": "aed",
            "لیر": "try",
            "یوان": "cny",
        }
        key = currency_map.get(currency_name)
        if not key:
            return None
        currency_data = data.get(key)
        if not currency_data:
            return None
        price = currency_data.get("value")
        return int(price) if price is not None else None
    except Exception as e:
        print(e)
        return None

def fetch_euro_min_max():
    try:
        euro_price = get_currency_price("یورو")
        if euro_price:
            min_price = euro_price - 6000
            max_price = euro_price + 6000
            return max_price, min_price
        else:
            return None, None
    except Exception as e:
        print(f"Error getting EUR min/max price: {e}")
        return None, None

def fetch_ustd_min_max():
    try:
        ustd_price = get_currency_price("دلار")
        if ustd_price:
            min_price = ustd_price - 2000
            max_price = ustd_price + 2000
            return max_price, min_price
        else:
            return None, None
    except Exception as e:
        print(f"Error getting USD_USDT min/max price: {e}")
        return None, None

######################## Imports ########################
import jdatetime
import requests
import json
import jdatetime
import pytz
import requests
import json
import locale
import requests
import json
import os
import time
from datetime import datetime, timedelta


cur_dict = {
    'ustd': '💵 تتر',
    'ev': '💳 پرفکت مانی',
    'gbp': '💷 پوند',
    'usd_sell': '💲 دلار',
    'aed_sell': '🇦🇪 درهم',
    'eur': '💶 یورو',
    'try': '💶 لیر',
    'sek': '🇸🇪 کرون سوئد',
    'dkk': '🇩🇰 کرون دانمارک',
    'nok': '🇳🇴 کرون نروژ',
    'cny': '🇨🇳 یوان چین',
    'myr': '🇲🇾 رینگیت مالزی',
    'cad': '🇨🇦 دلار کانادا',
    'chf': '🇨🇭 فرانک سوئیس',
    'aud': '🇦🇺 دلار استرالیا',
    'azn': '🇦🇿 منات آذربایجان',
    'kwd': '🇰🇼 دینار کویت',
    'sgd': '🇸🇬 دلار سنگاپور',
    'rub': '🇷🇺 روبل روسیه',
    'qar': '🇶🇦 ریال قطر',
    'afn': '🇦🇫 افغانی',
    'omr': '🇴🇲 ریال عمان'
}


cur_dict2 = {
    'ustd': 'تتر',
    'ev': 'پرفکت مانی',
    'gbp': 'پوند',
    'usd_sell': 'دلار',
    'aed_sell': 'درهم',
    'eur': 'یورو',
    'try': 'لیر',
    'sek': 'کرون سوئد',
    'dkk': 'کرون دانمارک',
    'nok': 'کرون نروژ',
    'cny': 'یوان چین',
    'myr': 'رینگیت مالزی',
    'cad': 'دلار کانادا',
    'chf': 'فرانک سوئیس',
    'aud': 'دلار استرالیا',
    'azn': 'منات آذربایجان',
    'kwd': 'دینار کویت',
    'sgd': 'دلار سنگاپور',
    'rub': 'روبل روسیه',
    'qar': 'ریال قطر',
    'afn': 'افغانی',
    'omr': 'ریال عمان'
}

def get_usdt_price_from_api():
    url = 'https://api.tetherland.com/currencies'   
    response = requests.get(url)
    response.raise_for_status()

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise ValueError("Unable to parse JSON", str(e))

    usdt_currency = data['data']['currencies'].get('USDT')
    if usdt_currency is None:
        raise KeyError("USDT not found in response")
    
    price = usdt_currency.get('price')
    if price is None:
        raise KeyError("Price not found in USDT object")

    return price

tehran_timezone = pytz.timezone('Asia/Tehran')
def calculate_buy_discount(original_price, discount_percentage):
    original_price = int(original_price)
    discounted_price = original_price - (original_price * discount_percentage / 100)
    return str(round(int(discounted_price)))


def calculate_sell_price(original_price, discount_percentage):
    original_price = int(original_price)
    discounted_price = original_price + (original_price * discount_percentage / 100)
    return str(round(int(discounted_price)))

    
def get_navasan_data():
    api_key = 'premCc2QyVz3qwEH2szdjOZfi1qU5SpO'
    url = f'http://api.navasan.tech/latest/?api_key={api_key}'

    response = requests.get(url)
    response.raise_for_status()

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise ValueError("Unable to parse JSON", str(e))

    return data

def get_currency_price_from_navasan(name,currency):
    price = format_number(int(get_navasan_data()[currency]['value']))
    return price

def format_number(number):
    number = int(number)
    locale.setlocale(locale.LC_ALL, '')
    formatted_number = locale.format_string('%d', number, grouping=True)
    return formatted_number



def get_jalali_datetime():
    persian_days = {
        'Monday': 'دوشنبه',
        'Tuesday': 'سه‌شنبه',
        'Wednesday': 'چهارشنبه',
        'Thursday': 'پنج‌شنبه',
        'Friday': 'جمعه',
        'Saturday': 'شنبه',
        'Sunday': 'یکشنبه'
    }
    now = jdatetime.datetime.now()
    jalali_date_time = now.strftime('%Y/%m/%d')
    for en_day, fa_day in persian_days.items():
        jalali_date_time = jalali_date_time.replace(en_day, fa_day)
    jalali_date_time = jalali_date_time.replace("٠", "۰").replace("١", "۱").replace("٢", "۲").replace("٣", "۳").replace("٤", "۴").replace("٥", "۵").replace("٦", "۶").replace("٧", "۷").replace("٨", "۸").replace("٩", "۹")
    return jalali_date_time


def get_jalali_day():
    persian_days = {
        'Monday': 'دوشنبه',
        'Tuesday': 'سه‌شنبه',
        'Wednesday': 'چهارشنبه',
        'Thursday': 'پنج‌شنبه',
        'Friday': 'جمعه',
        'Saturday': 'شنبه',
        'Sunday': 'یکشنبه'
    }
    now = jdatetime.datetime.now()
    jalali_date_time = now.strftime('%A')
    for en_day, fa_day in persian_days.items():
        jalali_date_time = jalali_date_time.replace(en_day, fa_day)
    jalali_date_time = jalali_date_time.replace("٠", "۰").replace("١", "۱").replace("٢", "۲").replace("٣", "۳").replace("٤", "۴").replace("٥", "۵").replace("٦", "۶").replace("٧", "۷").replace("٨", "۸").replace("٩", "۹")
    return jalali_date_time


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
CACHE_FILE = os.path.join(DATA_DIR, "currency_cache.json")
CACHE_DURATION = timedelta(minutes=30)



def get_usdt_price_from_api():
    url = 'https://api.tetherland.com/currencies'
    response = requests.get(url)
    response.raise_for_status()

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise ValueError("Unable to parse JSON", str(e))

    usdt_currency = data['data']['currencies'].get('USDT')
    if usdt_currency is None:
        raise KeyError("USDT not found in response")

    price = usdt_currency.get('price')
    if price is None:
        raise KeyError("Price not found in USDT object")

    return float(price)

def update_cache():
    data = get_navasan_data()
    usdt_price = get_usdt_price_from_api()
    data['ustd'] = {'value': usdt_price}

    with open(CACHE_FILE, 'w') as f:
        json.dump({'timestamp': time.time(), 'data': data}, f)

def get_cached_data():
    if not os.path.exists(CACHE_FILE):
        update_cache()

    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
        cache_time = datetime.fromtimestamp(cache['timestamp'])
        if datetime.now() - cache_time > CACHE_DURATION:
            update_cache()
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        return cache['data']

def get_currency_price(currency_code):
    data = get_cached_data()
    if currency_code not in data:
        raise KeyError(f"{currency_code} not found in cached data")
    return float(data[currency_code]['value'])

def is_price_within_range(price, currency):
    # Find the currency code from cur_dict
    currency_code = None
    for key, value in cur_dict.items():
        if value == currency:
            currency_code = key
            break
    
    if not currency_code:
        raise ValueError(f"Currency {currency} not found in dictionary")

    current_price = get_currency_price(currency_code) if currency_code!='ev' else get_currency_price("ustd")+250
    print("cureent price : ",current_price)

    lower_bound = current_price * 0.95
    upper_bound = current_price * 1.05

    return lower_bound <= price <= upper_bound



import requests
import re
import json
import jdatetime
import locale
import emoji
import re
import urllib.parse
import os
import json
import pandas as pd
import asyncio
from pyrogram import Client
from dotenv import load_dotenv
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")


# custom forward channels 
class CustomChannels(object):
    euro_channels = {
        "spain" : -1002457142632 ,
        "germany" : -1002384522064, 
        "italy" : -1002349489420,
        "france" : -1002329905875,
        "cyprus" : -1002288647780,
         "meow" : -1002339012039
    }
    
    pond_channels = {
        "uk" : -1002481520621
    }
    
    cny_channels = {
        "alibaba" : -1002369021803
    }
    
    usd_channels = {
        "la" : -1002263723875,
         "meow" : -1002339012039
        
    }
    usd_canada_channels = {
        "ca" : -1002340663316
    }
    
    aed_channels = {
        "dubai" : -1002347581386
    }
    
    kron_channels = {
        "denmark" : -1002398357287
    }
    
    swedn_kron = {
        "sweden" : -1002339012039
    }
    
    
    lir_channels = {
        "turkey" : -1002287827533,
        "cyprus" : -1002288647780
    }
    
    thether_Channels = {
        "gap" : -1002343881600
    }
    
    rub_channels = {
        "russia" : -1002347581386
    }


cchannels = CustomChannels()



def send_to_custom_channels(currency:str,message_text:str,kb):
    if "کرون" in currency:
        channels_to_send = cchannels.kron_channels.values()
        for channel in channels_to_send:

            try:
               send_telegram_message(  bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)    
    elif "کانادا" in currency :
        channels_to_send = cchannels.usd_canada_channels.values()
        for channel in channels_to_send:

            try:
                               send_telegram_message(  bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)   
                
    
    
    elif "تتر" in currency :
        channels_to_send = cchannels.thether_Channels.values()
        for channel in channels_to_send:

            try:
                               send_telegram_message(  bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)              
                          
                          
                          
    elif "دلار" in currency :
        channels_to_send = cchannels.usd_channels.values()
        for channel in channels_to_send:

            try:
               send_telegram_message(  bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)    
    
    elif "یورو" in currency :
        channels_to_send = cchannels.euro_channels.values()
        for channel in channels_to_send:

            try:
               send_telegram_message(  bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)    
    
    elif "یوان" in currency :
        channels_to_send = cchannels.cny_channels.values()
        for channel in channels_to_send:

            try:
               send_telegram_message(  bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)    
    
    elif "درهم" in currency:
        channels_to_send = cchannels.aed_channels.values()
        for channel in channels_to_send:

            try:
                
                send_telegram_message(  bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)    
    
    
    elif "پوند" in currency :
        channels_to_send = cchannels.pond_channels.values()
        for channel in channels_to_send:

            try:
                send_telegram_message(
                                        bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)  
                
    elif "لیر" in currency :
        channels_to_send = cchannels.lir_channels.values()
        for channel in channels_to_send:

            try:
                send_telegram_message(
                                        bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)                
    elif "روبل" in currency :
        channels_to_send = cchannels.rub_channels.values()
        for channel in channels_to_send:
            try:
                send_telegram_message(
                                        bot_token=bot_token,
                                        chat_id=channel,
                                        message = message_text,
                                        reply_markup=kb
                                        )
            except Exception as e :
                print(e)

# Helper function to send a message using the Telegram API
def send_telegram_message(bot_token, chat_id, message, reply_markup=None):
    """
    Sends a message to a Telegram chat and returns the message ID.
    
    :param bot_token: Telegram bot token as a string.
    :param chat_id: Chat ID or username of the chat to send the message to.
    :param message: The text message to send.
    :param reply_markup: InlineKeyboardMarkup for buttons.
    :return: The message ID of the sent message.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # print("sending message to >",chat_id)
    # print("chat id type : ",type(chat_id))
    # print("message text >",message)
    payload = {
        'chat_id': chat_id,
        'text': message,
        'reply_markup': json.dumps(reply_markup) if reply_markup else None,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get("ok"):
            return response_data['result']['message_id']
        else:
            print(f"Error from Telegram API: {response_data.get('description')}")
            return None
    except Exception as e:
        print(response.content)
        print(f"Request failed: {e}")
        return None
    
def get_current_jalali_date():
    # Get the current Jalali date and time
    jalali_now = jdatetime.datetime.now()
    
    # Extract the day, month, and year
    day = jalali_now.day
    month = jalali_now.month
    year = jalali_now.year
    
    # Return the date in the format "day month year"
    return f"{day} {month} {year}"


def format_number(number):
    try:
        number = int(number)
        locale.setlocale(locale.LC_ALL, '')
        return locale.format_string('%d', number, grouping=True)
    except ValueError :
        return number    


def clean_string(text):
    # Remove all non-letter characters except for Persian characters
    cleaned_text = re.sub(r'[^\u0600-\u06FFa-zA-Z\s]', '', text)
    # Replace spaces with underscores
    cleaned_text = cleaned_text.replace(' ', '_')
    return cleaned_text


def remove_emoji(text):
    return emoji.replace_emoji(text, replace='')


def generate_telegram_share_url(base_url, text):
    # Encode the URL and text
    encoded_url = urllib.parse.quote(base_url)
    encoded_text = urllib.parse.quote(text)
    
    # Construct the Telegram share URL
    share_url = f"http://t.me/share/url?url={encoded_url}&text={encoded_text}"
    
    return share_url

def get_jalali_date():
    # Dictionary to map English month names to Persian month names
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

    # Get the current Jalali date
    jalali_date = jdatetime.datetime.now()

    # Extract the day and month
    day = jalali_date.day
    month = jalali_date.strftime('%B')

    # Translate the month to Persian
    persian_month = persian_months.get(month, month)

    # Convert the day to Persian numbers
    persian_numbers = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    persian_day = str(day).translate(persian_numbers)

    # Return the formatted date
    return f'{persian_day} {persian_month}'

# Function to create tmp directory if not exists
def create_tmp_dir():
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

# Function to convert JSON data to Excel file
def get_users_excel(json_file, excel_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data['data'])
    df.to_excel(excel_file, index=False)

# Async function to send file using Pyrogram
async def send_excel_file(client, chat_id, file_path):
    await client.send_document(chat_id, file_path)

# Main async function to execute the steps
async def send_users(client,chat_id):
    json_file = 'helpers/DB-FILES/users.json'
    excel_file = 'tmp/users.xlsx'

    create_tmp_dir()
    get_users_excel(json_file, excel_file)
    
    
    await send_excel_file(client, chat_id, excel_file)

import requests





def fexpal_regex(text):
    # Patterns to extract information
    action_currency_pattern = r'#(خرید|فروش) #(یورو|پوند)'
    amount_pattern = r'(🔵|🟣)\s*(خرید|فروش)\s*:\s*(\d+)\s*(یورو|پوند)'
    suggested_price_pattern = r'📩 قیمت پیشنهادی: (\d+) تومان'
    transfer_type_pattern = r'▫️ نوع حواله: (.*)'
    description_pattern = r'▫️ توضیحات: (.*?)(?:\n|$)'

    # Extract information using regex
    action_currency_match = re.search(action_currency_pattern, text)
    amount_match = re.search(amount_pattern, text)
    suggested_price_match = re.search(suggested_price_pattern, text)
    transfer_type_match = re.search(transfer_type_pattern, text)
    description_match = re.search(description_pattern, text, re.DOTALL)

    # Translate action to English
    action_persian = action_currency_match.group(1) if action_currency_match else None
    action_english = "buy" if action_persian == "خرید" else "sell" if action_persian == "فروش" else None

    # Create a dictionary to store the extracted information
    data = {
        "action": action_english,
        "currency": action_currency_match.group(2) if action_currency_match else None,
        "amount": int(amount_match.group(3)) if amount_match else None,
        "suggested_price": int(suggested_price_match.group(1)) if suggested_price_match else None,
        "transfer_type": transfer_type_match.group(1).strip() if transfer_type_match else None,
        "description": description_match.group(1).strip() if description_match else None
    }

    # Convert the dictionary to JSON
    json_data = json.dumps(data, ensure_ascii=False, indent=4)
    return json_data


def patriex_regex(text):
    import re
    import json

    # Updated transaction pattern to handle the new format
    transaction_pattern = r'🔄\s*حواله\s*(\d+).*?بابت\s*(خرید|فروش)\s*(\d+)\s*(یورو|پوند)'
    
    # Other patterns remain the same
    buyer_seller_pattern = r'👤\s*(خریدار|فروشنده):\s*(.*)'
    suggested_price_pattern = r'♦️\s*قیمت پیشنهادی:\s*([\d,]+)\s*تومان'
    country_pattern = r'🌎\s*کشور:\s*#(.*)'
    transfer_type_pattern = r'🧾\s*نوع حواله:\s*#(.*)'
    description_pattern = r'✍️\s*توضیحات:\s*(.*)'

    # Extract information using regex
    transaction_match = re.search(transaction_pattern, text, re.DOTALL)
    buyer_seller_match = re.search(buyer_seller_pattern, text)
    suggested_price_match = re.search(suggested_price_pattern, text)
    country_match = re.search(country_pattern, text)
    transfer_type_match = re.search(transfer_type_pattern, text)
    description_match = re.search(description_pattern, text)

    # Determine the action type and extract currency from the hashtag
    currency_match = re.search(r'#(فروشنده|خریدار)_(یورو|پوند)', text)
    action = "buy" if currency_match and currency_match.group(1) == "خریدار" else "sell"
    currency = currency_match.group(2) if currency_match else None

    # Create a dictionary to store the extracted information
    data = {
        "action": action,
        "amount": int(transaction_match.group(3)) if transaction_match else None,
        "currency": currency,
        "buyer_seller": buyer_seller_match.group(2) if buyer_seller_match else None,
        "suggested_price": int(suggested_price_match.group(1).replace(',', '')) if suggested_price_match else None,
        "country": country_match.group(1) if country_match else None,
        "transfer_type": transfer_type_match.group(1) if transfer_type_match else None,
        "description": description_match.group(1) if description_match else None,
        "status": "active"  # Assuming all transactions are active unless explicitly marked as cancelled
    }

    # Convert the dictionary to JSON
    json_data = json.dumps(data, ensure_ascii=False, indent=4)
    return json_data


def get_euro_price_api():
    response = requests.get("https://open-arz.milaadfarzian.workers.dev/?get=arz")
    return response.json()[1]['price'].replace(",","")


def get_usd_price_api():
    response = requests.get("https://open-arz.milaadfarzian.workers.dev/?get=arz")
    return response.json()[0]['price'].replace(",","")





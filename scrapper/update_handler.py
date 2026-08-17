import requests
from pyrogram import Client, filters
from config import *
from utils import *
from db import *
from persian_names import fullname_fa ,fullname_en
import json
import random
from colorama import Fore, Style, init

init(autoreset=True)


def get_request_post_message_id(req):
    requests_Storage = RequestsDB()
    request = requests_Storage.get(request_id=req)
    return request.get("post_id")
     

def make_up_fake_bids(req):
    requests_Storage = RequestsDB()
    request = requests_Storage.get(request_id=req)
    request_time = ''
    request_price = ""
    

def update_request_post_content(req):
    post_message_id = get_request_post_message_id(req)
    pass 
 


CHANNEL_ID = -1002065261878
bot_token = "7142012125:AAHlSGZiO40Mu6v2X4LcCSJqFcLFqNk4rpM"

app = Client(
    "cryptal-listener",
    api_id=api_id,
    api_hash=api_hash,
    session_string="BADq6zgApvhQP6kUncqawU4N8H85q-u0YptGp1bvYFLM50UxYTczHwX_17pfXocTpLZDWuaM3Bt_5yLewJioputSOwx1tqpyS75_y7CZn6aNBpNqrBRzwrIPyTkhU7cJoLREEhGI5C45w6OfYAfeDf9ab2cvQ0uQiuBY38AdOMpzQhR46hdbL0HOYdLvaWBgNjE9SNPhkcfaST7jT3F-BQALCAPAA14XcIYxS5QrZexVG2XlAQMYrQITZbvgNBkFmEd3bKcbBhgYh5n_gV1ypNfQTHfimHlQKwcBM3jWRnlln6CGqW3Zd_qIwsoN0DWJXQOaGnLE7gsd4Da8SbZMWc1GfQRFQAAAAAGvtXzGAA"
)



async def from_beta(_, __, m):
    print(m)
    try:
        sender_chat = m.sender_chat.id
        print(Fore.CYAN + f"Sender chat ID: {sender_chat}")
        if sender_chat == -1002434628718:
            print("New message from beta channel")
            return True
        return False
    except Exception as e:
        print(f"Error in from_beta: {e}")
        return False

async def from_fexpal(_, __, m):
    if not m.sender_chat:
        return False
    try:
        sender_chat = m.sender_chat.id
        if sender_chat == fexpal_channel_id:
            return True
        return False
    except Exception as e:
        print(f"Error in from_fexpal: {e}")
        return False

async def from_patrius(_, __, m):
    if not m.sender_chat:
        return False
    try:
        sender_chat = m.sender_chat.id
        if sender_chat == patriex_channel_id:
            return True
        return False
    except Exception as e:
        return False

is_from_beta = filters.create(func=from_beta)
is_from_fexpal = filters.create(func=from_fexpal)
is_from_patrius = filters.create(func=from_patrius)

def get_post_text(req):
    try:
        request_id = req["request_id"]
        user_id = req['user_id']
        user = users.get(user_id)
        name = random.choice([fullname_fa('random'),fullname_en("random")])
        currency = req["currency"]

        successfull_transactions = random.randint(1, 20)
        failed_transactions = random.randint(1, min(10, successfull_transactions - 1))

        transaction_method = req["payment_method"]
        transaction_type = "خریدار" if req["exchange_type"] == "buyer" else "فروشنده"
        country = user["country"]
        price = format_number(req["price"])
        amount = req["amount"]
        description = req["description"] if req["description"] is not None else "ندارد"
        for_this = "خرید" if transaction_type == "خریدار" else "فروش"
        emoji = "🔵" if for_this == 'خرید' else "🟣"
        text_template = f'''

🔄 حواله {request_id} بابت {"خرید" if transaction_type=="خریدار" else "فروش"} {format_number(int(amount))} #{remove_emoji(currency).strip().replace(" ","_")} 


👤 #{transaction_type}_{remove_emoji(currency).strip().replace(" ","_")} 
⤵️ تاریخچه تبادلات کاربر
🟢 موفق: {successfull_transactions} | 🔴 ناموفق: {failed_transactions}


♦️ قیمت پیشنهادی:  {price} {"" if price == "توافقی🤝" else "تومان"}
🌎 کشور: {random.choice(['آلمان',"ترکیه","ایران","امارات","کانادا"])}
🧾 نوع حواله : {remove_emoji(transaction_method)}

{"" if description == "ندارد" or description =="" else "<blockquote>▫️ توضیحات: {}</blockquote>".format(description)}

📨 ثبت درخواست جدید 👈 {bot_id}

'''
        return text_template
    except Exception as e:
        print(f"Error in get_post_text: {e}")
        





def extract_tether_rate(text):
    pattern = r'نرخ تتر:\s*([\d,]+)'
    
    match = re.search(pattern, text)
    
    if match:
        rate = match.group(1).replace(',', '')
        return rate
    else:
        return None

@app.on_message(filters.chat(-1001314852919))
async def handle_thther_land_messages(client, message):
    if not message.text:
        return
    
    if not extract_tether_rate(message.text):
        return
    
    thether_rate = extract_tether_rate(message.text)
    print("tether price rate" , thether_rate)
    new_request = requests.add(
            user_id=master_user_id,
            currency="💎 تتر",
            amount=random.randint(100,2500),
            description="",
            exchange_type="buyer" ,
            payment_method=random.choice(["TRC20 ( TRX )","TON","ERC20 ( ETH )","BEP20 ( BSC )"]),
            price=thether_rate
        )
        
    post_text = get_post_text(new_request)
    if post_text=="Error generating post text." or post_text==None:
        return


    button = {
        "inline_keyboard": [
            [
                {
                    "text": "ارسال پیشنهاد 💌",
                    "url": f"https://t.me/{bot_id.replace('@','')}?start={new_request['request_id']}"
                }
            ],
            [
                {
                    "text": "تجربیات و نظرات کاربران",
                    "url": "https://t.me/TabadolArz_Comments"
                }
            ]
        ]
    }
    print("post text : ",post_text)
    sent_message_id = send_telegram_message(bot_token, CHANNEL_ID, post_text, reply_markup=button)
    try:
        print("post text",post_text)
        send_to_custom_channels(currency="تتر",message_text = post_text, kb = button)
    except Exception as e :
        print(e) 
    if sent_message_id:
        requests.update(new_request['request_id'], 'post_id', sent_message_id)






    
    
    
    
    
    

    
@app.on_message(filters.chat(fexpal_channel_id))
async def handle_fexpal_message(client, message):
    try:
        print(Fore.CYAN + "Handling message from fexpal")
        message_initial_data = json.loads(fexpal_regex(message.text))

        currency = message_initial_data["currency"]
        items = [
            "💵 تتر",
            "💳 پرفکت مانی",
            "💷 پوند",
            "💲 دلار",
            "🇦🇪 درهم",
            "💶 یورو",
            "💶 لیر",
            "🇸🇪 کرون سوئد",
            "🇩🇰 کرون دانمارک",
            "🇳🇴 کرون نروژ",
            "🇨🇳 یوان چین",
            "❌ انصراف"
        ]
        for item in items:
            if currency in item:
                currency = item
                break
        
        new_request = requests.add(
            user_id=master_user_id,
            currency=currency,
            amount=message_initial_data["amount"],
            description=message_initial_data["description"],
            exchange_type="buyer" if message_initial_data['action'] == "buy" else "seller",
            payment_method=message_initial_data["transfer_type"],
            price=message_initial_data['suggested_price']
        )
        
        post_text = get_post_text(new_request)
        if post_text=="Error generating post text." or post_text==None:
            return

        button = {
            "inline_keyboard": [
                [
                    {
                        "text": "ارسال پیشنهاد 💌",
                        "url": f"https://t.me/{bot_id.replace('@','')}?start={new_request['request_id']}"
                    }
                ],
                [
                    {
                        "text": "تجربیات و نظرات کاربران",
                        "url": "https://t.me/TabadolArz_Comments"
                    }
                ]
            ]
        }

        sent_message_id = send_telegram_message(bot_token, CHANNEL_ID, post_text, reply_markup=button)
        try:
            print("post text",post_text)
            send_to_custom_channels(currency=currency,message_text = post_text, kb = button)
        except Exception as e :
            print(e) 
        if sent_message_id:
            requests.update(new_request['request_id'], 'post_id', sent_message_id)
    except Exception as e:
        print(f"Error in handle_fexpal_message: {e}")

@app.on_message(filters.chat(patriex_channel_id))
async def handle_patrius_message(client, message):
    try:
        message_initial_data = json.loads(patriex_regex(message.text))

        currency = message_initial_data["currency"]
        items = [
            "💵 تتر",
            "💳 پرفکت مانی",
            "💷 پوند",
            "💲 دلار",
            "🇦🇪 درهم",
            "💶 یورو",
            "💶 لیر",
            "🇸🇪 کرون سوئد",
            "🇩🇰 کرون دانمارک",
            "🇳🇴 کرون نروژ",
            "🇨🇳 یوان چین",
            "❌ انصراف"
        ]
        for item in items:
            if currency in item:
                currency = item
                break
        
        new_request = requests.add(
            user_id=master_user_id,
            currency=currency,
            amount=message_initial_data["amount"],
            description=message_initial_data["description"],
            exchange_type="buyer" if message_initial_data['action'] == "buy" else "seller",
            payment_method=message_initial_data["transfer_type"],
            price=message_initial_data['suggested_price']
        )
        
        post_text = get_post_text(new_request)

        button = {
            "inline_keyboard": [
                [
                    {
                        "text": "ارسال پیشنهاد 💌",
                        "url": f"https://t.me/{bot_id.replace('@','')}?start={new_request['request_id']}"
                    }
                ],
                [
                    {
                        "text": "تجربیات و نظرات کاربران",
                        "url": "https://t.me/TabadolArz_Comments"
                    }
                ]
            ]
        }

        sent_message_id = send_telegram_message(bot_token, CHANNEL_ID, post_text, reply_markup=button)
        try:
            send_to_custom_channels(currency=currency,message_text = post_text, kb = button)
        except Exception as e :
            print(e)     

        if sent_message_id:
            requests.update(new_request['request_id'], 'post_id', sent_message_id)
    except Exception as e:
        print(f"Error in handle_patrius_message: {e}")

print(Fore.YELLOW + "Listening for messages...")

app.run()

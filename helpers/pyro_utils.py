from pyrogram.types import Message
from pyrogram import Client  
from helpers.keyboard import *
from helpers.db import *
from functools import wraps
from helpers.state import state_manager
from pykeyboard import InlineKeyboard, InlineButton
from .cryptal_utils import is_price_within_range
from helpers.utils import format_number, clean_string, remove_emoji , fetch_euro_min_max , fetch_ustd_min_max
from asyncio import sleep
from configs.config import *
from pyrogram import enums
from pyrogram.errors import UserNotParticipant


async def show_user_menu(client: Client, message: Message):
    # try:
    #         user_id = message.from_user.id
    #         member = await client.get_chat_member(force_join_channel_id, user_id)
    # except UserNotParticipant:
    #         await send_guest_membersip_alert(message)
    #         return

    user_main_menu_text = f"""کاربر محترم {message.from_user.mention} سلام 👋🏼

🔹 برای ادامه از منوی زیر گزینه مورد نظرتون رو انتخاب کنید"""
    kb = user_menu
    await message.reply(text=user_main_menu_text, reply_markup=kb, quote=True)

async def show_admin_menu(client: Client, message: Message):
    admin_main_menu_text = f'''ادمین محترم {message.from_user.mention} سلام 👋🏼

🔹 برای ادامه از منوی زیر گزینه مورد نظرتون رو انتخاب کنید'''
    kb = admin_menu
    await message.reply(text=admin_main_menu_text, reply_markup=kb, quote=True)

async def send_guest_membersip_alert(message: Message):
    kb = join_button
    await message.reply("برای استفاده از خدمات ربات ابتدا می‌بایست در کانال تبادل ارز عضو شوید.", reply_markup=kb)

def is_added(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        user_id = message.from_user.id
        if not users.user_exists(user_id):
            users.add(user_id=user_id,
                      first_name=message.from_user.first_name,
                      last_name=message.from_user.last_name,
                      username=message.from_user.username)
        return await func(client, message)
    return wrapper

async def handle_filing_form(message: Message):
    user_id = message.from_user.id
    user_current_state = await state_manager.get(message)
    # print(f"user current state : {user_current_state}")

    if user_current_state == 'name' and message.text:
        users.update(user_id, "name", message.text)
        await state_manager.set('number', message)
        await message.reply(quote=True, text='''📱 روی دکمه (  ارسال شماره تماس )  کلیک کنید و شماره تماس خودتون رو به اشتراک بزارید''', reply_markup=get_contact_markup())       

    elif user_current_state == 'country' and message.text:
        users.update(user_id, 'country', message.text)
        await message.reply("ثبت اطلاعات با موفقیت انجام شد برای ادامه به منوی اصلی بازگردید !", reply_markup=home_kb)
        await state_manager.delete(message)

    elif user_current_state == 'number' and message.contact:
        await state_manager.set('country', message)
        users.update(user_id, "phone_number", message.contact.phone_number)
        await message.reply(quote=True, text='''💭 کشور محل زندگیتون رو وارد کنید''', reply_markup=country_kb())

async def user_has_unfilled_field(client: Client, message: Message):
    return users.not_filled_form(message.from_user.id)

async def show_profile(message: Message):
    user_id = message.from_user.id
    user_data = users.get(user_id)

    profile_info = f"🆔 آیدی عددی: {user_data['user_id']}\n" \
                   f"📞 شماره تماس: {user_data['phone_number'] if user_data['phone_number'] is not None else 'وارد نشده !'}\n" \
                   f"👤 نام و نام خانوادگی: {user_data['name'] if user_data['name'] is not None else 'وارد نشده !'}\n" \
                   f"🔖 نام کاربری: {user_data['username'] if user_data['username'] is not None else 'وارد نشده !'}\n" \
                   f"🌍 کشور: {user_data['country'] if user_data['country'] is not None else 'وارد نشده !'}\n" \
                   f"📅 تاریخ عضویت: {user_data['joined_date'].replace(' ', '/')}\n" \
                   f"📅 تعداد زیرمجموعه : {len(user_data['refrals'].split('.')) if user_data['refrals'] else 0}\n" \
                   f"✅ معامله موفق : {(user_data['successfull_transactions'])} \n"\
                   f"🚫 معامله ناموفق : {(user_data['failed_transactions'])} \n"\
                   f"👝 کیف پول : {format_number(user_data['wallet'])} تومان\n"

    await message.reply(profile_info, quote=True, reply_markup=edit_kb)

async def handle_about_us(message):
    await message.reply(quote=True, text='''💎تبادل ارز، اولین بازار معاملاتی ارز در ایران💎

🔹خرید و فروش به صورت P2P

💯 انجام معاملات با کمترین کارمزد، بهترین نرخ، امن و بدون واسطه بین طرفین

✅ امکان معامله بر پایه‌ی تتر و ریال

📢کانال معاملات:    @TabadolArz_Trades

💬گروه تبادل نظر:       @TabadolArz_Group
''', reply_markup=social_kb)

async def get_post_text(client,request_id: int):
    req = requests.get(request_id)
    name = ''
    user_id = req['user_id']
    # print(user_id)
    user = users.get(user_id)
    post_id = req.get("post_id",None)
    if user.get("user_id")==master_user and post_id!=None:
        try:
            mess = await client.get_messages(discussion_send_chat, int(req.get("post_id")))
            mess_text = mess.text
            if "خریدار" in mess_text :
                # print(user)
                # print("bid fromn ^^")
                # print(mess_text)
                registered_name = mess_text.split("👤 خریدار:")[1].split("⤵️")[0].strip()
                # print(f"by {registered_name}")
                name = registered_name
            else:
                # print(user)
                # print("bid fromn ^^")
                
                # print(mess_text)
                registered_name = mess_text.split("👤 فروشنده:")[1].split("⤵️")[0].strip()
                # print(f"by {registered_name}")
                name = registered_name
        except :
            pass        
    else :
        name = user["name"]
                    
                    
    

    currency = req["currency"]
    successfull_transactions = user["successfull_transactions"]
    failed_transactions = user["failed_transactions"]
    transaction_method = req["payment_method"]
    transaction_type = "خریدار" if req["exchange_type"] == "buyer" else "فروشنده"
    country = user["country"]
    price = format_number(req["price"])
    amount = req["amount"]
    description = req["description"] if req["description"] is not None else "ندارد"
    for_this = "خرید" if  req["exchange_type"] == "buyer" else "فروش"
    text_template = f'''

    
🔄 حواله {request_id}  بابت {for_this} {format_number(int(amount))} #{remove_emoji(currency).strip().replace(" ","_")} 


👤 #{transaction_type}_{remove_emoji(currency).strip().replace(" ","_")} 
⤵️ تاریخچه تبادلات کاربر
🟢 موفق: {successfull_transactions} | 🔴 ناموفق: {failed_transactions}


♦️ قیمت پیشنهادی:  {price} {"" if price == "توافقی🤝" else "تومان"}
🌎 کشور: {country}
🧾 نوع حواله : {remove_emoji(transaction_method)}


{"" if description == "ندارد" else "<blockquote>▫️ توضیحات: {}</blockquote>".format(description)}

📨 ثبت درخواست جدید 👈 {bot_id}


'''
    return text_template




async def get_post_text2(client,request_id: int):
    req = requests.get(request_id)
    name = ''
    user_id = req['user_id']
    # print(user_id)
    user = users.get(user_id)
    post_id = req.get("post_id",None)
    if user.get("user_id")==master_user and post_id!=None:
        try:
            mess = await client.get_messages(discussion_send_chat, int(req.get("post_id")))
            mess_text = mess.text
            if "خریدار" in mess_text :
                # print(user)
                # print("bid fromn ^^")
                # print(mess_text)
                registered_name = mess_text.split("👤 خریدار:")[1].split("⤵️")[0].strip()
                # print(f"by {registered_name}")
                name = registered_name
            else:
                # print(user)
                # print("bid fromn ^^")
                
                # print(mess_text)
                registered_name = mess_text.split("👤 فروشنده:")[1].split("⤵️")[0].strip()
                # print(f"by {registered_name}")
                name = registered_name
        except :
            pass        
    else :
        name = user["name"]
                    
                    
    

    currency = req["currency"]
    successfull_transactions = user["successfull_transactions"]
    failed_transactions = user["failed_transactions"]
    transaction_method = req["payment_method"]
    transaction_type = "خریدار" if req["exchange_type"] == "buyer" else "فروشنده"
    country = user["country"]
    price = format_number(req["price"])
    amount = req["amount"]
    description = req["description"] if req["description"] is not None else "ندارد"
    for_this = "خرید" if  req["exchange_type"] == "buyer" else "فروش"
    text_template = f'''

    
🔄 حواله {request_id}  بابت {for_this} {format_number(int(amount))} #{remove_emoji(currency).strip().replace(" ","_")} 


👤 #{transaction_type}_{remove_emoji(currency).strip().replace(" ","_")}  : {name} 
⤵️ تاریخچه تبادلات کاربر
🟢 موفق: {successfull_transactions} | 🔴 ناموفق: {failed_transactions}


♦️ قیمت پیشنهادی:  {price} {"" if price == "توافقی🤝" else "تومان"}
🌎 کشور: {country}
🧾 نوع حواله : {remove_emoji(transaction_method)}


{"" if description == "ندارد" else "<blockquote>▫️ توضیحات: {}</blockquote>".format(description)}

📨 ثبت درخواست جدید 👈 {bot_id}


'''
    return text_template


async def generate_post(message: Message, request_id: int):
    req = requests.get(request_id)
    user_id = req['user_id']
    user = users.get(user_id)
    name = user["name"]
    currency = req["currency"]
    successfull_transactions = user["successfull_transactions"]
    failed_transactions = user["failed_transactions"]
    transaction_method = req["payment_method"]
    transaction_type = "خریدار" if req["exchange_type"] == "buyer" else "فروشنده"
    country = user["country"]
    price = format_number(req["price"])
    amount = req["amount"]
    description = req["description"] if req["description"] is not None else "ندارد"
    way = "خرید" if transaction_type == 'خریدار' else "فروش"
    text_template = f'''

    
🔄 حواله {request_id}  بابت {way} {format_number(int(amount))} #{remove_emoji(currency).strip().replace(" ","_")} 


👤 #{transaction_type}_{remove_emoji(currency).strip().replace(" ","_")} : {name}
⤵️ تاریخچه تبادلات کاربر
🟢 موفق: {successfull_transactions} | 🔴 ناموفق: {failed_transactions}


♦️ قیمت پیشنهادی:  {price} تومان
🌎 کشور: {country}
🧾 نوع حواله : {remove_emoji(transaction_method)}


{"" if description == "ندارد" else "<blockquote>▫️ توضیحات: {}</blockquote>".format(description)}

📨 ثبت درخواست جدید 👈 {bot_id}


'''
    
    await message.reply(quote=True, text=text_template)
    await message.reply("⬆️  درصورت تایید پیش نمایش آگهی لطفا گزینه تایید و ارسال رو انتخاب کنید", reply_markup=request_kb())
    await state_manager.set('send-request', message)

async def handle_user_request_generation(client: Client, message: Message):
    user_id = message.from_user.id
    user_current_state = await state_manager.get(message)
    # print(f"user [{user_id}] state > {user_current_state}")
    user_current_request = await state_manager.get_user_last_request(message)
    # print(f"user [{user_id}] request id > {user_current_request}")
    if user_current_request is None:
        user_request_id = requests.add(user_id)
        await state_manager.set_user_last_request(message, user_request_id)
        print(f"user {message.from_user.first_name}({message.from_user.id}) new Request created [ < {user_request_id} > ]")

    if user_current_state == 'currency' and message.text:
        button_labels = [
            "💎 تتر", "💳 پرفکت مانی",
            "💷 پوند", "💲 دلار",
            "🇦🇪 درهم", "💶 یورو",
            "💶 لیر", "🇸🇪 کرون سوئد",
            "🇩🇰 کرون دانمارک", "🇳🇴 کرون نروژ",
            "🇨🇳 یوان چین", "🇲🇾 رینگیت مالزی",
            "🇨🇦 دلار کانادا", "🇨🇭 فرانک سوئیس",
            "🇦🇺 دلار استرالیا", "🇦🇿 منات آذربایجان",
            "🇰🇼 دینار کویت", "🇸🇬 دلار سنگاپور",
            "🇷🇺 روبل روسیه", "🇶🇦 ریال قطر",
            "🇦🇫 افغانی", "🇴🇲 ریال عمان",
            "❌ انصراف"
        ]
        if message.text not in button_labels:
            await message.reply("🔺 گزینه مورد نظر را انتخاب نمایید:")   
            return
        
        if message.text=="💎 تتر":
            # checkbeing joinded in ththerland
            tether_channel = -1002343881600
            try:
                    user_id = message.from_user.id
                    member = await client.get_chat_member(tether_channel, user_id)
                    
            except UserNotParticipant:
                    text= " کاربر محترم شما هنوز در گروه گروه جامع تبادل ارز دیجیتال تتر(خرید و فروش رمزارز تتر TRC20 و BEP20) جوین نشده اید برای ادامه روی لینک گروه کلیک کنید و عضو بشید و بعد از عضویت تایید عضویت رو انتخاب کنید : "
                    joined_thter_buttons = InlineKeyboard(row_width = 1)
                    joined_thter_buttons.add(
                        InlineButton("عضویت در گروه",url = "https://t.me/TabadolArz_Tether"),
                        InlineButton("تایید عضویت (عضو شدم !)","ustd-joined")
                        
                    )
                    await message.reply(
                        text = text ,
                        reply_markup = joined_thter_buttons
                    )
                    return
            pass
        
        
        else:
            try:
                    user_id = message.from_user.id
                    member = await client.get_chat_member(force_join_channel_id, user_id)
            except UserNotParticipant:
                    await send_guest_membersip_alert(message)
                    return
        
        req_id = await state_manager.get_user_last_request(message)
        requests.update(req_id, 'currency', message.text)
        await state_manager.set('exchange_type', message)
        await message.reply(quote=True, text=f'''⁉️ فروشنده {message.text} هستید یا خریدار آن‌؟


🟢 اگر خریدار هستید پس از پرداخت مبلغ سفارش به صورت ریالی یا تتری نزد تبادل ارز {message.text} آن توسط فروشنده به حساب معرفی شده توسط شما منتقل خواهد شد.

🔴 در صورتی که فروشنده هستید پس از تایید دریافت {message.text} توسط خریدار، مبلغ ریالی یا تتری سفارش پرداخت خواهد شد.''',
                            reply_markup=request_type_kb())

    elif user_current_state == 'exchange_type' and message.text:
        buttons = ["💎 فروشنده هستم", "⭐️ خریدار هستم"]
        if message.text not in buttons:
            await message.reply("🔺 گزینه مورد نظر را انتخاب نمایید:")    
            return
        req_id = await state_manager.get_user_last_request(message)
        requests.update(req_id, 'exchange_type', "seller" if message.text == "💎 فروشنده هستم" else "buyer")
        currency = requests.get(req_id)["currency"]
        await state_manager.set('amount', message)
        way = "خرید" if message.text == "⭐️ خریدار هستم" else "فروش"
        await message.reply(quote=True, text=f'''⁉️ قصد {way} چه مقدار {currency} را دارید ?

🔴 مقدار آن را بصورت یک عدد معتبر تایپ نمایید.''', reply_markup=cance_kb)

    elif user_current_state == 'amount' and message.text:
        if not message.text.isdigit():
            await message.reply("🔺 عدد ورودی نامعتبر است") 
            return
        req_id = await state_manager.get_user_last_request(message)
        requests.update(req_id, 'amount', message.text)
        await state_manager.set('method', message)
        currency = requests.get(req_id)["currency"]
        exchange_type = requests.get(int(req_id)).get('exchange_type')
        way = "خرید" if exchange_type == "buyer" else "فروش"

        if currency == "💳 پرفکت مانی":
            if way=='خرید':
                await message.reply(quote=True, text=f'''⁉️ لطفا شیوه‌ی دریافت {currency} از فروشنده را مشخص کنید.''', reply_markup=method_for_perfect_mony())
            elif way=='فروش':
                await message.reply(quote=True, text=f'''⁉️ لطفا شیوه‌ی پرداخت {currency} به خریدار را مشخص کنید.''', reply_markup=method_for_perfect_mony())
        elif currency == "🇨🇳 یوان چین":
            if way=='خرید':
                await message.reply(quote=True, text=f'''⁉️ لطفا شیوه‌ی دریافت {currency} از فروشنده را مشخص کنید.''', reply_markup=cny_method())
            elif way=='فروش' :
                await message.reply(quote=True, text=f'''⁉️ لطفا شیوه‌ی پرداخت {currency} به خریدار را مشخص کنید.''', reply_markup=cny_method())
        elif currency == "💎 تتر":
            if way=='خرید':
                await message.reply(quote=True, text=f'''⁉️ لطفا شیوه‌ی دریافت {currency} از فروشنده را مشخص کنید.''', reply_markup=method_for_ustd())
            elif way=='فروش' :
                await message.reply(quote=True, text=f'''⁉️ لطفا شیوه‌ی پرداخت {currency} به خریدار را مشخص کنید.''', reply_markup=method_for_ustd())
        
        
        
        else:
            if way=='خرید':
               await message.reply(quote=True, text=f'''⁉️ لطفا شیوه‌ی دریافت {currency} از فروشنده را مشخص کنید.''', reply_markup=payment_mathod_kb())
            elif way=='فروش':
                await message.reply(quote=True, text=f'''⁉️ لطفا شیوه‌ی پرداخت {currency} به خریدار را مشخص کنید.''', reply_markup=payment_mathod_kb())

    elif user_current_state == 'method' and message.text:
        req_id = await state_manager.get_user_last_request(message)
        requests.update(req_id, 'payment_method', message.text)    
        await state_manager.set('price', message)
        currency = requests.get(req_id)["currency"]
        cance_kbr = ReplyKeyboard(row_width=1, resize_keyboard=True)
        cance_kbr.add(
            ReplyButton("توافقی🤝"),
            ReplyButton("❌ انصراف")
        )
        way = "خرید" if requests.get(req_id)['exchange_type'] == 'seller' else "فروش"
        caption = f"""📌 قیمت مد نظر شما برای {way} هر یک واحد {currency} را وارد کنید.


❌ لطفا از ارسال قیمت های خارج از عرف بازار خودداری کنید❗️"""
        req_id = await state_manager.get_user_last_request(message)
        currency = requests.get(req_id)["currency"]
        if  currency=="💶 یورو":
            max_e ,min_e = fetch_euro_min_max()
            caption+=f"""\n\n📍 کاربر محترم میانگین معاملات و مبالغ پیشنهادی برای ارز یورو برای امروز (  حداقل {min_e} تومان و حداکثر {max_e} تومان )  بوده است برای تسریع در انجام معامله خود میتوانید در رنج معمول درخواست یا پیشنهاد خود را ثبت کنید"""
        
        elif currency=="💎 تتر":
            max_e ,min_e = fetch_ustd_min_max()
            caption+=f"""\n\n📍 کاربر محترم میانگین معاملات و مبالغ پیشنهادی برای ارز تتر برای امروز (  حداقل {min_e} تومان و حداکثر {max_e} تومان )  بوده است برای تسریع در انجام معامله خود میتوانید در رنج معمول درخواست یا پیشنهاد خود را ثبت کنید"""
            
        
        await message.reply(quote=True, text=caption, reply_markup=cance_kbr)

    elif user_current_state == 'price' and message.text:
        if not message.text.isdigit() and message.text != "توافقی🤝":
            await message.reply("🔺 عدد ورودی نامعتبر است") 
            return
        elif message.text == "توافقی🤝":    
            req_id = await state_manager.get_user_last_request(message)
            requests.update(req_id, 'price', message.text)   
            await state_manager.set('description', message)
            await message.reply(quote=True, text='''📑 توضیحات 
    درصورتیکه تمایل دارید توضیحاتی به آگهی اضافه کنید ، توضیح خودتون رو بصورت مختصر ارسال کنید 

    🗞 در غیر اینصورت روی گزینه ادامه کلیک کنید :''', reply_markup=desc_kb())
            return

        price = int(message.text)
        req_id = await state_manager.get_user_last_request(message)
        currency = requests.get(req_id)["currency"]
        euro_max, euro_min = fetch_euro_min_max()
        ustd_max, ustd_min = fetch_ustd_min_max()

        if currency == "💶 یورو":
            if not euro_min <= price <= euro_max:
                await message.reply("قیمت وارد شده نامتعارف است؛ ثبت آگهی صرفا در رنج قیمت‌های روز هر ارز ممکن می‌باشد❗️")
                return

        elif currency == "💎 تتر":
            if not ustd_min <= price <= ustd_max:
                await message.reply("قیمت وارد شده نامتعارف است؛ ثبت آگهی صرفا در رنج قیمت‌های روز هر ارز ممکن می‌باشد❗️")
                return

        # else:
        #     if not 5000 < price < 200000:
        #         await message.reply("قیمت وارد شده نامتعارف است؛ ثبت آگهی صرفا در رنج قیمت‌های روز هر ارز ممکن می‌باشد❗️")
        #         return

        requests.update(req_id, 'price', message.text)
        await state_manager.set('description', message)
        await message.reply(quote=True, text='''📑 توضیحات 
درصورتیکه تمایل دارید توضیحاتی به آگهی اضافه کنید ، توضیح خودتون رو بصورت مختصر ارسال کنید 

🗞 در غیر اینصورت روی گزینه ادامه کلیک کنید :''', reply_markup=desc_kb())    

    elif user_current_state == 'description':
        req_id = await state_manager.get_user_last_request(message)
        if message.text != "ادامه":
            requests.update(req_id, 'description', message.text)    
        await state_manager.set('confirm', message)
        await message.reply(quote=True, text='درصورت تایید لطفاً گزینه مورد نظرتون رو وارد کنید', reply_markup=request_kb())   

    elif user_current_state == 'confirm' and message.text:
        req_id = await state_manager.get_user_last_request(message)
        if message.text == "تایید و  ارسال ✅":
            await generate_post(message, req_id)  

    elif user_current_state == "send-request" and message.text:
        if message.text == "تایید و  ارسال ✅":
            await message.reply("آگهی شما بلافاصله بعد از تایید ادمین کانال ثبت خواهد شد ")
            
            request_id = await state_manager.get_user_last_request(message)
            kb = start_paramed_kb_request(request_id)
            confirm_admins_kb = InlineKeyboard(row_width=1)
            confirm_admins_kb.add(
                InlineButton("تایید و ارسال آگهی", f"post:{request_id}"),
                InlineButton("رد کردن", f"del:{request_id}"),
            )
            await state_manager.delete(message)
            await show_user_menu(client, message)
            text = await get_post_text2(client,request_id)
            try:
                await client.send_message(chat_id=report_channel, text=text, reply_markup=confirm_admins_kb)
            except Exception as e :
                 print(e)
                 await message.reply(str(e))
                 return

async def handle_user_bid(client: Client, message: Message):
    user_id = message.from_user.id
    user_current_state = await state_manager.get(message)
    user_bid = await state_manager.get_bid_id(message)
    message_text = message.text

    if '/start' in message_text and " " in message_text:
        param = message_text.split(" ")[1]
        print("bid param", param)

        if not param.isdigit() or not requests.get(int(param)):
            await show_user_menu(client, message)
            return

        request = requests.get(int(param))
        user_requested_id = request["user_id"]
        if int(user_requested_id) == message.from_user.id:
            await message.reply(quote=True, text="امکان ارسال پیشنهاد به درخواست خودتون وجود نداره !", reply_markup=home_kb)
            return

        request_status = request['open_to_bid']
        if not request_status:
            await message.reply(text="فرصت ارسال پیشنهاد به این درخواست به اتمام رسیده است !", quote=True, reply_markup=home_kb)
            await state_manager.reset(message)
        elif request_status:
            pre_text = f"🟢 شما در حال ارسال پیشنهاد برای حواله {param} می باشید."
            pre_text += "\n\n" + await get_post_text(client,int(param))

            exchange_type = "خریدار" if request["exchange_type"] == 'seller' else "فروشنده"
            currency = remove_emoji(request["currency"])
            post_text = f'⁉️ لطفا به عنوان {exchange_type} قیمت پیشنهادی خود  برای هر یک {currency} را به تومان وارد کنید:'
            text = pre_text + '\n\n' + post_text
            await message.reply(quote=True, reply_markup=cance_kb, text=text)
            bid_id = bids.add(user_id=user_id, request_id=request["request_id"])
            await state_manager.set_bid_id(message, bid_id)
            await state_manager.set("sending-bid-price", message)

    elif user_current_state == 'sending-bid-price':
        if not message_text.isdigit():
            await message.reply(quote=True, text="🔺 عدد ورودی نامعتبر است", reply_markup=cance_kb)
            return

        bid_details = bids.get(bid_id=user_bid)
        request_id = bid_details["request_id"]
        request_details = requests.get(request_id=request_id)
        currency = request_details["currency"]
        price = int(message.text)
        euro_min_max = fetch_euro_min_max()
        ustd_min_max = fetch_ustd_min_max()

        if currency == "💶 یورو":
            if not euro_min_max or not euro_min_max[1] - 6000 < price < euro_min_max[0] + 6000:
                await message.reply("قیمت وارد شده نامتعارف است؛ ثبت آگهی صرفا در رنج قیمت‌های روز هر ارز ممکن می‌باشد❗️")
                return

        elif currency == "💎 تتر":
            if not ustd_min_max or not ustd_min_max[1] - 2000 < price < ustd_min_max[0] + 2000:
                await message.reply("قیمت وارد شده نامتعارف است؛ ثبت آگهی صرفا در رنج قیمت‌های روز هر ارز ممکن می‌باشد❗️")
                return

        
        bids.update(user_bid, "price", int(message.text))
        await message.reply("آیا از ارسال پیشنهاد خود اطمینان دارید ؟", reply_markup=request_kb())
        await state_manager.set("confirm-bid", message)

    elif user_current_state == "confirm-bid":
        user_id = await state_manager.get_bid_id(message)
        bid_details = bids.get(bid_id=int(user_bid))
        request_id = bid_details["request_id"]
        request_details = requests.get(request_id=request_id)
        name = users.get(bid_details['user_id'])["name"]
        bidder_user_id = users.get(bid_details['user_id'])["user_id"]
        mtype = "خرید" if request_details["exchange_type"] == 'buyer' else "فروش" 
        
        if message.text == "تایید و  ارسال ✅":
            send_message_kb = InlineKeyboard(row_width=1)
            send_message_kb.add(
                InlineButton("حذف پیشنهاد", f"delete_bid:{int(user_bid)}"),
            )
            await message.reply("پیشنهاد شما با موفقیت رو این حواله ثبت شد", reply_markup=send_message_kb)
            await show_user_menu(client, message)
            bid_request_text = '''↩️ کاربری روی درخواست شما (  {}  ) مبلغ {} را برای {} هر {} ثبت کرد 

🔻 برای تایید یا رد این  پیشنهاد از گزینه های زیر استفاده کنید'''.format(
                f"[حواله {request_id}]({group_link}/{request_details['post_id']})",
                bid_details["price"],
                mtype,
                remove_emoji(request_details["currency"])
            )




            sudo_users_allowed_list = [
                982290123 ,
                7284701597,
                6379933870
            ] 
            
            
            
            if request_details["user_id"] in sudo_users_allowed_list:
                print("bidder id : " , int(bidder_user_id))
                details = users.get(user_id  = int(bidder_user_id))
                print(details)
                user_bidder_full_details=f"""
                
                
                👤 اطلاعات کاربر پیشنهاد دهنده :

• آیدی عددی : {details.get('user_id')}
• شماره تماس : {details.get('phone_number')} 
• نام کاربری: @{details.get('username')}
• کشور : {details.get('country')} 
• تاریخ عضویت : {details.get('joined_date')}


                """
                bid_request_text+=user_bidder_full_details
            try:    
                await client.send_message(chat_id=request_details["user_id"], text=bid_request_text, reply_markup=bid_final_kb(int(user_bid)))
            except Exception as e :
                 print(e)
                 await message.reply(str(e))
                 return    
            await update_request_status(client, message, int(request_id))

async def update_request_status(client: Client, message: Message, request_id: int):
    name = ''
    bids_on_request = bids.get_related_bid_with_request_id(request_id=request_id)
    req = requests.get(request_id)
    user = users.get(req['user_id'])

        
        
    if not bids_on_request:
        return

    bids_list = ""
    for item in bids_on_request:
        try:
            status_emoji = "✅" if item["status"] == 'approved' else "❌" if item["status"] == 'rejected' else "⏳"
            suggested_price = format_number(int(item["price"]))
            user_telegram_firstname = users.get(item["user_id"])["name"]
            date_of_the_bid = item["date"]
            bids_list += f"\n{status_emoji} {suggested_price} تومان در {date_of_the_bid}"
        except :
            continue    

    

    currency = req["currency"]
    successfull_transactions = user["successfull_transactions"]
    failed_transactions = user["failed_transactions"]
    transaction_method = req["payment_method"]
    transaction_type = "خریدار" if req["exchange_type"] == "buyer" else "فروشنده"
    country = user["country"]
    price = format_number(req["price"])
    amount = req["amount"]
    description = req["description"] if req["description"] is not None else "ندارد"
    for_this = "خرید" if transaction_type == "خریدار" else "فروش"
    post_text = f"📨 ثبت درخواست جدید 👈 {bot_id}"
    text_template = f'''


🔄 حواله {request_id}  بابت {for_this} {format_number(int(amount))} #{remove_emoji(currency).strip().replace(" ","_")}


👤 #{transaction_type}_{remove_emoji(currency).strip().replace(" ","_")} 
⤵️ تاریخچه تبادلات کاربر
🟢 موفق: {successfull_transactions} | 🔴 ناموفق: {failed_transactions}


♦️ قیمت پیشنهادی:  {price} تومان
🌎 کشور: {country}
🧾 نوع حواله : {remove_emoji(transaction_method)}


{"" if description == "ندارد" else f"<blockquote>▫️ توضیحات: {description}</blockquote>"}

{bids_list}

 

'''
    text_template += "\n" + post_text
    # print(text_template)
    post_id = req["post_id"]
    await client.edit_message_text(chat_id=discussion_send_chat, message_id=post_id, text=text_template, reply_markup=start_paramed_kb_request(request_id))
    # print(f"request status updated with post_if > {post_id}")
        
async def find_request(message: Message):
    user_state = await state_manager.get(message)
    if user_state == 'select=serach=currency':
        # print(message.text)
        try:
            await state_manager.set_search_currency(message, message.text)
        except:
            pass    
        await message.reply("نوع جستجوی خود را انتخاب کنید :", reply_markup=meowkb()) 
        await state_manager.set('select=serach=type', message)

    elif user_state == 'select=serach=type':
        a = await state_manager.jget(message)
        # print(a)

        user_search_currency = a.get('currency') 
        user_search_type = message.text
        # print("us", user_search_currency)
        results = requests.get_requets_by_currency(user_search_currency, user_search_type)
        # print(results)
        if not results:
            await message.reply("جستجوی شما نتیجه ای در بر نداشت !", reply_markup=home_kb)
            await state_manager.delete(message)
            return
        temp_txt = ""
        for item in results:
            try:
                price = item.get("price")
                currency = remove_emoji(user_search_currency)
                amount = item.get("amount")
                exctype = "خرید" if item.get("exchange_type") == 'buyer' else "فروش"
                # print(f"[!] request details > price : {price} - currency : {currency} - amount : {amount} ")

                template = f'[حواله {item.get("post_id")}]({channel_address+str(item.get("post_id"))}) بابت {exctype} {amount} {currency} به مبلغ {format_number(price)}' 
                temp_txt += '\n' + template 
            except :
                continue    

        await message.reply(quote=True, reply_markup=home_kb, text=temp_txt, disable_web_page_preview=True)
        await state_manager.delete(message)

async def send_broadcast_message(client: Client, message: Message):
    await state_manager.delete(message)
    users_list = users.get_all_users_ids()   
    yes_counter = 0 
    no_counter = 0
    broadcast_progress = await message.reply(quote=True, text="ارسال همگانی آغاز شد")
    for user_id in users_list:
        try:
            await message.forward(user_id)
            await sleep(2)
            yes_counter += 1
        except:
            no_counter += 1
            continue 
        await broadcast_progress.edit_text(
            parse_mode=enums.parse_mode.ParseMode.HTML,
            text=f'''تعداد کل کاربران : <u>{len(users_list)}</u>
ارسال موفق : <u>{yes_counter}</u>
↩️ ارسال ناموفق : <u>{no_counter}</u>
<blockquote>ارسال ناموفق به معنای این است که کاربر ربات رو بلاک کرده یا دیلیت اکانت کرده است .</blockquote>'''
        )

    await message.reply("ارسال همگانی به اتمام رسید !")
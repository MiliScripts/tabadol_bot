from pykeyboard import ReplyButton , ReplyKeyboard , InlineButton , InlineKeyboard
from configs.config import force_join_channel_link , bot_id , support_chat_link  , channel_address , group_link , comments_url
from pyrogram.types import ReplyKeyboardMarkup , KeyboardButton , InlineKeyboardButton , InlineKeyboardMarkup
from helpers.db import *
cance_kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
cance_kb.add(
    ReplyButton("❌ انصراف")
)



def group_list():
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇹🇷 لیر ترکیه ", url="https://t.me/Cryptal_Turkiye")],
            [InlineKeyboardButton("🇦🇪 درهم  دبی", url="https://t.me/Dubai_Cryptal")],
            [InlineKeyboardButton("🇬🇧 پوند لندن", url="https://t.me/London_Cryptal")],
            [InlineKeyboardButton("🇩🇪 یورو آلمان", url="https://t.me/Germany_Cryptal")],
            [InlineKeyboardButton("🇪🇸 یورو  اسپانیا", url="https://t.me/Spain_Cryptal")],
            [InlineKeyboardButton("🇮🇹 یورو ایتالیا", url="https://t.me/Italy_Cryptal")],
            [InlineKeyboardButton("🇨🇳 یوآن چین", url="https://t.me/RMB_Cryptal")],
            [InlineKeyboardButton("🇺🇸 دلار آمریکا", url="https://t.me/usa_Cryptal")],
            [InlineKeyboardButton("🇩🇰 کرون دانمارک", url="https://t.me/Denmark_Cryptal")],
            [InlineKeyboardButton("🇷🇺 روبل روسیه", url="https://t.me/TabadolArz_Russia_Group")],
        ]
    )
    return keyboard


user_menu = ReplyKeyboard(row_width=2,resize_keyboard=True)
user_menu.add(
    ReplyButton("➕ ایجاد درخواست جدید"),
    ReplyButton("📤 درخواست های من"),
    ReplyButton("📨 پیشنهادات ارسالی من"),
    ReplyButton("🔎 جستجو"),
    ReplyButton("⭐️ پشتیبانی"),
    ReplyButton("📕 پروفایل"),
    ReplyButton("🚻 رفرال (زیرمجموعه گیری)"),
    ReplyButton("⭐️  لیست گروه های مجموعه  ⭐️"),
    ReplyButton("⁉️ درباره ما"),
    ReplyButton("🗣️ ارسال بازخورد")
)


admin_menu = ReplyKeyboard(row_width=2,resize_keyboard=True)
admin_menu.add(
    ReplyButton("دریافت لیست کاربران 🖨"),
    ReplyButton("ارسال همگانی 📲"),
    ReplyButton("راهنمای دستورات"),
)
join_button = InlineKeyboard(row_width=1)
join_button.add(
    InlineButton("💎 عضویت در تبادل ارز 💎",url=group_link),
    InlineButton("☑️ تایید عضویت","confirm-membership")
)


home_kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
home_kb.add(
    ReplyButton("🔙 بازگشت")
)

def get_contact_markup():
    contact_button = KeyboardButton("📱  ارسال شماره تماس", request_contact=True)
    back_button = KeyboardButton("🔙 بازگشت")
    return ReplyKeyboardMarkup([[contact_button],[back_button]], one_time_keyboard=True, resize_keyboard=True)


edit_kb = InlineKeyboard(row_width=1)
edit_kb.add(
    InlineButton("✏️ ویرایش پروفایل",'edit-profile'),
    InlineButton("تسویه کیف پول",'wallet-withdraw')
)

def payment_mathod_kb():
        # Define the buttons
    buttons = [
        [KeyboardButton("انتقال آنلاین(رولوت، پی‌پال، وایز و …)"),KeyboardButton("حواله وسترن یونیون")],
        [KeyboardButton("سایر(درج در توضیحات)"),KeyboardButton("حواله بانکی")],
        [KeyboardButton("❌ انصراف")]
    ]

    # Create the keyboard
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    return keyboard


def method_for_perfect_mony():
    kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
    kb.add(
        ReplyButton("ووچر"),
        ReplyButton("انتقال عادی"),
        ReplyButton("❌ انصراف"))
    return kb    

    
def cny_method():
    kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
    kb.add(
        ReplyButton("انتقال آنلاین(رولوت، پی‌پال، وایز و …)"),
        ReplyButton("انتقال عادی"),
        ReplyButton("حواله بانکی"),
        ReplyButton("❌ انصراف"))


    return kb    


def method_for_ustd():
    kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
    kb.add(
        ReplyButton("TRC20 ( TRX )"),
        ReplyButton("BEP20 ( BSC )"),
        ReplyButton("ERC20 ( ETH )"),
        ReplyButton("TON"),
        ReplyButton("❌ انصراف"))
    
    return kb
    





def currency_kb():
    buttons = [
        [KeyboardButton("💎 تتر")],
        [KeyboardButton("🇨🇦 دلار کانادا") , KeyboardButton("🇷🇺 روبل روسیه")],
        [KeyboardButton("💷 پوند"), KeyboardButton("💲 دلار")],
        [KeyboardButton("🇦🇪 درهم"), KeyboardButton("💶 یورو")],
        [KeyboardButton("💶 لیر"), KeyboardButton("🇸🇪 کرون سوئد")],
        [KeyboardButton("🇩🇰 کرون دانمارک"), KeyboardButton("🇳🇴 کرون نروژ")],
        [KeyboardButton("🇨🇳 یوان چین")],
        [KeyboardButton("❌ انصراف")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)



def request_type_kb():
    kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
    kb.add(
        ReplyButton("💎 فروشنده هستم"),
        ReplyButton("⭐️ خریدار هستم"),
        ReplyButton("❌ انصراف")
    )

    return kb

def desc_kb():
    kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
    kb.add(
        ReplyButton("ادامه"),
        ReplyButton("❌ انصراف")
    )
    return kb



social_kb = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "Instagram", url="https://instagram.com/TabadolArz_Trades"
        ),
        InlineKeyboardButton(
            "Telegram", url="https://t.me/TabadolArz_Trades"
        ),  
    ],
    [
        InlineKeyboardButton(
            "Twitter", url="https://x.com/cryptal_ex"
        )
    ]
])

def request_kb():
    kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
    kb.add(

        ReplyButton("تایید و  ارسال ✅"),
        ReplyButton("انصراف ❌")


    )
    return kb



def start_paramed_kb_request(request_id:int):
    """
    returns a link like https://t.me/bot.id?start=13131
    12131 is a request id used for bidding

    
    """
    kb = InlineKeyboard(row_width=1)
    kb.add(
        InlineButton(text = "ارسال پیشنهاد 💌",
                     url = f"https://t.me/{bot_id.replace('@','')}?start={request_id}"),
        InlineButton(text = "نظرات و تجربیات کاربران",
                     url = comments_url)
    )
    return kb



def bid_final_kb(bid_id):
    kb = InlineKeyboard(row_width=2)
    kb.add(
        InlineButton("تایید پیشنهاد","confirm-bid:"+str(bid_id)),InlineButton("رد کردن پیشنهاد","reject-bid:"+str(bid_id)),
    )
    return kb


hey_form = InlineKeyboard(row_width=1)
hey_form.add(
    InlineButton("ثبت اطلاعات شخصی و ادامه","meow3")
)



def paginate_requests(requests, page, per_page=15):
    total_pages = (len(requests) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    for i in requests:
        print(i)
    paginated_requests = requests[start:end]
    return paginated_requests, total_pages


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_inline_keyboard(requests, page, total_pages):
    buttons = []
    for req in requests:
        if req.get("post_id")!=None:
            button_text = f"{'فروش' if req['exchange_type']=='seller' else 'خرید'} {req['amount']} {req['currency']}"
            callback_data = f"request_option:{req['request_id']}"
            buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("« قبلی", callback_data=f"rpage:{page-1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton("بعدی »", callback_data=f"rpage:{page+1}"))

    if navigation_buttons:
        buttons.append(navigation_buttons)
    
    return InlineKeyboardMarkup(buttons)



def format_request_details(request):
    status_choices = {
        "pending" : "درحال پردازش",
        "approved" : "تایید شده",
        "done" : "انجام شده",
        "rejected" : "رد شده",
        "failed" : "کنسل شده"
    }
    details = (
        f"💵 درخواست شماره: {request['request_id']}\n"
        f"💰 مقدار: {request['amount']} {request['currency']}\n"
        f"🏦 روش پرداخت: {request['payment_method']}\n"
        f"📅 تاریخ ایجاد: {request['created_date']}\n"
        f"📄 توضیحات: {'ندارد' if request.get('description')==None else request.get('description')}\n"
        f"📊 وضعیت: {status_choices[request['status']]}\n"
        f"🔹 لینک: {channel_address+str(request.get('post_id', 'نامشخص'))}\n"
    )
    return details

def generate_request_details_keyboard(request_id):
    buttons = [
[
         InlineKeyboardButton("حذف", callback_data=f"delete_request:{request_id}")],
         [InlineKeyboardButton("بازگشت به درخواست ها", callback_data=f"show-req")]
    ]
    return InlineKeyboardMarkup(buttons)




def paginate_bids(bids, page, per_page=50):
    total_pages = (len(bids) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_bids = bids[start:end]
    return paginated_bids, total_pages



from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_bids_inline_keyboard(bids, page, total_pages):
    buttons = []
    for bid in bids:
        if bid.get("price")!=None:
            button_text = f"قیمت: {bid['price']} | تاریخ: {bid['date']}"
            callback_data = f"bid_option:{bid['bid_id']}"
            buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("« قبلی", callback_data=f"bpage:{page-1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton("بعدی »", callback_data=f"bpage:{page+1}"))

    if navigation_buttons:
        buttons.append(navigation_buttons)
    
    return InlineKeyboardMarkup(buttons)




def generate_feedback_keyboard(bid_id, request_id, price, currency):
    button_text = f"درخواست {request_id} به قیمت {price} {currency}"
    callback_data = f"send_feedback:{bid_id}"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(button_text, callback_data=callback_data)]])
    return keyboard


def format_bid_details(bid):
    request = requests.get(int(bid.get("request_id")))
    status_choices = {
        "pending" : "درحال پردازش",
        "approved" : "تایید شده",
        "done" : "انجام شده",
        "rejected" : "رد شده",
        "failed" : "کنسل شده",
        None : "درحال پردازش"
    }
    details = (
        f"🔹 شماره پیشنهاد: {bid['bid_id']}\n"
        f"🔹 مبلع پیشنهادی: {bid['price']}\n"
        f"🔹 تاریخ: {bid['date']}\n"
        f"🔹 وضعیت: {status_choices[bid.get('status','pending')]}\n"
        f"🔹 لینک: {channel_address+str(request.get('post_id', 'نامشخص'))}\n"

    )
    return details

def generate_bid_details_keyboard(bid_id):
    buttons = [
    [InlineKeyboardButton("حذف", callback_data=f"delete_bid:{bid_id}")],
    [InlineKeyboardButton("بازگشت به پیشنهاد ها", callback_data=f"show-bid")]
    ]
    return InlineKeyboardMarkup(buttons)



def meowkb():
    kb = ReplyKeyboard(row_width=1,resize_keyboard=True)
    kb.add(
        ReplyButton("💎 فروشنده "),
        ReplyButton("⭐️ خریدار "),
        ReplyButton("❌ انصراف")
    )

    return kb




def admin_deal_kb(bid_id,request_id):
    requester = requests.get(request_id).get("user_id")
    bider = bids.get(bid_id).get("user_id")
    kb = InlineKeyboard(row_width=1)
    kb.add(
        InlineButton("معامله موفقیت آمیز بود",f'success:{bid_id}'),
        InlineButton("نا موفق از سوی پیشنهاد دهنده",f'failed:{bider}'),
        InlineButton("نا موفق از سوی درخواست دهنده",f'failed:{requester}')
    )
    return kb




def make_start_deal_kb():
    reply_markup=InlineKeyboardMarkup(
                [
                    [  # First row

                        InlineKeyboardButton(  # Opens a web URL
                            "ارتباط با کارشناس معاملات",
                            url= support_chat_link
                        ),
                    ]
                ])
    return reply_markup

def country_kb():
    buttons = [
        [KeyboardButton("🇮🇷 ایران")],
        [KeyboardButton("🇹🇷 ترکیه"), KeyboardButton("🇦🇪 امارات")],
        [KeyboardButton("🇺🇸 آمریکا"), KeyboardButton("🇨🇦 کانادا")],
        [KeyboardButton("🇦🇺 استرالیا"), KeyboardButton("🇬🇧 انگلیس")],
        [KeyboardButton("🇨🇳 چین")],
        # European countries
        [KeyboardButton("🇮🇹 ایتالیا"), KeyboardButton("🇩🇪 آلمان")],
        [KeyboardButton("🇫🇷 فرانسه"), KeyboardButton("🇩🇰 دانمارک")],
        [KeyboardButton("🇳🇴 نروژ"), KeyboardButton("🇸🇪 سوئد")],
        [KeyboardButton("🇪🇸 اسپانیا"), KeyboardButton("🇵🇹 پرتغال")],
        [KeyboardButton("🇳🇱 هلند"), KeyboardButton("🇧🇪 بلژیک")],
        [KeyboardButton("🇦🇹 اتریش"), KeyboardButton("🇭🇺 مجارستان")],
        [KeyboardButton("🇨🇿 چک"), KeyboardButton("🇵🇱 لهستان")],
        [KeyboardButton("🇬🇷 یونان"), KeyboardButton("🇭🇷 کرواسی")],
        [KeyboardButton("🇸🇰 اسلواکی"), KeyboardButton("🇸🇮 اسلوونی")],
        [KeyboardButton("🇫🇮 فنلاند"), KeyboardButton("🇪🇪 استونی")],
        [KeyboardButton("🇱🇻 لتونی"), KeyboardButton("🇱🇹 لیتوانی")],
        [KeyboardButton("🇨🇾 قبرس"), KeyboardButton("🇲🇹 مالت")],
        [KeyboardButton("🇱🇺 لوکزامبورگ"), KeyboardButton("🇮🇪 ایرلند")],
        [KeyboardButton("🇷🇴 رومانی"), KeyboardButton("🇧🇬 بلغارستان")],
        [KeyboardButton("🇸🇰 اسلواکی"), KeyboardButton("🇸🇮 اسلوونی")],
        [KeyboardButton("❌ انصراف")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


    

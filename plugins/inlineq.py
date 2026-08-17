from pyrogram import Client , filters
from pyrogram.types import CallbackQuery
from pykeyboard import InlineKeyboard , InlineButton
from helpers.keyboard import *
from helpers.state import *
from helpers.db import *
from helpers.pyro_utils import update_request_status
from pyrogram import Client, filters
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import urllib.parse
from configs.config import *
from helpers.utils import *

@Client.on_inline_query()
async def inline_query_handler(client, inline_query: InlineQuery):
    query_text = inline_query.query.strip()
    print(query_text)
    if ":" in query_text:
        param = query_text.split(":")[1]
        param_type = query_text.split(":")[0]
        print(param,param_type)
        if param_type=='B':
            if bids.get(int(param)):
                bid = bids.get(int(param))
                request = requests.get(bids.get(int(param)).get("request_id"))
                result = InlineQueryResultArticle(
                id=query_text,  # Unique identifier for this result
                title="برای ارسال کلیک کنید ",
                input_message_content=InputTextMessageContent(
                    message_text=f"""سلام
درخواست رسیدگی به معامله رو دارم ازتون

↩️اطلاعات درخواست حواله 
فروشنده/ خریدار : {users.get(request.get("user_id")).get("name")} 
لینک درخواست: {channel_address}{request.get("post_id")}

↩️ پیشنهاد دهنده 
آیدی عددی : {bid.get("user_id")}
اسم : {users.get(bid.get("user_id")).get("name")}
مبلغ پیشنهادی : {format_number(bid.get('price'))}"""
                ),
                description="درخواست معامله ", # Optional thumbnail URL
            )
                await inline_query.answer(results=[result], cache_time=1)



from helpers.bot_filters import is_admin, broadcasting
from pyrogram import Client, filters
from helpers.pyro_utils import show_admin_menu, send_broadcast_message
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helpers.utils import *
from helpers.keyboard import *
from helpers.db import users, banned_users
from helpers.state import state_manager
from pyrogram import Client
from pyrogram.types import Message
from helpers.bot_filters import is_admin
admin_state = {
    
}




@Client.on_message(is_admin & filters.regex("🔙 بازگشت") & filters.private)
async def handle_admin_messages_back(c, m):
    await show_admin_menu(c, m)
    users.update(m.from_user.id, "state", None)

@Client.on_message(is_admin & filters.command(['start']) & filters.private)
async def handle_admin_messages(c, m):
    await show_admin_menu(c, m)

@Client.on_message(is_admin & filters.command(['ban']) & filters.private)
async def handle_ban_command(c, m):
    text = m.text
    if len(text.split()) > 1:
        user_id = text.split()[1]
        if not user_id.isdigit():
            await m.reply("user-id must be integers (0,1,...,9)")
            return
        if not users.user_exists(int(user_id)):
            await m.reply("user with this user-id doesn't exist in bot users!")
            return


        if int(user_id) in [x["user_id"] for x in banned_users.get_all_banned_users()]:   
            await m.reply("user is already banned!")
            return

        banned_users.add(int(user_id))
        lst = ""
        all_banned = banned_users.get_all_banned_users()
        if  all_banned==[]:
            lst = "no banned users" 
        else:    
            lst = "\n".join([str(x['user_id']) for x in all_banned]) 
        await m.reply(f"user with id {user_id} won't be able to use the bot till you /unban him!\n\nlist of banned users: {lst}\n")
        return

    await m.reply("ban usage:\n/ban <user_id>")    

@Client.on_message(is_admin & filters.command(['unban']) & filters.private)
async def handle_unban_command(c, m):
    text = m.text
    if len(text.split()) > 1:
        user_id = text.split()[1]
        if not user_id.isdigit():
            await m.reply("user-id must be integers (0,1,...,9)")
            return
        if not users.user_exists(int(user_id)):
            await m.reply("user with this user-id doesn't exist in bot users!")
            return

        
        if int(user_id)  not in [x["user_id"] for x in banned_users.get_all_banned_users()]:
            await m.reply("user is not banned!")
            return
        else:
            banned_users.remove(int(user_id))
            await m.reply(f"user with id {user_id} is now able to use the bot!")
            return
        
    await m.reply("unban usage:\n/unban <user_id>")    

@Client.on_message(is_admin & filters.text & filters.regex("دریافت لیست کاربران 🖨") & filters.private)
async def get_users_handler(client: Client, message: Message):
    await send_users(client, message.from_user.id)

@Client.on_message(is_admin & filters.text & filters.regex("ارسال همگانی 📲"))
async def broadcast_handler(client: Client, message: Message):
    await message.reply("پیام خود را برای ارسال همگانی ارسال کنید :", reply_markup=home_kb)
    await state_manager.set("broadcast",message)



@Client.on_message(is_admin & filters.text & filters.command(['sendgp']) & filters.private)
async def send_user_direct_gp(client: Client, message: Message):
    global admin_state
    message_text = message.text
    user_id = message.from_user.id
    
    # Initialize admin state with comprehensive details
    admin_state[user_id] = {
        "state": "sending-gp-dm",
        "step": "sending the message",
        "message_id": "",
    }
    
    # Rich, descriptive message with clear instructions
    await message.reply(
        "🚀 *پخش همگانی پیام* 📨\n\n"
        "مرحله ۱: آماده‌سازی پیام\n\n"
        "📝 لطفاً پیامی که می‌خواهید به کاربران منتخب ارسال کنید، آماده کنید.\n\n"
        "✅ نوع محتوای مجاز:\n"
        "• متن ✉️\n"
        "• صوت 🎙\n"
        "• ویدیو 🎥\n"
        "• سند و فایل 📄\n\n"
        "⚠️ توجه: پیام خود را در همین چت ارسال کنید.\n"
        "🕒 زمان: پیام باید ظرف ۵ دقیقه ارسال شود.", 
        quote=True
    )



@Client.on_message(is_admin & filters.text & filters.command(['send']) & filters.private )
async def send_user_direct(client: Client, message: Message):
    message_text = message.text
    if len(message_text.split(" "))>1 and message.reply_to_message:
        message_to_forward =message.reply_to_message.id
        target_user = message_text.split(" ")[1]
        if not target_user.isdigit():
            await message.reply("user id should only contain numbers")
            return
        
        try:
            await client.forward_messages(
                from_chat_id = message.from_user.id ,
                chat_id = target_user ,
                message_ids  = int(message_to_forward)
            )
            await message.reply("message sent ")
        except Exception as e :
            await message.reply(text = f"failed to send message to {target_user}\nerror : {e}")    
        
        
    
    
    else:
        await message.reply(
            "usage :reply on target message and type query :\n /send user_id \n example : /send 23232323"
        )
        return






@Client.on_message(is_admin & broadcasting & filters.private )
async def broadcast_handler_step(client: Client, message: Message):
    print("broadcasting ...")
    await send_broadcast_message(client, message)
    await state_manager.reset(message)
    

@Client.on_message(is_admin & filters.command(['up']) & filters.private )
async def updarede_stats(client: Client, message: Message):
    message_text = message.text
    if len(message_text.split(" "))<4:
        await message.reply("""
usage:
/up user-id new-success new-failed                            
                            """)
        return 
    user_to_upgrase = int(message_text.split(" ")[1])
    new_success = int(message_text.split(" ")[2])
    new_failed = int(message_text.split(" ")[3])
    users.update(user_to_upgrase,"successfull_transactions",new_success)
    
    users.update(user_to_upgrase,"failed_transactions",new_failed)
    
    user_data = users.get(user_to_upgrase)['telegram_first_name']
    await message.reply(
        f"user {user_data} new stats > sucess : {new_success} | failed : {new_failed}"
    )
    

@Client.on_message(is_admin & filters.command(['delete']) & filters.private)
async def delete_user_command(c, m): 
    user_id = int(m.text.split(" ")[1])
    try:
        users.delete(user_id = user_id)  
        await m.reply(f"user {user_id} deleted !")
    except Exception as e :
        await m.reply(f"failed to delete user {user_id} > {e}")     
        
        
        
@Client.on_message(is_admin & filters.command(['reqs']) & filters.private)
async def handle_admin_messages_check_user_reqs(c, m):  
    message_text = m.text
    if len(message_text.split())==0:
        return
    
    user_id = int(message_text.split(" ")[1])
    message = m
    try:
        user_requests = requests.get_all_user_requests(user_id)
        if user_requests==[]:
            await message.reply(quote=True,text="شما هنوز هیچ درخواستی ثبت نکرده اید !")
            return
        requests1, total_pages = paginate_requests(user_requests, 1)
        keyboard = generate_inline_keyboard(requests1, 1, total_pages)
        await message.reply("درخواست های شما به شرح زیر هست\nبرای ادامه یکی از گزینه های زیر رو انتخاب کنید :",
                            reply_markup=keyboard)
    except Exception as e :
         await message.reply(quote=True,text="شما هنوز هیچ درخواستی ثبت نکرده اید !")
         pass  

@Client.on_message(is_admin & filters.command(['charge']) & filters.private)
async def handle_charge_wallet(client: Client, message: Message):
    message_text = message.text
    if len(message_text.split()) != 3:
        await message.reply("""
Usage:
/charge <user_id> <amount>
Example: /charge 2423 10
        """)
        return 
    
    try:
        user_id = int(message_text.split()[1])
        amount = float(message_text.split()[2])
        
        if not users.user_exists(user_id):
            await message.reply(f"User with ID {user_id} does not exist!")
            return
        
        user_data = users.get(user_id)
        current_wallet = user_data.get('wallet', 0)
        new_wallet_balance = current_wallet + amount
        
        users.update(user_id, "wallet", new_wallet_balance)
        
        await message.reply(
            f"💰 Wallet Charged Successfully!\n"
            f"User ID: {user_id}\n"
            f"Added Amount: {amount}\n"
            f"New Balance: {new_wallet_balance}"
        )
    except ValueError:
        await message.reply("Invalid input. User ID and amount must be numbers.")
    except Exception as e:
        await message.reply(f"Error charging wallet: {e}")

@Client.on_message(is_admin & filters.command(['get']) & filters.private)
async def handle_get_user_info(client: Client, message: Message):
    message_text = message.text
    if len(message_text.split()) != 2:
        await message.reply("""
Usage:
/get <user_id>
Example: /get 2423
        """)
        return 
    
    try:
        user_id = int(message_text.split()[1])
        
        if not users.user_exists(user_id):
            await message.reply(f"User with ID {user_id} does not exist!")
            return
        
        user_data = users.get(user_id)
        
        # Prepare user information string
        user_info = f"""🧑 User Information for ID {user_id}:

📱 Name: {user_data.get('telegram_first_name', 'N/A')} {user_data.get('telegram_last_name', '')}
🆔 Username: {user_data.get('username', 'N/A')}
📞 Phone Number: {user_data.get('phone_number', 'N/A')}
🌍 Country: {user_data.get('country', 'N/A')}

💰 Wallet Balance: {user_data.get('wallet', 0):.2f}
📊 Successful Transactions: {user_data.get('successfull_transactions', 0)}
❌ Failed Transactions: {user_data.get('failed_transactions', 0)}

📅 Joined Date: {user_data.get('joined_date', 'N/A')}
👥 Invited By: {user_data.get('invited_by', 'N/A')}
🔗 Referrals: {user_data.get('refrals', 'None')}"""
        
        await message.reply(user_info)
    
    except ValueError:
        await message.reply("Invalid user ID. Must be a number.")
    except Exception as e:
        await message.reply(f"Error retrieving user information: {e}")
            
@Client.on_message(is_admin & filters.command(['report']) & filters.private)
async def get_daily_euro_report(client: Client, message: Message):        
    await message.reply(
        text = generate_euro_daily_report()
    )    
     
     
@Client.on_message(is_admin & filters.command(['bids']) & filters.private)
async def handle_admin_messages_check_user_bids(c, m):  
    message_text = m.text
    if len(message_text.split())==0:
        return
    
    user_id = int(message_text.split(" ")[1])
    message = m   
    try:
        user_bids = bids.get_all_user_bids(user_id)
        if user_bids==[]:
                    await message.reply(quote=True,text="شما هنوز هیچ پیشنهادی ثبت نکرده اید !")
                    return
        bids1, total_pages = paginate_bids(user_bids, 1)
        keyboard = generate_bids_inline_keyboard(bids1, 1, total_pages)
        await message.reply("پیشنهادهای  شما به شرح زیر هست\nبرای ادامه یکی از گزینه های زیر رو انتخاب کنید :", reply_markup=keyboard)
    except Exception as e :
        await message.reply(quote=True,text="شما هنوز هیچ پیشنهادی ثبت نکرده اید !")       
        


@Client.on_message(is_admin & filters.command(['getreq']))
async def handle_get_request_info(client: Client, message: Message):
    print("getting req")
    message_text = message.text
    if len(message_text.split()) != 2:
        await message.reply("""
Usage:
/getreq <request_id>
Example: /getreq 123
        """)
        return
    
    try:
        request_id = int(message_text.split()[1])
        
        request_data = requests.get(request_id)
        post_id = str(requests.get(request_id)['post_id'])
        link = f'[لینک حواله]({group_link}/{post_id})'
        if not request_data:
            await message.reply(f"Request with ID {request_id} does not exist!")
            return
        
        # Get bids for the request
        bids_for_request = bids.get_related_bid_with_request_id(request_id)
        
        # Prepare request information string
        request_info = f"""
📝 Request Information for ID {request_id}:

👤 User ID: {request_data.get('user_id', 'N/A')}
 currency: {request_data.get('currency', 'N/A')}
💰 Amount: {request_data.get('amount', 'N/A')}
💳 Payment Method: {request_data.get('payment_method', 'N/A')}
🔄 Exchange Type: {request_data.get('exchange_type', 'N/A')}
💲 Price: {request_data.get('price', 'N/A')}
💬 Description: {request_data.get('description', 'N/A')}
  Status: {request_data.get('status', 'N/A')}
📅 Created Date: {request_data.get('created_date', 'N/A')}



Bids:"""
        
        if bids_for_request:
            for bid in bids_for_request:
                bidder_data = users.get(bid['user_id'])
                if bidder_data:
                    request_info += f"""
   Bid ID: {bid.get('bid_id', 'N/A')}
   Bidder Name: {bidder_data.get('telegram_first_name', 'N/A')} {bidder_data.get('telegram_last_name', '')}
   Bid Price: {bid.get('price', 'N/A')}
   Bid Date: {bid.get('date', 'N/A')}"""
                else:
                    request_info += f"""
   Bid ID: {bid.get('bid_id', 'N/A')}
   Bidder Name: User Not Found
   Bid Price: {bid.get('price', 'N/A')}
   Bid Date: {bid.get('date', 'N/A')}"""
        else:
            request_info += "\n No bids found for this request."
        
        await message.reply(request_info+"\n\n"+link)
    
    except ValueError:
        await message.reply("Invalid request ID. Must be a number.")
    except Exception as e:
        await message.reply(f"Error retrieving request information: {e}")

@Client.on_message(is_admin & filters.command(["help", "commands"]) & filters.private)
async def command_guide_handler(client: Client, message: Message):
    guide_text = """📖 **راهنمای دستورات**\n
📌 **/start**
💬 نمایش منوی مدیریت.
📚 نحوه استفاده:
`/start`

📌 **/ban**
💬 🚫 مسدود کردن یک کاربر در ربات.
📚 نحوه استفاده:
`/ban <user_id>`
مثال: `/ban 123456`

📌 **/unban**
💬 ✅ رفع مسدودیت یک کاربر.
📚 نحوه استفاده:
`/unban <user_id>`
مثال: `/unban 123456`

📌 **/get**
💬 🔍 دریافت اطلاعات کامل یک کاربر.
📚 نحوه استفاده:
`/get <user_id>`
مثال: `/get 123456`

📌 **/charge**
💬 💰 شارژ کیف پول یک کاربر.
📚 نحوه استفاده:
`/charge <user_id> <amount>`
مثال: `/charge 123456 10`

📌 **/send**
💬 ✉️ ارسال پیام مستقیم به کاربر.
📚 نحوه استفاده:
`/send <user_id>`
روی پیام موردنظر ریپلای کنید و تایپ کنید:
مثال: `/send 123456`

📌 **/sendgp**
💬 📨 ارسال پیام گروهی به شناسه‌های کاربری مشخص.
📚 نحوه استفاده:
`/sendgp`

📌 **/up**
💬 📊 بروزرسانی آمار تراکنش‌های کاربر (موفق و ناموفق).
📚 نحوه استفاده:
`/up <user_id> <new_success> <new_failed>`
مثال: `/up 123456 10 2`

📌 **/delete**
💬 🗑️ حذف کاربر از پایگاه داده ربات.
📚 نحوه استفاده:
`/delete <user_id>`
مثال: `/delete 123456`

📌 **/reqs**
💬 📝 دریافت تمام درخواست‌های ارسال شده توسط کاربر.
📚 نحوه استفاده:
`/reqs <user_id>`
مثال: `/reqs 123456`

📌 **/bids**
💬 📈 دریافت تمام پیشنهادات ثبت شده توسط کاربر.
📚 نحوه استفاده:
`/bids <user_id>`
مثال: `/bids 123456`

📌 **/report**
💬 📄 تولید گزارش روزانه تراکنش‌های یورو.
📚 نحوه استفاده:
`/report`
"""
    print("Sending")
    await message.reply(guide_text)

    guide_text = """📖 **راهنمای دستورات**\n
📌 **/start**
💬 نمایش منوی مدیریت.
📚 نحوه استفاده:
`/start`

📌 **/ban**
💬 🚫 مسدود کردن یک کاربر در ربات.
📚 نحوه استفاده:
`/ban <user_id>`
مثال: `/ban 123456`

📌 **/unban**
💬 ✅ رفع مسدودیت یک کاربر.
📚 نحوه استفاده:
`/unban <user_id>`
مثال: `/unban 123456`

📌 **/get**
💬 🔍 دریافت اطلاعات کامل یک کاربر.
📚 نحوه استفاده:
`/get <user_id>`
مثال: `/get 123456`

📌 **/charge**
💬 💰 شارژ کیف پول یک کاربر.
📚 نحوه استفاده:
`/charge <user_id> <amount>`
مثال: `/charge 123456 10`

📌 **/send**
💬 ✉️ ارسال پیام مستقیم به کاربر.
📚 نحوه استفاده:
`/send <user_id>`
روی پیام موردنظر ریپلای کنید و تایپ کنید:
مثال: `/send 123456`

📌 **/sendgp**
💬 📨 ارسال پیام گروهی به شناسه‌های کاربری مشخص.
📚 نحوه استفاده:
`/sendgp`

📌 **/up**
💬 📊 بروزرسانی آمار تراکنش‌های کاربر (موفق و ناموفق).
📚 نحوه استفاده:
`/up <user_id> <new_success> <new_failed>`
مثال: `/up 123456 10 2`

📌 **/delete**
💬 🗑️ حذف کاربر از پایگاه داده ربات.
📚 نحوه استفاده:
`/delete <user_id>`
مثال: `/delete 123456`

📌 **/reqs**
💬 📝 دریافت تمام درخواست‌های ارسال شده توسط کاربر.
📚 نحوه استفاده:
`/reqs <user_id>`
مثال: `/reqs 123456`

📌 **/bids**
💬 📈 دریافت تمام پیشنهادات ثبت شده توسط کاربر.
📚 نحوه استفاده:
`/bids <user_id>`
مثال: `/bids 123456`

📌 **/report**
💬 📄 تولید گزارش روزانه تراکنش‌های یورو.
📚 نحوه استفاده:
`/report`
"""
    print("Sending")
    await message.reply(guide_text)
@Client.on_message(is_admin & filters.regex("راهنمای دستورات") & filters.private)
async def command_guide_handler_buton(client: Client, message: Message):
    guide_text = "📖 **راهنمای دستورات**\n\n"

    # Debugging: Print COMMANDS list
    print("COMMANDS List:", COMMANDS)

    # Generate command guide
    for cmd in COMMANDS:
        print("Processing command:", cmd)  # Debugging each command
        commands = ", ".join([f"/{c}" for c in cmd["command"]])
        guide_text += f"📌 **{commands}**\n"
        guide_text += f"💬 {cmd['description']}\n"
        guide_text += f"📚 نحوه استفاده:\n`{cmd['usage']}`\n\n"

    # Debugging: Print the final guide text
    print("Generated Guide Text:", guide_text)

    # Send the guide as a reply
    await message.reply(guide_text)




@Client.on_message(is_admin & filters.command(['set']) & filters.private)
async def handle_set_request_bid(client: Client, message: Message):
    message_text = message.text
    parts = message_text.split()
    if len(parts) != 3:
        await message.reply("⚠️ استفاده: `/set <شناسه_درخواست> <شناسه_پیشنهاد>`")
        return

    try:
        request_id = int(parts[1])
        bid_id = int(parts[2])
    except ValueError:
        await message.reply("❌ `شناسه_درخواست` و `شناسه_پیشنهاد` باید اعداد صحیح باشند.")
        return
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("تایید پیشنهاد", callback_data=f"confirm-bid:{bid_id}"),
                InlineKeyboardButton("رد کردن پیشنهاد", callback_data=f"reject-bid:{bid_id}"),
            ]
        ]
    )

    await message.reply(
        f"❓ آیا می‌خواهید شناسه درخواست: {request_id} را با شناسه پیشنهاد: {bid_id} تایید کنید؟",
        reply_markup=keyboard
    )




@Client.on_message(is_admin & filters.private)
async def handle_admin_messages_raw(client: Client, message: Message):
    global admin_state
    user_id = message.from_user.id
    if user_id not in admin_state:
        return
    
    admin_current_state = admin_state[user_id]
    print(admin_current_state)
    
    if admin_current_state['state'] == 'sending-gp-dm':
        if admin_current_state['step'] == 'sending the message':
            admin_state[user_id]['message_id'] = message.id
            await message.reply(
                "📝 مرحله ۲: ارسال شناسه‌های کاربری برای پخش همگانی 📋\n\n"
                "لطفاً فهرست شناسه‌های کاربرانی که می‌خواهید پیام را به آنها ارسال کنید را وارد کنید. "
                "شناسه‌ها را با علامت ویرگول (,) از هم جدا کنید\n\n"
                "12121121,4242424,353542424", 
                quote=True
            )
            admin_state[user_id]['step'] = 'sending selected users'
        
        elif admin_current_state['step'] == 'sending selected users':
            list_of_selected_users = [int(x.strip()) for x in message.text.split(",")]
            progress_message = await message.reply(
                "🚀 در حال پخش پیام...\n"
                "⏳ در حال ارسال پیام به کاربران انتخاب شده...", 
                quote=True
            )
            
            failed = 0
            sent = 0          
            print(list_of_selected_users)   
            
            for item in list_of_selected_users:
                try:
                    await client.forward_messages(
                        from_chat_id=message.from_user.id,
                        chat_id=item,
                        message_ids=int(admin_state[user_id]['message_id'])
                    )
                    sent += 1
                except Exception as e:
                    print(e)
                    failed += 1  
                
                # Update progress periodically
                await progress_message.edit_text(
                    text=f"📊 پیشرفت پخش:\n"
                         f"✅ ارسال شده: {sent}\n"
                         f"❌ ناموفق: {failed}\n"
                         f"📨 کل کاربران: {len(list_of_selected_users)}"
                ) 
            
            # Final broadcast result
            await progress_message.edit_text(
                text=f"🎉 پخش همگانی تکمیل شد! 🏁\n\n"
                     f"📊 نتایج:\n"
                     f"✅ ارسال موفق: {sent}\n"
                     f"❌ ارسال ناموفق: {failed}\n"
                     f"📈 درصد موفقیت: {(sent/len(list_of_selected_users))*100:.2f}%"
            )



# Command Guide Data
COMMANDS = [
    {
        "command": ["start"],
        "description": "نمایش منوی مدیریت.",
        "usage": "/start"
    },
    {
        "command": ["ban"],
        "description": "🚫 مسدود کردن یک کاربر در ربات.",
        "usage": "/ban <user_id>\nمثال: /ban 123456"
    },
    {
        "command": ["unban"],
        "description": "✅ رفع مسدودیت یک کاربر.",
        "usage": "/unban <user_id>\nمثال: /unban 123456"
    },
    {
        "command": ["get"],
        "description": "🔍 دریافت اطلاعات کامل یک کاربر.",
        "usage": "/get <user_id>\nمثال: /get 123456"
    },
    {
        "command": ["charge"],
        "description": "💰 شارژ کیف پول یک کاربر.",
        "usage": "/charge <user_id> <amount>\nمثال: /charge 123456 10"
    },
    {
        "command": ["send"],
        "description": "✉️ ارسال پیام مستقیم به کاربر.",
        "usage": "/send <user_id>\nروی پیام موردنظر ریپلای کنید و تایپ کنید:\nمثال: /send 123456"
    },
    {
        "command": ["sendgp"],
        "description": "📨 ارسال پیام گروهی به شناسه‌های کاربری مشخص.",
        "usage": "/sendgp"
    },
    {
        "command": ["up"],
        "description": "📊 بروزرسانی آمار تراکنش‌های کاربر (موفق و ناموفق).",
        "usage": "/up <user_id> <new_success> <new_failed>\nمثال: /up 123456 10 2"
    },
    {
        "command": ["delete"],
        "description": "🗑️ حذف کاربر از پایگاه داده ربات.",
        "usage": "/delete <user_id>\nمثال: /delete 123456"
    },
    {
        "command": ["reqs"],
        "description": "📝 دریافت تمام درخواست‌های ارسال شده توسط کاربر.",
        "usage": "/reqs <user_id>\nمثال: /reqs 123456"
    },
    {
        "command": ["bids"],
        "description": "📈 دریافت تمام پیشنهادات ثبت شده توسط کاربر.",
        "usage": "/bids <user_id>\nمثال: /bids 123456"
    },
    {
        "command": ["report"],
        "description": "📄 تولید گزارش روزانه تراکنش‌های یورو.",
        "usage": "/report"
    },
    {
        "command": ["delete"],
        "description": "🗑️ حذف یک کاربر با شناسه.",
        "usage": "/delete <user_id>\nمثال: /delete 123456"
    },
    {
         "command": ["set"],
        "description": "تایید یک پیشنهاد برای یک درخواست",
        "usage": "/set <request_id> <bid_id>"
    },
]

# Command Guide Handler
from pyrogram import Client
from pyrogram.types import Message
from helpers.bot_filters import is_admin

# Command Guide Data
COMMANDS = [
    {
        "command": ["start"],
        "description": "نمایش منوی مدیریت.",
        "usage": "/start"
    },
    {
        "command": ["ban"],
        "description": "🚫 مسدود کردن یک کاربر در ربات.",
        "usage": "/ban <user_id>\nمثال: /ban 123456"
    },
    {
        "command": ["unban"],
        "description": "✅ رفع مسدودیت یک کاربر.",
        "usage": "/unban <user_id>\nمثال: /unban 123456"
    },
    {
        "command": ["get"],
        "description": "🔍 دریافت اطلاعات کامل یک کاربر.",
        "usage": "/get <user_id>\nمثال: /get 123456"
    },
    {
        "command": ["charge"],
        "description": "💰 شارژ کیف پول یک کاربر.",
        "usage": "/charge <user_id> <amount>\nمثال: /charge 123456 10"
    },
    {
        "command": ["send"],
        "description": "✉️ ارسال پیام مستقیم به کاربر.",
        "usage": "/send <user_id>\nروی پیام موردنظر ریپلای کنید و تایپ کنید:\nمثال: /send 123456"
    },
    {
        "command": ["sendgp"],
        "description": "📨 ارسال پیام گروهی به شناسه‌های کاربری مشخص.",
        "usage": "/sendgp"
    },
    {
        "command": ["up"],
        "description": "📊 بروزرسانی آمار تراکنش‌های کاربر (موفق و ناموفق).",
        "usage": "/up <user_id> <new_success> <new_failed>\nمثال: /up 123456 10 2"
    },
    {
        "command": ["delete"],
        "description": "🗑️ حذف کاربر از پایگاه داده ربات."}
]
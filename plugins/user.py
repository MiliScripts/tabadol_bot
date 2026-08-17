from helpers.bot_filters import *
from helpers.pyro_utils import *
from pyrogram.types import Message
from pyrogram import filters , Client 
from helpers.keyboard import *
from helpers.state import state_manager
from helpers.db import *
from configs.config import *
from pyrogram.errors import UserNotParticipant


# @Client.on_message(not_memeber & filters.private)
# async def handle_guest(c,m):
#     await send_guest_membersip_alert(m)





temp_user_states = {
    
}

@Client.on_message(is_banned & filters.private)
@is_added
async def handle_banned(c,m):
    await m.reply("دسترسی شما به ربات محدود شده و امکان استفاده از ربات رو ندارید برای دسترسی به پشتیبانی ربات پیام بدین !")

@Client.on_message(filters.regex("انصراف") & not_banned & filters.private)
@is_added
async def user_cancel_handler(c,m):
        await state_manager.delete(m)
        await show_user_menu(c,m)


@Client.on_message(filters.regex("🔙 بازگشت")& not_banned & filters.private)
@is_added
async def user_back_handler(c,m):
    await state_manager.reset(m)
    await show_user_menu(c,m)


@Client.on_message(filters.command(['start'])& not_banned & filters.private)
async def handle_user_start_paramed_message(c:Client,m:Message):
    message = m
    message_text = m.text
    user_id = m.from_user.id
    if message_text=='/start':
        users.add(user_id=user_id
                         ,first_name =message.from_user.first_name,
                         last_name=message.from_user.last_name
                         ,username = message.from_user.username)
        await state_manager.reset(m)
        
        await show_user_menu(c,m)
        return
    else:
        if " " in message_text:
            if "_" in message.text.split(" ")[1] :
                # handling refrals
                if message.text.split(" ")[1].split("_")[0]=='Refral':
                    print("link refral start detected")
                    try:
                        holder_user = int(message.text.split(" ")[1].split("_")[1])
                        print("holder user is : ",holder_user)
                        
                        user_to_add_as_refral = message.from_user.id
                        print("user to add as refral is : ",user_to_add_as_refral)
                        holder_users_refrals = users.get(holder_user)['refrals']
                        print("refrals : ",holder_users_refrals)
                        
                        print("holder user refrals are : ",holder_users_refrals)
                        if str(user_to_add_as_refral) not in holder_users_refrals.split(".") and not users.user_exists(user_id=user_to_add_as_refral) and user_to_add_as_refral!=holder_user:

                            a = holder_users_refrals+"."+str(user_to_add_as_refral) if holder_users_refrals!="" else holder_users_refrals+str(user_to_add_as_refral)
                            users.add(user_id=user_id
                            ,first_name =message.from_user.first_name,
                            last_name=message.from_user.last_name
                            ,username = message.from_user.username)
                            print(a)
                            users.update(holder_user,"refrals",a)
                            users.update(user_to_add_as_refral,"invited_by",holder_user)
                            print(f'[!] user {user_to_add_as_refral}  added to {holder_user} refrals')
                            await c.send_message(chat_id=int(holder_user),text = f"💠 کاربر {m.from_user.mention} با لینک رفرال  شما عضو  مجموعه شد")
                            await show_user_menu(c,m)
                            return
                        else:
                            await show_user_menu(c,m)
                            return
                    except Exception as e :
                        print(e)
                        await show_user_menu(c,m)
                        return




                elif message.text.split(" ")[1].split("_")[0]=='feedback':
                    request_id = int(message.text.split(" ")[1].split("_")[1])
                    print(request_id)
                    print(message.text)
                    temp_user_states[m.from_user.id] = {
                        "request_id" : request_id ,
                        "text" : "",
                        "stars" : 0
                    }
                    
                    try:
                        
                        request = requests.get(request_id)
                        if not request:
                            await message.reply("⚠️ متاسفانه شناسه درخواستی که وارد کردید یافت نشد.")
                            return

                        is_creator = request['user_id'] == message.from_user.id
                        related_bids = bids.get_related_bid_with_request_id(request_id)
                        
                        is_bidder = False
                        for bid in related_bids:
                            if bid['user_id'] == message.from_user.id:
                                is_bidder = True
                                break
                        
                        if not (is_creator or is_bidder):
                            await message.reply("⛔️ شما نه ایجاد کننده این درخواست هستید و نه پیشنهادی برای آن ثبت کرده‌اید.")
                            return

                        if message.from_user.id not in temp_user_states:
                            temp_user_states[message.from_user.id] = {}
                        temp_user_states[message.from_user.id]['request_id'] = request_id
                        
                        stars_kb = InlineKeyboard(row_width=1)
                        stars_lst = []
                        stars_lst.append(InlineButton("⭐", callback_data="feedback_star_1"))
                        stars_lst.append(InlineButton("⭐⭐", callback_data="feedback_star_2"))
                        stars_lst.append(InlineButton("⭐⭐⭐", callback_data="feedback_star_3"))
                        stars_lst.append(InlineButton("⭐⭐⭐⭐", callback_data="feedback_star_4"))
                        stars_lst.append(InlineButton("⭐⭐⭐⭐⭐", callback_data="feedback_star_5"))
                        stars_lst.append(InlineButton("❌ انصراف", callback_data="feedback_cancel"))
                        stars_kb.add(*stars_lst)

                        await message.reply("🌟 لطفا امتیاز خود را انتخاب کنید:", reply_markup=stars_kb)
                        await state_manager.set("feedback_stars", message)
                        return


                    except Exception as e:
                        print(f"Error in handle_feedback_request_id: {e}")
                        await message.reply("😕 متاسفانه مشکلی پیش آمده است. لطفا دوباره تلاش کنید.")
                        return
                    
                    
                    
                    

            check= await confirm_user_susbscription(message.from_user.id,c)
            if not check :
                return
            check= await user_has_unfilled_field(c,m)
            if check :
                await m.reply('''⚠️ برای ادامه لطفا اطلاعات پروفایل خود را کامل کنید 

        💬 نام و نام خانوادگی خودتون رو وارد کنید''',reply_markup=home_kb)
                await state_manager.set("name",m)
                return 
            
            await   handle_user_bid(c,m)




@Client.on_message(filters.text & filters.regex("رفرال")& not_banned & filters.private)
@is_added
async def refral(client: Client, message: Message):
    m = message
    c = client
    user_id = m.from_user.id
    print("refral view is called !")

    # checkinf if user's profile is completed
    # yes > get link and information
    # no  > ask for profile completeation
    check= await user_has_unfilled_field(c,m)
    print(check)
    if check :
        await m.reply('''⚠️ برای ادامه لطفا اطلاعات پروفایل خود را کامل کنید 

💬 نام و نام خانوادگی خودتون رو وارد کنید''',reply_markup=home_kb)
        await state_manager.set("name",m)
        return 

    # sending more details about refral 
    # sending user special link
    # showing user refral users    



    refreal_intro_text = '''🚹 کاربر محترم درصورتیکه دوستان خود را با لینک زیر به ربات دعوت کنید

🚻 به ازای هر معامله از فردی که با لینک شما وارد ربات شده است و ربات رو استارت کرده است نیم درصد از کل هزینه معامله  به کیف پول شما اضافه خواهد شد

💠 در نهایت با ارتباط با پشتیبانی قادر به تسویه کیف پول خود خواهید بود'''
    user_refral_link = f'''لینک اشتراک شما : 

https://t.me/{bot_id.replace("@","")}?start=Refral_{user_id}'''
    await m.reply(refreal_intro_text)
    await m.reply(user_refral_link,reply_markup=home_kb)
    print("user refral link sent ")


@Client.on_message(filters.text & filters.regex("⭐️  لیست گروه های مجموعه  ⭐️")& not_banned & filters.private)
@is_added
async def get_groups_list(client: Client, message: Message):
    await message.reply(
        text= 'لیست گروه های مجموعه \nبرای ورود در هر گروه روی عنوان گروه کلیک کنید .',
        reply_markup = group_list()
    )
    
    
    
    
    
@Client.on_message(filters.text & filters.regex("➕ ایجاد درخواست جدید")& not_banned & filters.private)
@is_added
async def create_request_handler(client: Client, message: Message):
    check= await user_has_unfilled_field(client,message)
    if check :
        await message.reply('''هنوز احراز هویت خودتون رو کامل نکردید توجه کنید که برای ثبت هرگونه درخواست یا پیشنهاد باید مرحله‌ی اول احراز هویت رو تکمیل کنید.

💬 نام و نام خانوادگی خودتون رو وارد کنید''',reply_markup=home_kb)
        await state_manager.set("name",message)
        return 


    check= await confirm_user_susbscription(message.from_user.id,client)
    if not check :
        return

    await message.reply(quote=True,text='''⁉️ قصد خرید یا فروش کدام یک از ارز های زیر را دارید؟


🟢 در حال حاضر خرید و فروش ارزهای زیر امکان پذیر می باشد.

🔴 در صورتی که ارز مورد نظر شما در لیست وجود ندارد می توانید به ادمین اطلاع دهید تا درصورت لزوم به لیست اضافه گردد.''',
reply_markup=currency_kb()) 
    await state_manager.set("currency",message)

@Client.on_message(filters.text & filters.regex("📤 درخواست های من")& not_banned)
@is_added
async def my_requests_handler(client: Client, message: Message):
    try:
        user_requests = requests.get_all_user_requests(message.from_user.id)
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

@Client.on_message(filters.text & filters.regex("📨 پیشنهادات ارسالی من")& not_banned & filters.private)
@is_added
async def my_proposals_handler(client: Client, message: Message):
    try:
        user_bids = bids.get_all_user_bids(message.from_user.id)
        if user_bids==[]:
                    await message.reply(quote=True,text="شما هنوز هیچ پیشنهادی ثبت نکرده اید !")
                    return
        bids1, total_pages = paginate_bids(user_bids, 1)
        keyboard = generate_bids_inline_keyboard(bids1, 1, total_pages)
        await message.reply("پیشنهادهای  شما به شرح زیر هست\nبرای ادامه یکی از گزینه های زیر رو انتخاب کنید :", reply_markup=keyboard)
    except Exception as e :
        await message.reply(quote=True,text="شما هنوز هیچ پیشنهادی ثبت نکرده اید !")

@Client.on_message(filters.text & filters.regex("🔎 جستجو")& not_banned)
@is_added
async def search_handler(client: Client, message: Message):
    await message.reply(quote=True,text='ارز مورد نظر را برای جستجو انتخاب کنید :',reply_markup=currency_kb())
    await state_manager.set('select=serach=currency',message)


@Client.on_message(filters.text & filters.regex("⭐️ پشتیبانی") & filters.private)
@is_added
async def support_handler(client: Client, message: Message):
    sup_kb = InlineKeyboard()
    sup_kb.add(
         InlineButton("ورود به پشتیبانی",url=support_chat_link)
    )
    await message.reply("👥 درصورت نیاز به راهنمایی یا پشتیبانی روی دکمه زیر کلیک کنید",reply_markup=sup_kb)

@Client.on_message(filters.text & filters.regex("📕 پروفایل") & filters.private)
@is_added
async def profile_handler(client: Client, message: Message):
    await show_profile(message)

@Client.on_message(filters.text & filters.regex("⁉️ درباره ما")& not_banned & filters.private)
@is_added
async def about_us(client: Client, message: Message):
    await handle_about_us(message)




@Client.on_message(filters.text & filters.regex("🗣️ ارسال بازخورد") & filters.private)
@is_added
async def feedback_handler(client: Client, message: Message):
    text = "کاربر محترم لطفاً برای ثبت بازخوردتان شناسه حواله مورد نظرتون رو ارسال کنید  :\n[نمونه](https://cool-violet-6bc8.milaadfarzian.workers.dev/download/BQACAgQAAxkDAAMWZ89zFMTHXHy8IUlzC_9lrzejHpQAAlkgAAK80XhS2idGWsYWrmU2BA/documents/file_39.jpg)"
    await message.reply(text, quote=True,reply_markup=cance_kb)
    await state_manager.set("feedback_request_id", message)
    temp_user_states[message.from_user.id] = {
        "request_id" : None ,
        "text" : "",
        "stars" : 0
    }
    






 
@Client.on_message(is_filling_profile & filters.private)
@is_added
async def handle_user_information(client: Client, message: Message):
    s = await state_manager.get(message)
    print(s)
    await handle_filing_form(message)
@Client.on_message(is_feedback_text & filters.private)
@is_added
async def handle_feedback_text(client: Client, message: Message):
    user_id = message.from_user.id
    try:
        print(temp_user_states[user_id])
        feedback_text = message.text
        request_id = temp_user_states[user_id]['request_id']
        stars = temp_user_states[user_id].get('stars')
        user = users.get(user_id)
        username = user.get("username")
        name = user.get("name")
        request = requests.get(request_id)
        post_id = request.get("post_id")
        
        
        
        
        
        from jdatetime import datetime

        day_mapping = {
            "Saturday": "شنبه",
            "Sunday": "یکشنبه",
            "Monday": "دوشنبه",
            "Tuesday": "سه شنبه",
            "Wednesday": "چهارشنبه",
            "Thursday": "پنجشنبه",
            "Friday": "جمعه",
        }

        month_mapping = {
            "Farvardin": "فروردین",
            "Ordibehesht": "اردیبهشت",
            "Khordad": "خرداد",
            "Tir": "تیر",
            "Mordad": "مرداد",
            "Shahrivar": "شهریور",
            "Mehr": "مهر",
            "Aban": "آبان",
            "Azar": "آذر",
            "Dey": "دی",
            "Bahman": "بهمن",
            "Esfand": "اسفند",
        }

        today = datetime.now()
        persian_day = day_mapping.get(today.strftime("%A"))
        persian_day_number = today.day
        persian_month = month_mapping.get(today.strftime("%B"))
        persian_year = today.strftime("%Y")

        feedback_message = f"""
<blockquote>💬 نظر شما</blockquote>

👤 نام کاربر : {name}
🔖 شماره حواله: [{request_id}](https://t.me/TabadolArz_Trades/{post_id})
💡 میزان رضایت :

<blockquote>{'⭐️' * stars}</blockquote>

📅 {persian_day} {persian_day_number} {persian_month} {persian_year}
📝 متن نظر :

<blockquote>
{feedback_text}
</blockquote>

<blockquote>🆔 @TabadolArz_Robot</blockquote>"""
        
        feedback_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("تایید بازخورد", callback_data=f"confirm_feedback"),
                    InlineKeyboardButton("رد بازخورد", callback_data=f"reject_feedback")
                ]
            ]
        )
        try:
            await client.send_message(chat_id=-1002246606763, text=feedback_message, reply_markup=feedback_keyboard , disable_web_page_preview  = True)
            await message.reply("✅ بازخورد شما برای بررسی ارسال شد. ممنون از همکاری شما!")
        except Exception as e:
            print(f"Error sending feedback to admin: {e}")
            await message.reply("❌ متاسفانه در ارسال بازخورد شما مشکلی پیش آمد. لطفا دوباره تلاش کنید.")
        await state_manager.delete(message)
        del temp_user_states[user_id]

    except KeyError:
        pass
        # await message.reply("⚠️ لطفا دوباره از طریق منوی ارسال بازخورد اقدام کنید.")
        # return

    
@Client.on_message(is_feedback_request_id & filters.private)
@is_added
async def handle_feedback_request_id(client: Client, message: Message):
    try:
        request_id = int(message.text)
        request = requests.get(request_id)
        if not request:
            await message.reply("⚠️ متاسفانه شناسه درخواستی که وارد کردید یافت نشد.")
            return

        user_id = message.from_user.id
        is_creator = request['user_id'] == user_id
        related_bids = bids.get_related_bid_with_request_id(int(message.text))
        
        is_bidder = False
        for bid in related_bids:
            if bid['user_id'] == user_id:
                is_bidder = True
                break
        
        if not (is_creator or is_bidder):
            await message.reply("⛔️ شما نه ایجاد کننده این درخواست هستید و نه پیشنهادی برای آن ثبت کرده‌اید.")
            return
        
        # Check request status before allowing feedback
        if request['status'] != 'success':
            if request['status'] != 'pending':
                await message.reply("⚠️ این درخواست هنوز در وضعیت معلق قرار دارد. لطفا پس از نهایی شدن معامله بازخورد خود را ارسال کنید.")
                return
            else:
                await message.reply("⚠️ این درخواست هنوز نهایی نشده است.")
                return

        if user_id not in temp_user_states:
            temp_user_states[user_id] = {}
        temp_user_states[user_id]['request_id'] = request_id
        stars_kb = InlineKeyboard(row_width=1)
        stars_lst = []
        stars_lst.append(InlineButton("⭐", callback_data="feedback_star_1"))
        stars_lst.append(InlineButton("⭐⭐", callback_data="feedback_star_2"))
        stars_lst.append(InlineButton("⭐⭐⭐", callback_data="feedback_star_3"))
        stars_lst.append(InlineButton("⭐⭐⭐⭐", callback_data="feedback_star_4"))
        stars_lst.append(InlineButton("⭐⭐⭐⭐⭐", callback_data="feedback_star_5"))
        stars_lst.append(InlineButton("❌ انصراف", callback_data="feedback_cancel"))
        stars_kb.add(*stars_lst)

        await message.reply("🌟 لطفا امتیاز خود را انتخاب کنید:", reply_markup=stars_kb)
        await state_manager.set("feedback_stars", message)

    except ValueError:
        await message.reply("🔢 لطفا شناسه حواله را بصورت عددی وارد کنید.",reply_markup=cance_kb)
        return
    except Exception as e:
        print(f"Error in handle_feedback_request_id: {e}")
        await message.reply("😕 متاسفانه مشکلی پیش آمده است. لطفا دوباره تلاش کنید.")
        return

@Client.on_callback_query(filters.regex("^feedback_star_"))
async def handle_feedback_stars(client: Client, callback_query):
    print(callback_query.data)
    star_count = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    if user_id not in temp_user_states:
        temp_user_states[user_id] = {}
    temp_user_states[user_id]['stars'] = star_count
    await callback_query.message.reply("📝 لطفا متن بازخورد خود را ارسال کنید:",reply_markup=cance_kb)
    await state_manager.set("feedback_text", callback_query)




@Client.on_message(is_sending_request & not_banned & filters.private)
@is_added
async def handle_user_request_texts(client: Client, message: Message):
    await handle_user_request_generation(client,message) 



@Client.on_message(is_sending_bid & not_banned & filters.private)
@is_added
async def handle_user_biding_texts(client: Client, message: Message):
    await handle_user_bid(client,message) 






@Client.on_message(sending_message_to_user & not_banned & filters.private)
@is_added
async def handle_sending_message_to_user(client: Client, message: Message):
    user_message_reciever= await state_manager.get_user_chat_reciever(message)
    await message.copy(chat_id=int(user_message_reciever))
    await state_manager.delete(message)
    await message.reply("پیام شما با موفقیت برای این کاربر ارسال شد !",reply_markup=home_kb)
    



@Client.on_message(makeing_search & not_banned & filters.private)
@is_added
async def handle_making_search(client: Client, message: Message):
    await find_request(message)
    




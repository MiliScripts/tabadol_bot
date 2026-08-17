from pyrogram import Client , filters
from pyrogram.types import CallbackQuery
from pykeyboard import InlineKeyboard , InlineButton
from helpers.keyboard import *
from helpers.state import *
from helpers.db import *
from configs.config import *
from helpers.utils import *
from helpers.pyro_utils import *
from pyrogram.errors import UserNotParticipant
from plugins.user import temp_user_states



@Client.on_callback_query(filters.regex("confirm_feedback"))
async def handle_accept_feedback(c:Client,q:CallbackQuery):
    try:
        message = await c.copy_message(
            chat_id=-1002464737438,
            from_chat_id=q.message.chat.id,
            message_id=q.message.id,
        )
        await q.message.edit_reply_markup(reply_markup=None)
        print(f"Feedback message sent to -1002464737438 with message ID: {message.id}")
    except Exception as e:
        print(f"Error sending feedback to admin: {e}")
        await q.answer("❌ متاسفانه در ارسال بازخورد مشکلی پیش آمد. لطفا دوباره تلاش کنید.")

@Client.on_callback_query(filters.regex("reject_feedback"))
async def handle_reject_feedback(c:Client,q:CallbackQuery):
    await q.answer("بازخورد شما رد شد.")



@Client.on_callback_query(filters.regex("ustd-joined"))
async def handle_button_membership_ustd(c:Client,q:CallbackQuery):
    try:
        user_id = q.from_user.id
        member = await c.get_chat_member(-1002343881600, user_id)
        await q.message.delete()
        await show_user_menu(c,q.message)
    except UserNotParticipant:
        await q.answer("شما هنوز در گروه تتر جوین نشدید !")


@Client.on_callback_query(filters.regex("confirm-membership"))
async def handle_button_membership(c:Client,q:CallbackQuery):
    try:
        user_id = q.from_user.id
        member = await c.get_chat_member(-1002065261878, user_id)
        await q.message.delete()
        await show_user_menu(c,q.message)
    except UserNotParticipant:
        await q.answer("شما هنوز در کانال ما جوین نشدید !")

@Client.on_callback_query(filters.regex("edit-profile"))
async def handle_button(c:Client,q:CallbackQuery):
    await q.message.reply('''
💬 نام و نام خانوادگی خودتون رو وارد کنید''',reply_markup=home_kb)
    users.update(q.from_user.id, "state", "name")
    await state_manager.set("name",q)
    return 

def calculate(number_one, number_two, p_type):
    result = number_one * number_two
    if p_type == 'فروشنده':
        result -= result * 0.005
    elif p_type == 'خریدار':
        result += result * 0.005
    return result
@Client.on_callback_query(filters.regex("confirm-bid:"))
async def handle_button_confirm_bid(c: Client, q: CallbackQuery):
    try:
        print("handle_button_confirm_bid: Started")
        call = q.data
        print(f"handle_button_confirm_bid: call = {call}")
        user_id = q.from_user.id
        print(f"handle_button_confirm_bid: user_id = {user_id}")
        bid_id = int(call.split(":")[1])
        print(f"handle_button_confirm_bid: bid_id = {bid_id}")
        bid_details = bids.get(bid_id)
        print(f"handle_button_confirm_bid: bid_details = {bid_details}")
        if not bid_details:
            print("handle_button_confirm_bid: bid_details is None")
            await q.answer("جزئیات پیشنهاد پیدا نشد.", show_alert=True)
            return

        request_id = int(bid_details.get("request_id"))
        print(f"handle_button_confirm_bid: request_id = {request_id}")
        print(f"Bid Details: {bid_details}")
        print(f"Bid ID: {bid_id}")
        
        request_data = requests.get(request_id)
        if not request_data:
            await q.answer("اطلاعات درخواست یافت نشد",show_alert=True)
            return
        post_id = str(request_data.get('post_id', ''))

        
        
        print(post_id)

        bid_user_id = bid_details.get("user_id")
        print(f"handle_button_confirm_bid: bid_user_id = {bid_user_id}")

        link = f'[لینک حواله]({group_link}/{post_id})'
        print(f"handle_button_confirm_bid: link = {link}")
        try:
            await c.send_message(chat_id=bid_user_id, text='با پیشنهاد شما موافقت شد'+"\n\n"+link)
            print("handle_button_confirm_bid: Message sent to bid user")
        except Exception as e:
            await q.answer(str(e))
            print(f"Error sending message to bid user: {e}")

        bids.update(bid_id, "status", "approved")
        print("handle_button_confirm_bid: Bid status updated")

        try:
            await update_request_status(c, q.message, request_id)
            print("handle_button_confirm_bid: Request status updated")
        except Exception as e :
            print("ok who cares about ",str(e))    

        await q.answer("دستور شما ثبت و به پیشنهاد دهنده اطلاع داده شد")
        print("handle_button_confirm_bid: Answer sent to user")
    
        

        bidder_info = users.get(bid_user_id)
        bidder_name = bidder_info.get('name', 'ناشناس') if bidder_info else 'ناشناس'
        bidder_mention = f"[{bidder_name}](tg://user?id={bid_user_id})"
        print(f"handle_button_confirm_bid: bidder_mention = {bidder_mention}")
        price = format_number(bid_details.get("price"))
        print(f"handle_button_confirm_bid: price = {price}")
        extype = "خریدار" if request_data.get("exchange_type")=='buyer' else "فروشنده"
        print(f"handle_button_confirm_bid: extype = {extype}")
        way ="خرید" if extype=='فروشنده' else "فروش"
        print(f"handle_button_confirm_bid: way = {way}")
        amount = request_data.get('amount')
        amount = int(amount) if amount else 0
        print(f"handle_button_confirm_bid: amount = {amount}")
        currancy = request_data.get('currency')
        print(f"handle_button_confirm_bid: currancy = {currancy}")
        chikooo = ''
        calculated_amount = calculate(number_one = int(bid_details.get("price")),number_two=int(request_data.get('amount')),p_type="خریدار" if extype=='فروشنده' else "فروشنده")
        should_pay = format_number(int(calculated_amount) if calculated_amount else 0)
        print(f"handle_button_confirm_bid: should_pay = {should_pay}")
        if way=='خرید' : 
            chikooo = f'''☑️ حواله {request_id}   -  پیشنهاد {way} {amount} {currancy} با قیمت {price} تومان توسط {extype} پذیرفته شد؛ شما پس از پرداخت {should_pay} تومان مبلغ {amount} {currancy} دریافت خواهید کرد.

    برای انجام معامله از طریق گزینه‌ی ارتباط با کارشناس معاملات اقدام کنید.'''
        else:
            chikooo = f'''☑️ حواله {request_id}   -  پیشنهاد {way} {amount} {currancy} با قیمت {price} تومان توسط {extype} پذیرفته شد؛ شما پس از پرداخت {amount} {currancy} مبلغ  {should_pay} تومان   دریافت خواهید کرد.

برای انجام معامله از طریق گزینه‌ی ارتباط با کارشناس معاملات اقدام کنید.'''

        print(f"handle_button_confirm_bid: chikooo = {chikooo}")
        try:
            await c.send_message(chat_id=bid_user_id,text=chikooo,reply_markup=make_start_deal_kb())
            print("handle_button_confirm_bid: Message sent to bid user with deal KB")
        except Exception as e:
            await q.answer(str(e))
            print(f"Error sending message to bid user with deal KB: {e}")

        requests.update(request_id,"open_to_bid",False)
        print("handle_button_confirm_bid: Request open_to_bid updated to False")

        way ="فروش" if extype=='فروشنده' else "خرید"
        print(f"handle_button_confirm_bid: way = {way}")
        sam = "پرداخت میکنید" if extype=='خریدار' else "دریافت میکنید"
        print(f"handle_button_confirm_bid: sam = {sam}")
        calculated_amount_2 = calculate(number_one = int(bid_details.get("price")),number_two=int(request_data.get('amount')),p_type=extype)
        cc = format_number(int(calculated_amount_2) if calculated_amount_2 else 0)
        print(f"handle_button_confirm_bid: cc = {cc}")
        y_n_text =f'''☑️ حواله {request_id}   -  با این پیشنهاد  موافقت شد
بابت {way} {amount} {currancy} مبلغ {cc} {sam}'''
        print(f"handle_button_confirm_bid: y_n_text = {y_n_text}")
        try:
            await q.edit_message_text(text=f"با این پیشنهاد موافقت شد\n\n{y_n_text}\n\nبرای انجام معامله از طریق گزینه‌ی ارتباط با کارشناس معاملات اقدام کنید.",reply_markup=make_start_deal_kb())
            print("handle_button_confirm_bid: Edited message text")
        except Exception as e:
            print(f"Error editing message text: {e}")
            if "MESSAGE_NOT_MODIFIED" in str(e):
                await q.answer("The message was not modified because you tried to edit it using the same content",show_alert=True)


        admins_kb_conforamtion = InlineKeyboard(row_width=2)
        admins_kb_conforamtion.add(
            InlineButton("کنسلی حواله‌دار",f"notok:{bid_id}-dealer"),
            InlineButton("کنسلی حواله‌گیر",f"notok:{bid_id}-bidder"),
            InlineButton("تایید انجام موفق حواله",f"okk:{bid_id}-{request_id}"),
            InlineButton("کنسلی کارشناسی",f"notok:agent-{bid_id}-{request_id}"),
            

        )

        print("handle_button_confirm_bid: Created admins_kb_conforamtion")
        g1 = '''
🔻 دریافتی: {}  {}
🔻 پرداختی: {} {}
'''
        g2 = '''
🔻 دریافتی: {} {}
🔻 پرداختی: {} {}
'''
        if request_data.get("exchange_type")=='seller':
            print("handle_button_confirm_bid: Exchange type is seller")
            g1 =g1.format(cc," تومان",amount , remove_emoji(currancy))
            g2 = g2.format(amount,remove_emoji(currancy),should_pay," تومان")


        elif  request_data.get("exchange_type")=='buyer':
            print("handle_button_confirm_bid: Exchange type is buyer")
            g1 =g1.format(amount,remove_emoji(currancy),cc, " نومان") 
            g2 = g2.format(should_pay," تومان",amount , remove_emoji(currancy))

        print(f"handle_button_confirm_bid: g1 = {g1}")
        print(f"handle_button_confirm_bid: g2 = {g2}")

        dealer_info = users.get(request_data.get("user_id"))
        dealer_name = dealer_info.get("name", "ناشناس") if dealer_info else "ناشناس"
        dealer_username = dealer_info.get("username")
        dealer_phone = dealer_info.get("phone_number")

        bidder_info = users.get(bid_user_id)
        bidder_name = bidder_info.get("name", "ناشناس") if bidder_info else "ناشناس"
        bidder_username = bidder_info.get("username")
        bidder_phone = bidder_info.get("phone_number")


        report_text = f'''

گزارش معامله

🔻 {link}

↩️ حواله دار:
✔️ نام : {dealer_name}
✔️ نام کاربری : {"@" + str(dealer_username) if dealer_username else "ندارد"}
✔️ شماره تماس : {"+" + str(dealer_phone) if dealer_phone else "ندارد"}
{g1}

↩️ حواله‌گیر:
✔️ نام : {bidder_name}
✔️ نام کاربری : {"@" + str(bidder_username) if bidder_username else "ندارد"}
✔️  شماره تماس : {"+" + str(bidder_phone) if bidder_phone else "ندارد"}
{g2}
'''

        try:
            await c.send_message(chat_id=report_channel,text=report_text,reply_markup=admins_kb_conforamtion)
            print("handle_button_confirm_bid: Sent report to report channel")
        except Exception as e:
            await q.answer(str(e))
            print(f"Error sending report to report channel: {e}")











    except Exception as e :
        print(f"handle_button_confirm_bid: An exception occurred: {e}")
        if "MESSAGE_NOT_MODIFIED" in str(e):
            await q.answer("The message was not modified because you tried to edit it using the same content",show_alert=True)



@Client.on_callback_query(filters.regex("reject-bid:"))
async def handle_button_reject_bid(c:Client,q:CallbackQuery):
    try:
        call = q.data
        user_id = q.from_user.id
        bid_id=  int(call.split(":")[1])
        bid_details = bids.get(bid_id)
        if not bid_details:
            await q.answer("Bid not found.", show_alert=True)
            return

        bid_user_id = bid_details.get("user_id")
        request_id = int(bid_details.get("request_id"))
        request_details = requests.get(request_id)

        if not request_details:
            await q.answer("Request not found.", show_alert=True)
            return

        post_id = str(request_details.get('post_id'))
        link = f'[لینک حواله]({group_link}/{post_id})'
        try:
            await c.send_message(chat_id=bid_user_id,text='با پیشنهاد شما مخالفت شد'+"\n"+link)
        except Exception as e:
            
            await q.answer(str(e))
            print(f"Failed to send rejection message to bidder: {e}")

        bids.update(bid_id,"status","rejected")
        await update_request_status(c,q.message,request_id)
        await q.edit_message_text("دستور شما ثبت و به پیشنهاد دهنده اطلاع داده شد "+"\n"+link)

        requests.update(request_id,"open_to_bid",True)

    except Exception as e:
        print(f"An error occurred in handle_button_reject_bid: {e}")
        await q.answer(f"An error occurred: {e}", show_alert=True)



@Client.on_callback_query(filters.regex("^feedback_cancel"))
async def handle_feedback_cancel(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in temp_user_states:
        del temp_user_states[user_id]
    await callback_query.message.reply("❌ عملیات بازخورد لغو شد.", reply_markup=user_menu)
    await state_manager.delete(callback_query)



@Client.on_callback_query(filters.regex("message:"))
async def handle_button_messagedd_bid(c:Client,q:CallbackQuery):

    call = q.data
    user_id = q.from_user.id
    bid_id=  int(call.split(":")[1])
    bid_details = bids.get(bid_id)
    await q.message.reply("پیام خود را در قالب متن وارد کنید",quote=True,reply_markup=cance_kb)
    await state_manager.set("send-message-to-user",q.message)
    await state_manager.set_user_chat_reciever(q.message,int(bids.get(bid_id).get("user_id")))

    
@Client.on_callback_query(filters.regex("meow3"))
async def handle_start_form(c:Client,q:CallbackQuery):
    check= await user_has_unfilled_field(c,q.message)
    if check :
        await q.message.reply('''⚠️ برای ادامه لطفا اطلاعات پروفایل خود را کامل کنید 

💬 نام و نام خانوادگی خودتون رو وارد کنید''',reply_markup=home_kb)
        await state_manager.set("name",q.message)
        return 




@Client.on_callback_query(filters.regex("rpage:"))
async def on_page_callback_request_pagination(client: Client, callback_query: CallbackQuery):
    # print(callback_query.data)
    # print("pagination called  for bids")
    page = int(callback_query.data.split(":")[1])
    user_requests = requests.get_all_user_requests(callback_query.from_user.id)
    requests1, total_pages = paginate_requests(user_requests, page)
    keyboard = generate_inline_keyboard(requests1, page, total_pages)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@Client.on_callback_query(filters.regex("request_option:"))
async def on_request_callback_request(client: Client, callback_query: CallbackQuery):


    request_id = int(callback_query.data.split(":")[1])
    # print("showing req")
    user_requests = requests.get_all_user_requests(callback_query.from_user.id)

    request = next((req for req in user_requests if req['request_id'] == request_id), None)
    # print(request)
    if request:
        details = format_request_details(request)
        keyboard = generate_request_details_keyboard(request_id)
        await callback_query.message.edit_text(details, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("delete_request:"))
async def on_edit_delete_callback_request(client: Client, callback_query: CallbackQuery):
    # print("del req")

    request_id = int(callback_query.data.split(":")[1])
    # print(request_id)
    kb = InlineKeyboard()
    kb.add(
            InlineButton("بازگشت به درخواست ها",'show-req')
        )
    await callback_query.message.edit_text("درخواست شما با موفقیت حذف شد",reply_markup=kb)
    try:
        p = requests.get(request_id).get('post_id')
        requests.delete(request_id)
        # print("deleting message")
        # print(force_join_channel_id)
        await client.delete_messages(chat_id=discussion_send_chat,message_ids=p)
        
    except Exception as e:
        print(e)
        pass    





@Client.on_callback_query(filters.regex("bpage:"))
async def on_page_callback_bid(client: Client, callback_query: CallbackQuery):
    # print("pagination called  for bids")
    # print(callback_query.data)
    page = int(callback_query.data.split(":")[1])
    user_bids = bids.get_all_user_bids(callback_query.from_user.id)
    bid1s, total_pages = paginate_bids(user_bids = bids.get_all_user_bids(callback_query.from_user.id), page=page)
    keyboard = generate_bids_inline_keyboard(bids1, page, total_pages)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@Client.on_callback_query(filters.regex("bid_option:"))
async def on_bid_callback(client: Client, callback_query: CallbackQuery):
    user_bids = bids.get_all_user_bids(callback_query.from_user.id)
    bid_id = int(callback_query.data.split(":")[1])
    bid = next((b for b in user_bids if b['bid_id'] == bid_id), None)
    if bid:
        details = format_bid_details(bid)
        keyboard = generate_bid_details_keyboard(bid_id)
        await callback_query.message.edit_text(details, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("delete_bid:"))
async def on_edit_delete_callback_bid(client: Client, callback_query: CallbackQuery):
    # print('del bid')
    
    bid_id = int(callback_query.data.split(":")[1])
    # print(bid_id)

    try:
        kb = InlineKeyboard()
        kb.add(
            InlineButton("بازگشت به پیشنهاد ها",'show-bid')
        )
        await callback_query.message.edit_text("پیشنهاد شما با موفقیت حذف شد",reply_markup=kb)
        bids.delete(bid_id)
        await update_request_status(client,callback_query.message,bids.get(bid_id).get("request_id"))
        
    except Exception as e :
        print(e)
        pass    


@Client.on_callback_query(filters.regex("failed:"))
async def alamolhoda(client: Client, callback_query: CallbackQuery):
    
    user_id_to_fail = int(callback_query.data.split(":"))
    users.update(user_id_to_fail,"failed_transactions",users.get(user_id_to_fail).get("failed_transactions")+1)
    await callback_query.answer("تراکنش ناموفق برای کاربر ثبت شد")



@Client.on_callback_query(filters.regex("success:"))
async def malekmotiee(client: Client, callback_query: CallbackQuery):
    bid_id = callback_query.data.split(":")[1]
    bid = bids.get(int("bid_id"))
    bidder =bid.get("user_id")
    requester = requests.get(bid.get("request_id")).get("user_id")
    lst = [int(bidder),int(requester)]
    for item in lst:
        user_id_to_success = item
        users.update(item,"successfull_transactions",users.get(user_id_to_fail).get("successfull_transactions")+1)


    
    await q.answer("تراکنش موفق برای کاربر ثبت شد")    




@Client.on_callback_query(filters.regex("show-req"))
async def show_requessts_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_requests = requests.get_all_user_requests(callback_query.from_user.id)
    if user_requests==[]:
        await callback_query.message.reply(quote=True,text="شما هنوز هیچ درخواستی ثبت نکرده اید !")
        return
    requests1, total_pages = paginate_requests(user_requests, 1)
    keyboard = generate_inline_keyboard(requests1, 1, total_pages)
    await callback_query.message.reply("درخواست های شما به شرح زیر هست\nبرای ادامه یکی از گزینه های زیر رو انتخاب کنید :",
                        reply_markup=keyboard)
    await callback_query.message.delete()                    




@Client.on_callback_query(filters.regex("show-bid"))
async def show_bids_handlefr(client: Client, callback_query: CallbackQuery):        
    user_id = callback_query.from_user.id
    user_bids = bids.get_all_user_bids(callback_query.from_user.id)
    if user_bids==[]:
                await callback_query.message.reply(quote=True,text="شما هنوز هیچ پیشنهادی ثبت نکرده اید !")
                return
    bids1, total_pages = paginate_bids(user_bids, 1)
    keyboard = generate_bids_inline_keyboard(bids1, 1, total_pages)
    await callback_query.message.reply("پیشنهادهای  شما به شرح زیر هست\nبرای ادامه یکی از گزینه های زیر رو انتخاب کنید :", reply_markup=keyboard)
    await callback_query.message.delete()




@Client.on_callback_query(filters.regex("notok:"))
async def deal_not_ok_dealer(c:Client,q:CallbackQuery):
    user_id = q.from_user.id
    call = q.data
    # add cancell by agent funtianality
    if call.split(":")[1].split("-")[0]=="agent":
        bid_id = call.split(":")[1].split("-")[1]
        request_id = call.split(":")[1].split("-")[2]
        bidder = bids.get(int(bid_id)).get("user_id")
        dealer = requests.get(int(request_id)).get("user_id")
        post_id = requests.get(int(request_id)).get("post_id")
        link = f'[لینک حواله]({group_link}/{post_id})'
        lst = [
            dealer , bidder
        ]
        bids.update(bid_id,"status","rejected")
        message_text = q.message.text
        await q.edit_message_text(message_text+"\n\n"+"نتیجه : کنسلی از سوی کارشناس")
        for item in lst :
            try:
                await c.send_message(
                    chat_id = item,
                    text ="معامله از سوی کارشناس کنسل شد"+"\n\n"+link
                )
            except Exception as e :
                await q.answer(str(e))
                print(e)
                continue
        requests.update(request_id,"open_to_bid",True)    
        return
            
            
                    
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    notok_type = call.split(":")[1].split("-")[1]
    # print(f"transcation failed (notok) > by [ {notok_type} ]")
    # print(call)
    bid_id = call.split(":")[1].split("-")[0]
    bids.update(int(call.split(":")[1].split("-")[0]),"status","rejected")
    try:
        await update_request_status(c,q.message,int(bids.get(int(bid_id)).get("request_id")))
    except :
        pass    
    if notok_type=="dealer":
        request_id = bids.get(int(bid_id)).get("request_id")
        bid_id = call.split(":")[1].split("-")[0]
        deatials = requests.get(int(request_id)).get("user_id")
        users.update(deatials,"failed_transactions",users.get(deatials).get("failed_transactions")+1)
        message_text = q.message.text
        await q.edit_message_text(message_text+"\n\n نتیجه : کنسلی حواله دار")
        request_id = bids.get(int(bid_id)).get("request_id")
        bidder = bids.get(int(bid_id)).get("user_id")
        dealer = requests.get(int(request_id)).get("user_id")
        post_id = requests.get(int(request_id)).get("post_id")
        lst = [bidder,dealer]
        link = f'[لینک حواله]({group_link}/{post_id})'
        for item in lst : 
            try:
                await c.send_message(
                    chat_id = item ,
                    text = "معامله کنسل شد (از سوی حواله دار)"+"\n\n"+link
                )
            except Exception as e :
                await q.answer(str(e))
                print(e)
            continue
        
        requests.update(request_id,"open_to_bid",True)
        return
    elif notok_type=='bidder':
        bid_id = call.split(":")[1].split("-")[0]
        request_id = bids.get(int(bid_id)).get("request_id")
        # print(f"request id : {request_id}")
        # print(requests.get(int(request_id)))
        details = bids.get(int(bid_id)).get("user_id")
        users.update(details,"failed_transactions",users.get(details).get("failed_transactions")+1)
        message_text = q.message.text
        await q.edit_message_text(message_text+"\n\n نتیجه : کنسلی حواله گیر")
        
        bidder = bids.get(int(bid_id)).get("user_id")
        dealer = requests.get(int(request_id)).get("user_id")
        post_id = requests.get(int(request_id)).get("post_id")
        lst = [bidder,dealer]
        link = f'[لینک حواله]({group_link}/{post_id})'
        for item in lst : 
            try:
                await c.send_message(
                    chat_id = item ,
                    text = "معامله کنسل شد (از سوی حواله گیر)"+"\n\n"+link
                )
            except Exception as e :
                await q.answer(str(e))
                print(e)
                continue
        requests.update(request_id,"open_to_bid",True)    



@Client.on_callback_query(filters.regex("okk:"))
async def deal_not_ok_bidder(c:Client,q:CallbackQuery):
    user_id = q.from_user.id
    call = q.data
    request_id = call.split(":")[1].split("-")[1]
    bid_id = call.split(":")[1].split("-")[0]
    bidder = bids.get(int(bid_id)).get("user_id")
    dealer = requests.get(int(request_id)).get("user_id")
    post_id = requests.get(int(request_id)).get("post_id")
    lst = [int(bidder),int(dealer)]
    for item in lst :
        print("adding to users success fields")
        users.update(item,"successfull_transactions",users.get(item).get("successfull_transactions")+1)
    message_text = q.message.text
    await q.edit_message_text(message_text+"\n\n نتیجه  : معامله موفقیت آمیر بود !")




    # givinfg 0.5 % of transaction whole result to the inviter
    whole_result = int(requests.get(request_id=int(request_id)).get("amount"))  * int(bids.get(bid_id=int(bid_id)).get("price"))
    print('whole result :',whole_result)
    the_percenatge= int(whole_result) * 0.005
    print(" the  0.5  f the result will be added to inviters ")
    
    



    # adding to inviter of the bidder 
    bidder_inviter = users.get(bids.get(bid_id=int(bid_id)).get("user_id")).get("invited_by")
    if bidder_inviter==None:
        pass
    else:
        users.update(bidder_inviter,'wallet',users.get(bidder_inviter).get("wallet")+the_percenatge)
        the_bidder_name = users.get(bids.get(bid_id=int(bid_id)).get("user_id")).get("name")
        try:
                    await c.send_message(chat_id =bidder_inviter,text=f'''💢 برای کاربر {the_bidder_name} که با لینک رفرال شما وارد ربات شده بود ، یک  معامله موفقیت آمیز ثبت شد و نیم درصد از حجم کل معامله به مبلغ {format_number(the_percenatge)} تومان به کیف پول شما در ربات واریز شد .


            ❇️ موجودی جدید کیف پول شما :
            {format_number(users.get(bidder_inviter).get("wallet"))} تومان''')
        except Exception as e :
             await q.answer(str(e))
             print(e)
             pass


    # adding to inviter of the requester 
    requester_inviter = users.get(requests.get(request_id=int(request_id)).get("user_id")).get("invited_by")
    if requester_inviter==None:
        pass
    else:
        users.update(requester_inviter,'wallet',users.get(requester_inviter).get("wallet")+the_percenatge)
        the_requester_name = users.get(requests.get(request_id=int(request_id)).get("user_id")).get("name")
        try:
            await c.send_message(chat_id =requester_inviter,text=f'''💢 برای کاربر {the_requester_name} که با لینک رفرال شما وارد ربات شده بود ، یک  معامله موفقیت آمیز ثبت شد و نیم درصد از حجم کل معامله به مبلغ {format_number(the_percenatge)} تومان به کیف پول شما در ربات واریز شد .


    ❇️ موجودی جدید کیف پول شما :
    {format_number(users.get(requester_inviter).get("wallet"))} تومان''')
        except Exception as e :
             await q.answer(str(e))
             print(e)
             pass
            
     # edit send bid button to see feedbacks "مشاهده نظرات"  
    try:
        print("[**] editing post message button")
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        # Bots only
        await c.edit_message_reply_markup(
            chat_id = discussion_send_chat ,
            message_id= int(post_id),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("مشاهده نظرات", url="https://t.me/Tabadol_Comments")]]))
        print("request post button updated")
    except Exception as e :
        print(f"failed to edit main post - {post_id} -button > {e}")        
     
     
     # send to bidder and request owner to send feed back "ارسال نظر
    for user in lst :
        text = "معامله شما با موفقیت انجام شد و سپاس از  اعتماد و حسن انتخاب شما\nدر صورت تمایل لطفا نظرتون رو در گروه تبادل ارز ارسال کنید"
        button = InlineKeyboard()
        button.add(
            InlineButton("ارسال نظر ☁️",url = f"https://t.me/TabadolArz_Robot?start=feedback_{request_id}")
        )
        try:
            await c.send_message(
                chat_id = int(user),
                text = text ,
                reply_markup = button
            )
            print(f"ask for feedback sent to user {user}")
        except Exception as e :
            await q.answer(str(e))
            print(f"failed to send to {user} > {e}")
            
     
      














# <--- post and not post

@Client.on_callback_query(filters.regex("post:"))
async def handle_post_channel(c: Client, q: CallbackQuery):
    request_id = int(q.data.split(":")[1])
    kb = start_paramed_kb_request(request_id)

    try:
        # Send the post to the main discussion channel
        post_msg = await c.send_message(
            chat_id=discussion_send_chat,
            text=await get_post_text(c, request_id),
            reply_markup=kb,
            parse_mode=enums.ParseMode.HTML
        )

        # Update the request with the new post ID
        requests.update(request_id, "post_id", post_msg.id)

        # Edit the callback query message to show confirmation
        mess_text = q.message.text
        link = f'[لینک حواله]({group_link}/{post_msg.id})'
        updated_text = mess_text + "\n\n" + f" ☑️ این آگهی در چنل پست شد !\nلینک : {link}"
        await q.edit_message_text(text=updated_text)

        # Notify the user who requested the post
        requested_by = requests.get(request_id).get("user_id")
        try:
            await c.send_message(
                chat_id=int(requested_by),
                text='آگهی شما با موفقیت توسط ادمین تایید شد و در کانال قرار داده شد !' + f"\n\n {link}"
            )
        except Exception as e_user:
            await q.answer(f"خطا در ارسال پیام به کاربر: {e_user}")
            print(f"User notification error: {e_user}")

        print(f"Request after posting: {requests.get(request_id)}")

        # Send post to any custom channels related to this request
        print("Sending to channels related")
        await send_to_custom_channels(
            client=c,
            currency=requests.get(request_id).get("currency"),
            message_text=await get_post_text(c, request_id),
            kb=kb
        )

    except Exception as e:
        # Catch any error in sending or editing messages
        await q.answer(f"خطا در ارسال آگهی: {e}")
        print(f"Error in handle_post_channel: {e}")



@Client.on_callback_query(filters.regex("del:"))
async def handle_not_post(c: Client, q: CallbackQuery):    
        request_id = int(q.data.split(":")[1])
        requested_By = requests.get(int(request_id)).get("user_id")
        try:
            await c.send_message(
                chat_id = int(requested_By),
                text = "آگهی شما رد شد !"
            )
        except Exception as e :
            print(e)
            await q.answer(str(e))
        await q.answer("آگهی رد شد")

        await q.edit_message_text(text=q.message.text+"\n\n🔴 آگهی رد شد")
    
    
    

@Client.on_callback_query(filters.regex("wallet-withdraw")) 
async def handel_Wallet_withdraw(c: Client, q: CallbackQuery):
    user_id = q.from_user.id
    user = users.get(user_id)
    balance = user.get("wallet")
    if balance == 0:
        await q.answer("شما هیچ مقداری در کیف پول ندارید !")
    else:
        await q.answer("برای تسویه کیف پول از بخش پشتیبانی به کارشناس مربوطه درخواست واریز دهید", show_alert=True)
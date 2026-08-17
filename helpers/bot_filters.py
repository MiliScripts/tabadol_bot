from pyrogram import filters
from configs.config import admins, force_join_channel_id , discussion_send_chat
from pyrogram import Client
from pyrogram.errors import UserNotParticipant
from pyrogram.types import Message
from .pyro_utils import send_guest_membersip_alert, show_user_menu
from helpers.db import users, requests, bids, banned_users
from helpers.state import state_manager

# admin filter
async def check_if_user_is_admin(_, __, message: Message):
    try:
        try:
            return message.from_user.id in admins
        except:
            return False
    except:
        pass

# member filter
async def check_user_in_chat(_, client: Client, message: Message):
    try:
        try:
            user_id = message.from_user.id
            member = await client.get_chat_member(discussion_send_chat, user_id)
            return True
        except UserNotParticipant:
            return False
        except Exception as e:
            return False
    except:
        pass

async def check_user_not_in_chat(_, client: Client, message: Message):
    try:
        try:
            user_id = message.from_user.id

            try:
                user_id = message.from_user.id
                member = await client.get_chat_member(-1002065261878, user_id)
                return False
            except UserNotParticipant:
                print("user is not a member of the chat!")
                return True
        except Exception as e:
            return False
    except:
        pass

async def check_user_filing_form(_, client: Client, message: Message):
    try:
        message_text = message.text
        if message_text == "❌ انصراف":
            await state_manager.delete(message)
            await show_user_menu(client, message)
        user_id = message.from_user.id
        user_state = await state_manager.get(message)
        if user_state in ['name', 'city', 'number', 'country']:
            return True
        return False
    except:
        pass

async def check_user_Sending_request(_, client: Client, message: Message):
    try:
        try:
            message_text = message.text
            if message_text == "❌ انصراف":
                await state_manager.delete(message)
                await show_user_menu(client, message)
            user_current_state = await state_manager.get(message)
            if user_current_state in ["currency", 'amount', 'method', 'exchange_type', 'price', "description", "confirm", "send-request"]:
                return True
            return False
        except:
            return False
    except:
        pass

async def check_user_Sending_bid(_, client: Client, message: Message):
    try:
        try:
            message_text = message.text
            if message_text == "❌ انصراف":
                await state_manager.delete(message)
                await show_user_menu(client, message)
            user_current_state = await state_manager.get(message)
            if user_current_state in ["sending-bid-price", "confirm-bid"]:
                return True
            return False
        except:
            return False
    except:
        pass

async def check_user_sending_message(_, client: Client, message: Message):
    try:
        try:
            user_current_state = await state_manager.get(message)
            if user_current_state in ["send-message-to-user"]:
                return True
            return False
        except:
            return False
    except:
        pass

async def user_making_search(_, client: Client, message: Message):
    try:
        try:
            user_current_state = await state_manager.get(message)
            if user_current_state in ['select=serach=currency', 'select=serach=type']:
                return True
            return False
        except:
            return False
    except:
        pass

async def admin_sending_broardcast(_, client: Client, message: Message):
    try:
        try:
            user_current_state = await state_manager.get(message)
            print(user_current_state)
            if user_current_state in ["broadcast"]:
                return True
            return False
        except:
            return False
    except:
        pass

async def check_if_user_is_banned(_, __, m):
    try:
        try:
            user_id = m.from_user.id
            return banned_users.is_banned(user_id)
        except:
            return False
    except:
        pass

async def check_if_user_is_not_banned(_, __, m):
    try:
        try:
            user_id = m.from_user.id
            return not banned_users.is_banned(user_id)
        except:
            return False
    except:
        pass

async def check_user_feedback_text(_, client: Client, message: Message):
    try:
        user_current_state = await state_manager.get(message)
        print("user state is : ",user_current_state)
        if user_current_state == "feedback_text":
            return True
        return False
    except:
        return False

async def check_user_feedback_request_id(_, client: Client, message: Message):
    try:
        user_current_state = await state_manager.get(message)
        if user_current_state == "feedback_request_id":
            return True
        return False
    except:
        return False

async def check_user_feedback_stars(_, client: Client, message: Message):
    try:
        user_current_state = await state_manager.get(message)
        if user_current_state == "feedback_stars":
            return True
        return False
    except:
        return False

is_admin = filters.create(func=check_if_user_is_admin)
is_member = filters.create(func=check_user_in_chat)
is_filling_profile = filters.create(func=check_user_filing_form)
is_sending_request = filters.create(func=check_user_Sending_request)
is_sending_bid = filters.create(func=check_user_Sending_bid)
not_memeber = filters.create(func=check_user_not_in_chat)
sending_message_to_user = filters.create(func=check_user_sending_message)
makeing_search = filters.create(func=user_making_search)
broadcasting = filters.create(func=admin_sending_broardcast)
is_banned = filters.create(func=check_if_user_is_banned)
not_banned = filters.create(func=check_if_user_is_not_banned)
is_feedback_text = filters.create(func=check_user_feedback_text)
is_feedback_request_id = filters.create(func=check_user_feedback_request_id)
is_feedback_stars = filters.create(func=check_user_feedback_stars)
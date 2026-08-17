from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import jdatetime
from .utils import get_current_jalali_date, get_jalali_date
import os
from datetime import datetime


Base = declarative_base()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "bot.db")
os.makedirs(BASE_DIR, exist_ok=True)
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    phone_number = Column(String)
    telegram_first_name = Column(String)
    telegram_last_name = Column(String)
    username = Column(String)
    country = Column(String)
    name = Column(String)
    joined_date = Column(String)
    successfull_transactions = Column(Integer, default=0)
    failed_transactions = Column(Integer, default=0)
    refrals = Column(String)  # Store as comma-separated string
    invited_by = Column(Integer)
    wallet = Column(Float, default=0)

class Request(Base):
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    currency = Column(String)
    amount = Column(String)
    payment_method = Column(String)
    exchange_type = Column(String)
    price = Column(String)
    description = Column(String)
    status = Column(String)
    post_id = Column(Integer)
    created_date = Column(String)
    open_to_bid = Column(Boolean)

class Bid(Base):
    __tablename__ = 'bids'

    id = Column(Integer, primary_key=True)
    bid_id = Column(Integer)
    request_id = Column(Integer, ForeignKey('requests.request_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    price = Column(String)
    status = Column(String)
    date = Column(String)

class BannedUser(Base):
    __tablename__ = 'banned_users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    reason = Column(String)
    ban_date = Column(DateTime, default=datetime.utcnow)


class UserDB:
    def __init__(self):
        self.session = Session()

    def add(self, user_id, first_name, username, last_name=None, country=None, phone_number=None):
        existing_user = self.session.query(User).filter_by(user_id=user_id).first()
        if not existing_user:
            new_user = User(
                user_id=user_id,
                phone_number=phone_number,
                telegram_first_name=first_name,
                telegram_last_name=last_name,
                username=username,
                country=country,
                joined_date=get_current_jalali_date(),
                refrals=''
            )
            self.session.add(new_user)
            self.session.commit()

    def delete(self, user_id):
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            self.session.delete(user)
            self.session.commit()

    def update(self, user_id, field, value):
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if user:
            setattr(user, field, value)
            self.session.commit()

    def user_exists(self, user_id):
        return self.session.query(User).filter_by(user_id=user_id).first() is not None

    def not_filled_form(self, user_id):
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return True
        unfiled_data = []
        its_ok = ['telegram_last_name', 'username', "invited_by","refrals"]
        for column in User.__table__.columns:
            if column.name in its_ok:
                continue
            value = getattr(user, column.name)
            if value is None:
                unfiled_data.append(column.name)
        if unfiled_data:
            # print(f"not provided fields : {' - '.join(unfiled_data)}")
            return True
        return False

    def get(self, user_id):
        user = self.session.query(User).filter_by(user_id=user_id).first()
        return user.__dict__ if user else None

    def get_all_users_ids(self):
        return [user.user_id for user in self.session.query(User).all()]

class RequestsDB:
    def __init__(self):
        self.session = Session()

    def add(self, user_id, currency=None, amount=None, payment_method=None, exchange_type=None, price=None, description=None, status='pending'):
        last_request = self.session.query(Request).order_by(Request.request_id.desc()).first()
        request_id = last_request.request_id + 1 if last_request else 1
        
        new_request = Request(
            request_id=request_id,
            user_id=user_id,
            currency=currency,
            amount=amount,
            payment_method=payment_method,
            exchange_type=exchange_type,
            price=price,
            description=description,
            status=status,
            created_date=str(jdatetime.datetime.now()),
            open_to_bid=True
        )
        self.session.add(new_request)
        self.session.commit()
        return request_id


    def delete(self, request_id):
        request = self.session.query(Request).filter_by(request_id=request_id).first()
        if request:
            self.session.delete(request)
            self.session.commit()
            # print("Request deleted @")

    def update(self, request_id, field, value):
        request = self.session.query(Request).filter_by(request_id=request_id).first()
        if request:
            setattr(request, field, value)
            self.session.commit()

    def get(self, request_id):
        request = self.session.query(Request).filter_by(request_id=request_id).first()
        if not request:
            # print(f"request with id {request_id} doesnt exist !")
            return False
        return request.__dict__

    def get_all_user_requests(self, user_id):
        return [request.__dict__ for request in self.session.query(Request).filter_by(user_id=user_id).all()]

    def get_requets_by_currency(self, currency, type):
        # print("currecny : ", currency)
        # print('type :', type)
        f = 'seller' if type == '💎 فروشنده' else 'buyer'
        # print(f)
        return [request.__dict__ for request in self.session.query(Request).filter_by(currency=currency, exchange_type=f).all()]

class BidsDB:
    def __init__(self):
        self.session = Session()

    def add(self, user_id, price=None, request_id=None):
        last_bid = self.session.query(Bid).order_by(Bid.bid_id.desc()).first()
        bid_id = last_bid.bid_id + 1 if last_bid else 1
        
        new_bid = Bid(
            bid_id=bid_id,
            request_id=request_id,
            user_id=user_id,
            price=price,
            date=get_jalali_date()
        )
        self.session.add(new_bid)
        self.session.commit()
        return bid_id

    def delete(self, bid_id):
        bid = self.session.query(Bid).filter_by(bid_id=bid_id).first()
        if bid:
            self.session.delete(bid)
            self.session.commit()
            # print("bid deleted")

    def update(self, bid_id, field, value):
        bid = self.session.query(Bid).filter_by(bid_id=bid_id).first()
        if bid:
            setattr(bid, field, value)
            self.session.commit()

    def get(self, bid_id):
        bid = self.session.query(Bid).filter_by(bid_id=bid_id).first()
        if not bid:
            print(f"bid with id {bid_id} doesnt exist !")
            return False
        return bid.__dict__

    def get_related_bid_with_request_id(self, request_id):
        return [bid.__dict__ for bid in self.session.query(Bid).filter_by(request_id=request_id).all()]

    def get_all_user_bids(self, user_id):
        return [bid.__dict__ for bid in self.session.query(Bid).filter_by(user_id=user_id).all()]

class BannedUsersDB:
    def __init__(self):
        self.session = Session()

    def add(self, user_id, reason=None):
        existing_ban = self.session.query(BannedUser).filter_by(user_id=user_id).first()
        if not existing_ban:
            new_ban = BannedUser(user_id=user_id, reason=reason)
            self.session.add(new_ban)
            self.session.commit()
            return True
        return False

    def remove(self, user_id):
        banned_user = self.session.query(BannedUser).filter_by(user_id=user_id).first()
        if banned_user:
            self.session.delete(banned_user)
            self.session.commit()
            return True
        return False

    def is_banned(self, user_id):
        return self.session.query(BannedUser).filter_by(user_id=user_id).first() is not None

    def get_all_banned_users(self):
        return [banned_user.__dict__ for banned_user in self.session.query(BannedUser).all()]

    def get_ban_reason(self, user_id):
        banned_user = self.session.query(BannedUser).filter_by(user_id=user_id).first()
        return banned_user.reason if banned_user else None


               
def generate_euro_daily_report():
    requests_db = RequestsDB()
    today = jdatetime.date.today().strftime("%Y-%m-%d")
    euro_requests = [
        req for req in requests_db.get_requets_by_currency("💶 یورو", None)
        if req['created_date'].startswith(today)
    ]
    
    if not euro_requests:
        return "No Euro transactions today."
    
    prices = [float(req['price']) for req in euro_requests if req['price'] != "توافقی🤝"]
    
    if not prices:
        return "No valid prices for Euro transactions today."
    
    start_price = prices[0]
    max_price = max(prices)
    min_price = min(prices)
    end_price = prices[-1]
    
    report = f"""📌 گزارش معاملات یورو  

تاریخ: {jdatetime.date.today().strftime("%Y/%m/%d")}
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــ

◾️ شروع قیمت: {start_price:,.0f}
◾️ بیشترین قیمت: {max_price:,.0f}
◾️ کمترین قیمت: {min_price:,.0f}
◾️ پایان قیمت: {end_price:,.0f}

💎 درگاه امن معاملات ارزی"""

    return report                
                

# Initialize the databases
users = UserDB()
requests = RequestsDB()
bids = BidsDB()
banned_users = BannedUsersDB()




def get_euro_min_max():
    requests_db = RequestsDB()
    today = jdatetime.date.today().strftime("%Y-%m-%d")
    euro_requests = [
        req for req in requests_db.get_requets_by_currency("💶 یورو", None)
        if req['created_date'].startswith(today)
    ]
    
    if not euro_requests:
        return 0,0
    
    prices = [int(req['price']) for req in euro_requests if req['price'] != "توافقی🤝" and req['price']!=None]
    max_price = max(prices)
    min_price = min(prices)
    return max_price,min_price



def get_ustd_min_max():
    requests_db = RequestsDB()
    today = jdatetime.date.today().strftime("%Y-%m-%d")
    ustd_requests = [
        req for req in requests_db.get_requets_by_currency("💎 تتر", None)
        if req['created_date'].startswith(today)
    ]
    
    if not ustd_requests:
        return 0,0
    
    prices = [int(req['price']) for req in ustd_requests if req['price'] != "توافقی🤝" and req['price']!=None]
    max_price = max(prices)
    min_price = min(prices)
    return max_price,min_price





class CryptalChannels:
    def __init__(self):
        self.channels = {
            "europe": {
                "persian_name": "اروپا",
                "url": "https://t.me/TabadolArz_Europe",
                "chat_id": -1002339012039
            },
            "italy": {
                "persian_name": "ایتالیا",
                "url": "https://t.me/TabadolArz_Italy_Group",
                "chat_id": -1002349489420
            },
            "cyprus": {
                "persian_name": "قبرس",
                "url": "https://t.me/Cryptal_Cyprus_Group",
                "chat_id": -1002288647780
            },
            "spain": {
                "persian_name": "اسپانیا",
                "url": "https://t.me/Cryptal_Spain_Group",
                "chat_id": -1002457142632
            },
            "germany": {
                "persian_name": "المان",
                "url": "https://t.me/Germany_TabadolArz_Group",
                "chat_id": -1002384522064
            },
            "turkey": {
                "persian_name": "ترکیه",
                "url": "https://t.me/Cryptal_Turkiye_Group",
                "chat_id": -1002287827533
            },
            "london": {
                "persian_name": "لندن",
                "url": "https://t.me/TabadolArz_London_Group",
                "chat_id": -1002481520621
            },
            "china": {
                "persian_name": "چین",
                "url": "https://t.me/RMB_Cryptal_Group",
                "chat_id": -1002369021803
            },
            "denmark": {
                "persian_name": "دانمارک",
                "url": "https://t.me/Denmark_TabadolArz_Group",
                "chat_id": -1002398357287
            },
            "canada": {
                "persian_name": "کانادا",
                "url": "https://t.me/Cryptal_Canada_Group",
                "chat_id": -1002340663316
            },
            "usa": {
                "persian_name": "امریکا",
                "url": "https://t.me/TabadolArz_USA_Group",
                "chat_id": -1002263723875
            },
            "dubai": {
                "persian_name": "دبی",
                "url": "https://t.me/TabadolArz_Dubai_Group",
                "chat_id": -1002347581386
            },
        }

cryptal_channels = CryptalChannels()



from pyrogram.errors import UserNotParticipant
from helpers.db import users
from colorama import Fore, Style

async def confirm_user_susbscription(user_id,client):
    
    user = users.get(user_id)
    if not user:
        return False  # Or handle the case where the user doesn't exist

    user_country = user.get("country")
    print("user is from",user_country)
    for channel_name, channel_data in cryptal_channels.channels.items():
        print(channel_data["persian_name"] )
        if channel_data["persian_name"] in user_country :
            try:
                print(f"{Fore.GREEN}User {user_id} should join the {user_country} channel: {channel_data['persian_name']}{Style.RESET_ALL}")
                member = await client.get_chat_member(channel_data["chat_id"], user_id)
                return True
            except UserNotParticipant:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(f"کانال {channel_data['persian_name']}", url=channel_data['url'])
                        ],
                        [
                            InlineKeyboardButton("✅ بررسی عضویت", callback_data="recheck_subscription")
                        ]
                    ]
                )

                await client.send_message(
                    chat_id=user_id,
                    text=f"برای ادامه، لطفاً در کانال {channel_data['persian_name']} به آدرس زیر عضو شوید:",
                    reply_markup=keyboard
                )
                
                
                return False
            except Exception as e:
                print(e)
                return
        
        
        
    else :
            print("checling user be join in general group")
            # checling user be join in general group
            try:
                member = await client.get_chat_member(-1002065261878, user_id)
                return True
            except UserNotParticipant:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("گروه جامع تبادلات ارزی", url="https://t.me/TabadolArz_Trades")
                        ],
                        [
                            InlineKeyboardButton("✅ بررسی عضویت", callback_data="recheck_subscription")
                        ]
                    ]
                )

                await client.send_message(
                    chat_id=user_id,
                    text="برای ادامه، لطفاً در کانال اصلی عضو شوید:",
                    reply_markup=keyboard
                )
                return False
            except Exception as e:
                print(e)
                return
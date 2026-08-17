from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import jdatetime
from utils import get_current_jalali_date, get_jalali_date
import os
# Get the current script's directory
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

# Create engine and session
# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate up to the parent directory and locate the database file
db_path = os.path.join(current_dir, '..', 'bot.db')

# Create the database engine
engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

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
                refrals=""
            )
            self.session.add(new_user)
            self.session.commit()


    def get_all(self):
        users = self.session.query(User).all()
        return [{c.name: getattr(user, c.name) for c in user.__table__.columns} for user in users]
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
        its_ok = ['telegram_last_name', 'username', "invited_by"]
        for column in User.__table__.columns:
            if column.name in its_ok:
                continue
            value = getattr(user, column.name)
            if value is None:
                unfiled_data.append(column.name)
        if unfiled_data:
            print(f"not provided fields : {' - '.join(unfiled_data)}")
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
        return {
            "request_id" : request_id,
            "user_id" : user_id,
            "currency" : currency,
            "amount" : amount,
            "payment_method" : payment_method,
            "exchange_type" : exchange_type,
            "price" : price,
            "description" : description,
            'status' : status,
            "created_date" : str(jdatetime.datetime.now()),
            "open_to_bid" : True
        }

    def delete(self, request_id):
        request = self.session.query(Request).filter_by(request_id=request_id).first()
        if request:
            self.session.delete(request)
            self.session.commit()
            print("Request deleted @")

    def update(self, request_id, field, value):
        request = self.session.query(Request).filter_by(request_id=request_id).first()
        if request:
            setattr(request, field, value)
            self.session.commit()

    def get(self, request_id):
        request = self.session.query(Request).filter_by(request_id=request_id).first()
        if not request:
            print(f"request with id {request_id} doesnt exist !")
            return False
        return request.__dict__

    def get_all_user_requests(self, user_id):
        return [request.__dict__ for request in self.session.query(Request).filter_by(user_id=user_id).all()]

    def get_requets_by_currecny(self, currency, type):
        print("currecny : ", currency)
        print('type :', type)
        f = 'seller' if type == '💎 فروشنده' else 'buyer'
        print(f)
        return [request.__dict__ for request in self.session.query(Request).filter_by(currency=currency, exchange_type=f).all()]





# Initialize the databases
users = UserDB()
requests = RequestsDB()

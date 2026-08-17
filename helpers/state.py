import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pyrogram.types import Message

Base = declarative_base()

class UserState(Base):
    __tablename__ = 'user_states'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    next = Column(String)
    req_id = Column(Integer)
    chat_id = Column(Integer)
    bid_id = Column(Integer)
    currency = Column(String)
    type = Column(String)

# Use the existing exchange database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "bot.db")
engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class StateManager:
    def __init__(self):
        self.session = Session()

    def get_or_create_user(self, user_id):
        user = self.session.query(UserState).filter_by(user_id=user_id).first()
        if not user:
            user = UserState(user_id=user_id, next="", req_id=None, chat_id=None, bid_id=None, currency=None, type="")
            self.session.add(user)
            self.session.commit()
        return user

    async def set(self, step: str, message: Message):
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        user.next = step
        self.session.commit()

    async def get(self, message: Message) -> str:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        return user.next

    async def jget(self, message: Message) -> dict:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        return {c.name: getattr(user, c.name) for c in user.__table__.columns}

    async def set_bid_id(self, message: Message, bid_id) -> None:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        user.bid_id = bid_id
        self.session.commit()

    async def get_bid_id(self, message: Message) -> int:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        return user.bid_id

    async def reset(self, message: Message) -> None:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        user.next = ""
        user.req_id = None
        user.chat_id = None
        user.bid_id = None
        user.currency = None
        user.type = ""
        self.session.commit()

    async def delete(self, message: Message) -> None:
        user_id = message.from_user.id
        user = self.session.query(UserState).filter_by(user_id=user_id).first()
        if user:
            self.session.delete(user)
            self.session.commit()

    async def get_user_last_request(self, message: Message) -> int:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        return user.req_id

    async def set_user_last_request(self, message: Message, request_id) -> None:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        user.req_id = request_id
        self.session.commit()

    async def set_user_chat_reciever(self, message: Message, chat_id) -> None:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        user.chat_id = chat_id
        self.session.commit()

    async def get_user_chat_reciever(self, message: Message) -> int:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        return user.chat_id

    def get_search_currency(self, message):
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        return user.currency

    def get_search_type(self, message):
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        return user.type

    def set_search_currency(self, message, currency):
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        user.currency = currency
        self.session.commit()

    def set_search_type(self, message, search_type):
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        user.type = search_type
        self.session.commit()

    async def delete_user_last_request(self, message: Message) -> None:
        user_id = message.from_user.id
        user = self.get_or_create_user(user_id)
        user.req_id = None
        self.session.commit()

# Initialize the state manager
state_manager = StateManager()
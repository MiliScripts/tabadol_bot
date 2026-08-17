from pyrogram import Client
from configs.config import *
from time import time


class Api(Client):
    def __init__(self):
        super().__init__(
            name="Api",
            api_id=api_id,
            api_hash=api_hash,
            app_version="1.0.0",
            device_model="Postchi",
            bot_token=bot_token,
            plugins={"root": "plugins"},
            workers=20
        )

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        print("Bot started!")
        try:
            await self.send_message(5361491365, "✅ ربات با موفقیت آنلاین و فعال شد.")
        except Exception as e:
            print(f"Error sending startup message: {e}")

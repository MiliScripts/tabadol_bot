import os
import time
import shutil
import requests
import pandas as pd
import jdatetime

from datetime import datetime
from colorama import Fore, init

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
)
from sqlalchemy.orm import declarative_base, sessionmaker

# =========================
# CONFIG
# =========================

BOT_TOKEN = "7142012125:AAHlSGZiO40Mu6v2X4LcCSJqFcLFqNk4rpM"

CHAT_IDS = [
    51998101,
    5361491365
]

BACKUP_INTERVAL = 15 * 60  # 15 minutes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot.db")

EXCEL_FILE = os.path.join(BASE_DIR, "users.xlsx")
TEMP_DB_BACKUP = os.path.join(BASE_DIR, "bot_backup.db")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

# =========================
# INIT
# =========================

init(autoreset=True)

os.makedirs(BASE_DIR, exist_ok=True)

Base = declarative_base()

engine = create_engine(f"sqlite:///{DB_PATH}")

Session = sessionmaker(bind=engine)

# =========================
# MODELS
# =========================

class User(Base):
    __tablename__ = "users"

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

    refrals = Column(String)

    invited_by = Column(Integer)

    wallet = Column(Float, default=0)

Base.metadata.create_all(engine)

# =========================
# HELPERS
# =========================

def get_jalali_datetime():
    now = jdatetime.datetime.now()
    return now.strftime("%Y/%m/%d - %H:%M:%S")


def create_excel_backup():
    """
    Export users table to Excel.
    """

    session = Session()

    try:
        users = session.query(User).all()

        data = []

        for index, user in enumerate(users, start=1):
            data.append({
                "index": index,
                "id": user.id,
                "user_id": user.user_id,
                "phone_number": user.phone_number,
                "telegram_first_name": user.telegram_first_name,
                "telegram_last_name": user.telegram_last_name,
                "username": user.username,
                "country": user.country,
                "name": user.name,
                "joined_date": user.joined_date,
                "successfull_transactions": user.successfull_transactions,
                "failed_transactions": user.failed_transactions,
                "refrals": user.refrals,
                "invited_by": user.invited_by,
                "wallet": user.wallet
            })

        df = pd.DataFrame(data)

        df.to_excel(EXCEL_FILE, index=False)

        print(
            Fore.GREEN +
            f"[+] Excel backup created successfully ({len(data)} users)"
        )

        return len(data)

    except Exception as e:
        print(Fore.RED + f"[ERROR] Excel backup failed: {e}")
        return 0

    finally:
        session.close()


def create_database_backup():
    """
    Create safe SQLite backup copy.
    """

    try:
        shutil.copy2(DB_PATH, TEMP_DB_BACKUP)

        print(Fore.GREEN + "[+] Database backup copied successfully")

        return True

    except Exception as e:
        print(Fore.RED + f"[ERROR] Database backup failed: {e}")

        return False


def send_file(chat_id, file_path, caption):
    """
    Send file to Telegram.
    """

    try:
        with open(file_path, "rb") as file:

            response = requests.post(
                TELEGRAM_API_URL,
                data={
                    "chat_id": chat_id,
                    "caption": caption
                },
                files={
                    "document": file
                },
                timeout=60
            )

        if response.status_code == 200:

            print(
                Fore.GREEN +
                f"[+] Sent: {os.path.basename(file_path)} -> {chat_id}"
            )

            return True

        else:

            print(
                Fore.RED +
                f"[ERROR] Telegram send failed "
                f"({response.status_code}) "
                f"for chat_id={chat_id}"
            )

            print(response.text)

            return False

    except Exception as e:

        print(
            Fore.RED +
            f"[ERROR] Exception while sending file: {e}"
        )

        return False


def send_backup():
    """
    Main backup process.
    """

    print(Fore.CYAN + "\n========== BACKUP STARTED ==========")

    total_users = create_excel_backup()

    db_ok = create_database_backup()

    if not db_ok:
        return

    jalali_datetime = get_jalali_datetime()

    caption = (
        f"📦 BID Backup\n\n"
        f"🕒 {jalali_datetime}\n"
        f"👥 Total users: {total_users}"
    )

    files_to_send = [
        TEMP_DB_BACKUP,
        EXCEL_FILE
    ]

    for file_path in files_to_send:

        if not os.path.exists(file_path):

            print(
                Fore.RED +
                f"[ERROR] File not found: {file_path}"
            )

            continue

        for chat_id in CHAT_IDS:

            send_file(chat_id, file_path, caption)

    print(Fore.YELLOW + "========== BACKUP FINISHED ==========\n")


# =========================
# MAIN LOOP
# =========================

def main():

    print(Fore.CYAN + "[+] Backup service started")

    while True:

        try:

            send_backup()

        except Exception as e:

            print(
                Fore.RED +
                f"[FATAL ERROR] {e}"
            )

        print(
            Fore.YELLOW +
            f"[+] Sleeping for {BACKUP_INTERVAL // 60} minutes..."
        )

        time.sleep(BACKUP_INTERVAL)


if __name__ == "__main__":
    main()
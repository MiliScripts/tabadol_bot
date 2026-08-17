#!/usr/bin/env python3
import os
import sys
import time
import json
import csv
import math
import sqlite3
import requests
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot.db")
CSV_PATH = os.path.join(BASE_DIR, "inactive_users.csv")
BOT_TOKEN = "7142012125:AAHlSGZiO40Mu6v2X4LcCSJqFcLFqNk4rpM"

# Target Banner Image URL
PROMO_IMAGE_URL = "https://files.imeow.ir/dl/default/bd4b513f-bc11-4d20-b75d-59c758e817c5.png"

# Target Test User & Admin Notifications List
TEST_USER_ID = 6379933870
ADMIN_IDS = [5361491365, 51998101, 982290123]

# BATCH RATE LIMIT: Exactly 30 items per 60-second minute window
BATCH_SIZE = 30
BATCH_INTERVAL = 60.0  # seconds

TELEGRAM_SEND_PHOTO_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
TELEGRAM_SEND_MSG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TELEGRAM_EDIT_MSG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"

# Reply Keyboard matching currency_kb()
CURRENCY_KEYBOARD = {
    "keyboard": [
        [{"text": "💎 تتر"}],
        [{"text": "🇨🇦 دلار کانادا"}, {"text": "🇷🇺 روبل روسیه"}],
        [{"text": "💷 پوند"}, {"text": "💲 دلار"}],
        [{"text": "🇦🇪 درهم"}, {"text": "💶 یورو"}],
        [{"text": "💶 لیر"}, {"text": "🇸🇪 کرون سوئد"}],
        [{"text": "🇩🇰 کرون دانمارک"}, {"text": "🇳🇴 کرون نروژ"}],
        [{"text": "🇨🇳 یوان چین"}],
        [{"text": "❌ انصراف"}]
    ],
    "resize_keyboard": True
}

console = Console()

# ================= TIME FORMATTING HELPER =================
def format_seconds_fa(seconds):
    """Format seconds into Persian readable duration string."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h} ساعت و {m} دقیقه و {s} ثانیه"
    elif m > 0:
        return f"{m} دقیقه و {s} ثانیه"
    else:
        return f"{s} ثانیه"

# ================= DATABASE & USER HELPERS =================
def get_inactive_users():
    """Fetch users from bot.db who have zero records in requests table."""
    if not os.path.exists(DB_PATH):
        console.print(f"[bold red]❌ Error: Database file not found at {DB_PATH}[/bold red]")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        u.user_id,
        u.name,
        u.telegram_first_name,
        u.telegram_last_name,
        u.username,
        u.phone_number,
        u.country,
        u.joined_date
    FROM users u
    WHERE u.user_id NOT IN (
        SELECT DISTINCT user_id 
        FROM requests 
        WHERE user_id IS NOT NULL
    )
    ORDER BY u.id ASC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def set_user_currency_state(user_id):
    """
    Set user's state in user_states table to 'currency' in bot.db.
    Guarantees tapping any currency button directly triggers order placement in bid_bot.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user_states WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            cursor.execute("UPDATE user_states SET next = 'currency', req_id = NULL WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("INSERT INTO user_states (user_id, next) VALUES (?, 'currency')", (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        console.print(f"[dim red]⚠️ DB State Update Error for {user_id}: {e}[/dim red]")

def format_user_message():
    """Build warm, professional, feature-rich Persian message encouraging user to trade."""
    return (
        "سلام و وقت بخیر کاربر گرامی 🖐️✨\n\n"
        "🔰 تاکنون هیچ سفارش خرید یا فروشی از طرف شما در درگاه امن معاملات ارزی ثبت نشده است!\n\n"
        "💎 با درگاه امن معاملات ارزی می‌توانید یک تجربه عالی، سریع و کاملاً امن در انجام تمامی حواله‌ها و تبادلات ارزی داشته باشید:\n"
        "⚡️ ثبت سفارش مستقیم در کوتاه‌ترین زمان\n"
        "🛡 تضمین امنیت کامل تمامی تراکنش‌ها\n"
        "💰 مناسب‌ترین نرخ و بهترین قیمت بازار\n\n"
        "⁉️ قصد خرید یا فروش کدام یک از ارز های زیر را دارید؟\n\n"
        "🟢 در حال حاضر خرید و فروش ارزهای موجود در منوی زیر امکان‌پذیر می‌باشد.\n\n"
        "🔴 در صورتی که ارز مورد نظر شما در لیست وجود ندارد، می‌توانید به ادمین اطلاع دهید تا در صورت لزوم اضافه گردد."
    )

def send_telegram_message(user_id, text):
    """
    Send photo + caption message via Telegram Bot API with FloodWait retry logic.
    """
    payload = {
        "chat_id": user_id,
        "photo": PROMO_IMAGE_URL,
        "caption": text,
        "reply_markup": json.dumps(CURRENCY_KEYBOARD),
        "parse_mode": "HTML"
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(TELEGRAM_SEND_PHOTO_URL, json=payload, timeout=15)
            res_data = response.json()

            if response.status_code == 200 and res_data.get("ok"):
                set_user_currency_state(user_id)
                return True, "Success"

            if response.status_code == 429 or res_data.get("error_code") == 429:
                retry_after = res_data.get("parameters", {}).get("retry_after", 10)
                console.print(f"[bold yellow]⚠️ FloodWait detected! Waiting for {retry_after} seconds...[/bold yellow]")
                time.sleep(retry_after + 1)
                continue

            error_desc = res_data.get("description", "Unknown Telegram Error")
            return False, error_desc

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return False, str(e)

    return False, "Max retries exceeded"

# ================= ADMIN NOTIFICATION HELPERS =================
def notify_admins_start(total_users, start_time):
    """Send initial broadcast start announcement with ETA to admins and return message IDs."""
    admin_msgs = {}
    start_str = start_time.strftime("%Y/%m/%d - %H:%M:%S")
    
    total_batches = math.ceil(total_users / BATCH_SIZE)
    est_total_secs = total_batches * BATCH_INTERVAL
    est_duration_str = format_seconds_fa(est_total_secs)

    text = (
        f"🚀 <b>گزارش شروع پخش همگانی (کاربران غیرفعال)</b>\n\n"
        f"⏰ <b>زمان شروع:</b> {start_str}\n"
        f"👥 <b>تعداد کل مخاطبین هدف:</b> {total_users} نفر\n"
        f"⚡️ <b>سرعت ارسال:</b> بافت‌های ۳۰ تایی در هر دقیقه\n"
        f"⏱ <b>مدت زمان تخمینی کل:</b> {est_duration_str}\n"
        f"🎯 <b>عملیات:</b> ارسال عکس و پیام فعال‌سازی + کیبورد ارزها\n\n"
        f"💎 <b>درگاه امن معاملات ارزی</b>"
    )
    for admin_id in ADMIN_IDS:
        try:
            res = requests.post(
                TELEGRAM_SEND_MSG_URL,
                json={"chat_id": admin_id, "text": text, "parse_mode": "HTML"},
                timeout=10
            )
            if res.ok:
                admin_msgs[admin_id] = res.json()["result"]["message_id"]
        except Exception as e:
            console.print(f"[dim red]Failed to notify admin {admin_id}: {e}[/dim red]")
    return admin_msgs

def update_admins_progress(admin_msgs, total, current, success, fail, start_time):
    """Update progress status message with ETA for all admins."""
    elapsed = str(datetime.now() - start_time).split('.')[0]
    percent = (current / total * 100) if total > 0 else 0
    
    remaining_users = total - current
    rem_batches = math.ceil(remaining_users / BATCH_SIZE)
    rem_secs = rem_batches * BATCH_INTERVAL
    rem_str = format_seconds_fa(rem_secs)

    text = (
        f"🔄 <b>گزارش پیشرفت پخش همگانی</b>\n\n"
        f"📊 <b>پیشرفت:</b> {current}/{total} ({percent:.1f}%)\n"
        f"⚡️ <b>سرعت ارسال:</b> بافت ۳۰تایی / دققه‌ای\n"
        f"✅ <b>ارسال موفق و فعال‌شده:</b> {success}\n"
        f"❌ <b>ناموفق / بلاک شده:</b> {fail}\n"
        f"⏱ <b>زمان سپری شده:</b> {elapsed}\n"
        f"⏳ <b>زمان باقی‌مانده تخمینی:</b> {rem_str}\n\n"
        f"💎 <b>درگاه امن معاملات ارزی</b>"
    )
    for admin_id, msg_id in admin_msgs.items():
        try:
            requests.post(
                TELEGRAM_EDIT_MSG_URL,
                json={"chat_id": admin_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"},
                timeout=10
            )
        except Exception:
            pass

def notify_admins_final(admin_msgs, total, success, fail, start_time, end_time):
    """Send final HTML completion summary report to admins."""
    duration_str = str(end_time - start_time).split('.')[0]
    start_str = start_time.strftime("%Y/%m/%d - %H:%M:%S")
    end_str = end_time.strftime("%Y/%m/%d - %H:%M:%S")
    success_pct = (success / total * 100) if total > 0 else 0

    text = (
        f"📊 <b>گزارش نهایی پخش همگانی کاربران غیرفعال</b>\n\n"
        f"➖➖ـــــــــــــــــــــــــــــــــــــــــــــــــــــــــ➖➖\n"
        f"👥 <b>تعداد کل کاربران هدف:</b> {total} نفر\n"
        f"⚡️ <b>سرعت ارسال:</b> ۳۰ پیام در دقیقه\n"
        f"✅ <b>ارسال موفق و فعال‌شده:</b> {success} نفر\n"
        f"❌ <b>ناموفق / بلاک شده:</b> {fail} نفر\n"
        f"📈 <b>درصد موفقیت:</b> {success_pct:.1f}%\n\n"
        f"📅 <b>زمان شروع:</b> {start_str}\n"
        f"📅 <b>زمان پایان:</b> {end_str}\n"
        f"⏱ <b>مدت زمان کل:</b> {duration_str}\n"
        f"➖➖ـــــــــــــــــــــــــــــــــــــــــــــــــــــــــ➖➖\n"
        f"💎 <b>درگاه امن معاملات ارزی</b>"
    )

    for admin_id in ADMIN_IDS:
        msg_id = admin_msgs.get(admin_id)
        edited = False
        if msg_id:
            try:
                res = requests.post(
                    TELEGRAM_EDIT_MSG_URL,
                    json={"chat_id": admin_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"},
                    timeout=10
                )
                edited = res.ok
            except Exception:
                edited = False

        if not edited:
            try:
                requests.post(
                    TELEGRAM_SEND_MSG_URL,
                    json={"chat_id": admin_id, "text": text, "parse_mode": "HTML"},
                    timeout=10
                )
            except Exception:
                pass

# ================= ACTION 1: EXPORT CSV =================
def action_export_csv():
    users = get_inactive_users()
    headers = ["User ID", "Name", "Telegram First Name", "Telegram Last Name", "Username", "Phone", "Country", "Joined Date"]
    
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(users)

    console.print(Panel(
        f"[bold green]✔ Successfully exported {len(users)} inactive users to CSV![/bold green]\n"
        f"[cyan]📁 Output file:[/cyan] {CSV_PATH}",
        title="[bold white]EXPORT COMPLETE[/bold white]",
        border_style="green"
    ))

# ================= ACTION 2: TEST SEND =================
def action_test_send():
    console.print(f"\n[cyan]🧪 Sending test photo message to user ID: [bold yellow]{TEST_USER_ID}[/bold yellow]...[/cyan]")
    test_message = format_user_message()
    
    success, detail = send_telegram_message(TEST_USER_ID, test_message)
    if success:
        console.print(Panel(
            f"[bold green]✅ Test photo message successfully sent to {TEST_USER_ID}![/bold green]\n"
            f"📷 Photo Attached: {PROMO_IMAGE_URL}\n"
            f"✔ DB State updated to 'currency' for user {TEST_USER_ID}.\n"
            f"📱 Tap any currency button in Telegram to test instant order creation flow!",
            title="[bold green]TEST SUCCESS[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold red]❌ Failed to send test message to {TEST_USER_ID}:[/bold red]\n"
            f"[yellow]{detail}[/yellow]",
            title="[bold red]TEST FAILED[/bold red]",
            border_style="red"
        ))

# ================= ACTION 3: BROADCAST ALL =================
def action_broadcast_all():
    users = get_inactive_users()
    total = len(users)

    if total == 0:
        console.print("[yellow]⚠️ No inactive users found in database.[/yellow]")
        return

    total_batches = math.ceil(total / BATCH_SIZE)
    est_total_secs = total_batches * BATCH_INTERVAL
    est_duration_str = format_seconds_fa(est_total_secs)

    console.print(Panel(
        f"[bold yellow]⚠️ BROADCAST WARNING[/bold yellow]\n\n"
        f"You are about to send photo + prompt caption to [bold green]{total}[/bold green] inactive users.\n"
        f"⚡️ Batch Speed: [bold cyan]30 messages per 1-minute window[/bold cyan].\n"
        f"⏳ Total Estimated Time (ETA): [bold green]{est_duration_str}[/bold green].\n"
        f"🔔 Admins ({', '.join(map(str, ADMIN_IDS))}) will receive live updates every 10 users with ETA.",
        border_style="yellow"
    ))

    if not Confirm.ask("[bold red]Are you sure you want to proceed?[/bold red]"):
        console.print("[dim]Broadcast cancelled by user.[/dim]")
        return

    start_time = datetime.now()
    admin_msgs = notify_admins_start(total, start_time)

    success_count = 0
    fail_count = 0
    processed_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Broadcasting in batches of 30/min...", total=total)

        for batch_idx in range(0, total, BATCH_SIZE):
            batch_users = users[batch_idx : batch_idx + BATCH_SIZE]
            batch_start_time = time.time()

            for user in batch_users:
                uid = user[0]
                msg = format_user_message()
                
                ok, reason = send_telegram_message(uid, msg)
                processed_count += 1

                if ok:
                    success_count += 1
                else:
                    fail_count += 1
                    console.print(f"[dim red]✖ Failed for User {uid}: {reason}[/dim red]")

                progress.update(task, advance=1, description=f"[cyan]Sent: [green]{success_count}[/green] | Failed: [red]{fail_count}[/red]")
                
                # Live Progress Update to Admins every 10 users or at the end
                if processed_count % 10 == 0 or processed_count == total:
                    update_admins_progress(admin_msgs, total, processed_count, success_count, fail_count, start_time)

                # Micro-pause between HTTP requests in batch to avoid socket bursts
                time.sleep(0.05)

            # Sleep remaining time of the 1-minute window if batch completed faster than 60s
            batch_elapsed = time.time() - batch_start_time
            if batch_elapsed < BATCH_INTERVAL and processed_count < total:
                pause_needed = BATCH_INTERVAL - batch_elapsed
                console.print(f"[dim cyan]⏳ Batch of {len(batch_users)} completed in {batch_elapsed:.1f}s. Pausing {pause_needed:.1f}s for 1-min window...[/dim cyan]")
                time.sleep(pause_needed)

    end_time = datetime.now()
    notify_admins_final(admin_msgs, total, success_count, fail_count, start_time, end_time)

    duration = str(end_time - start_time).split('.')[0]
    console.print(Panel(
        f"[bold green]🎉 Broadcast Process Complete![/bold green]\n\n"
        f"👥 Total Targeted Users: {total}\n"
        f"⚡️ Batch Pace: 30 msgs/min\n"
        f"✅ Successfully Delivered & Activated: {success_count}\n"
        f"❌ Failed / Blocked: {fail_count}\n"
        f"⏱️ Total Execution Duration: {duration}\n"
        f"🔔 HTML Status Report dispatched to Admins!",
        title="[bold white]SUMMARY REPORT[/bold white]",
        border_style="cyan"
    ))

# ================= MAIN MENU TUI =================
def main_menu():
    while True:
        console.clear()
        console.print(Panel(
            "[bold white]درگاه امن معاملات ارزی — INACTIVE USERS SYSTEM[/bold white]\n"
            "[dim]Filter, export, test and broadcast photo + currency interactive options[/dim]",
            subtitle="[cyan]v1.7.0 (30 msgs/min Batch Pace + ETA)[/cyan]",
            border_style="magenta"
        ))

        users = get_inactive_users()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Option", style="bold yellow", width=8)
        table.add_column("Description", style="white")

        table.add_row("1", f"📊 Export Inactive Users to CSV (Total: {len(users)} users)")
        table.add_row("2", f"🧪 Send Test Photo Message to ID: [bold yellow]{TEST_USER_ID}[/bold yellow]")
        table.add_row("3", f"🚀 Start Broadcast Photo & Activate State for ALL ({len(users)} users @ 30 msgs/min batch)")
        table.add_row("4", "❌ Exit Application")

        console.print(table)
        console.print()

        choice = Prompt.ask("[bold magenta]Select an option[/bold magenta]", choices=["1", "2", "3", "4"], default="1")

        if choice == "1":
            action_export_csv()
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")
        elif choice == "2":
            action_test_send()
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")
        elif choice == "3":
            action_broadcast_all()
            Prompt.ask("\n[dim]Press Enter to return to menu...[/dim]")
        elif choice == "4":
            console.print("[bold yellow]👋 Goodbye![/bold yellow]")
            break

if __name__ == "__main__":
    main_menu()
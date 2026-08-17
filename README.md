# 💎 Parachi / BID Exchange Automation Suite

[ English ] | [ فارسی ]

---

## 🌐 English Developer Guide & System Architecture

### 🚀 System Overview
The **Parachi Exchange Automation Suite** is a production-grade microservice platform engineered for peer-to-peer (P2P) exchange rate tracking, automated order-book polling, trade proposal matching, user KYC authentication, multi-channel currency banner rendering, and automated backups across Telegram, Bale Messenger, and Web App endpoints.

---

### 🧩 Microservices Workflow & Deep Dive

The platform consists of **9 independent microservices** running inside Docker Compose:

#### 1. `bid_bot` (`main.py`)
- **Core Technology**: Pyrogram, SQLAlchemy, SQLite (`bot.db`).
- **Function**: Main P2P Telegram exchange bot where users submit currency buy/sell requests and place bids.
- **Workflow**:
  1. **Request Flow**: User selects currency -> specifies buyer/seller -> enters amount -> selects payment method (Wise, Revolut, Western Union, TRC20) -> sets price -> submits description.
  2. **Approval & Channel Publishing**: Submitted request goes to admin channel for verification -> upon approval, published to trade channel (`@TabadolArz_Trades`).
  3. **Bidding Flow**: Counterparty clicks "Send Proposal 💌" deep link -> inputs proposed price -> request owner receives interactive proposal notification -> accepts or rejects bid.
  4. **Trade Resolution & Referral**: Upon successful trade completion, a 0.5% commission is automatically credited to the inviter'\''s wallet balance in `bot.db`.

#### 2. `bid_backuper` (`backuper.py`)
- **Core Technology**: Pandas, OpenPyXL, SQLite, Telegram Bot API.
- **Function**: Automated, zero-downtime database and user records backup service.
- **Workflow**:
  1. Runs every 15 minutes in a continuous background loop.
  2. Queries `users` table from SQLite `bot.db`.
  3. Exports user records into Excel (`users.xlsx`).
  4. Creates a safe copy of the database (`bot_backup.db`).
  5. Sends both backup files with timestamped Jalali date/time captions directly to administrator Telegram IDs.

#### 3. `bid_transactions_report` (`transactions_daily_report.py`)
- **Core Technology**: Schedule, jdatetime, SQLAlchemy.
- **Function**: Daily financial trading statistics generator and publisher.
- **Workflow**:
  1. Listens on schedule: daily at 21:00 (Tether) and 23:59 (Euro & Tether).
  2. Queries current date requests from `bot.db`.
  3. Calculates starting price, highest price (max), lowest price (min), and closing price (end).
  4. Generates an HTML summary report with links to channel posts and publishes it to the main channel.

#### 4. `navasan-to-bale` (`navasan_to_bale.py`)
- **Core Technology**: Requests, Bale Bot API.
- **Function**: Live currency JSON feed provider for Bale Messenger.
- **Workflow**:
  1. Fetches live currency rates JSON from Navasan worker API (`https://navasan.milaadfarzian.workers.dev/`).
  2. Encapsulates JSON data into an in-memory byte buffer (`prices.json`).
  3. Posts document to Bale channel via Bale Bot API (`sendDocument`).
  4. Repeats cycle every 5 minutes.

#### 5. `order-book` (`order-book.py`)
- **Core Technology**: Requests, PyTZ, jdatetime.
- **Function**: Live order book poller and multi-group announcement bot.
- **Workflow**:
  1. Loads processed order IDs from `data/seen_orders.json`.
  2. Polls Parachi Order Book API (`https://api.parachi.com/api/order-book`) every 10 seconds.
  3. Formats trade announcements with seller star rating, Persian volume formatting, Jalali date, and proposal deep link.
  4. Dispatches orders to the main Iran group (`-1003366343939`) and targeted country groups (Canada, Turkey, Russia, Denmark, Sweden, Europe).
  5. Saves updated order IDs back to `data/seen_orders.json`.

#### 6. `parachi-auth-bot` (`parachi_auth_bot.py`)
- **Core Technology**: Aiogram 3, SQLite (`bot_users.db`), Parachi Backend API.
- **Function**: User KYC verification, Web App magic link generator, and group chat gatekeeper.
- **Workflow**:
  1. **Authentication**: User selects residence country -> shares phone contact -> bot verifies country phone code format -> verifies membership in country group.
  2. **Web App Link**: Calls Parachi init API (`https://api.parachi.com/api/telegram/init`), generates a unique login URL with a 20-minute expiration timer.
  3. **Group Moderation**: Monitors messages in 11 Telegram groups. Automatically deletes messages from unregistered or non-KYC users and posts auto-deleting warning banners.

#### 7. `parachi-price-story-image` (`parachi_price_story_image/app.py`)
- **Core Technology**: Pillow (PIL), Schedule, Requests, PyTZ.
- **Function**: Daily price story image banner rendering engine.
- **Workflow**:
  1. Executes scheduled jobs at 00:00 AM and 12:00 PM (Tehran Time).
  2. Fetches currency rates with a 5-attempt retry mechanism to prevent zero/null values.
  3. Opens image template `assets/images/new_story_v2.png`.
  4. Renders Persian formatted prices for 11 currencies using TrueType font `assets/fonts/AbarMidFaNum-Bold.ttf`.
  5. Saves output banner to `assets/images/output.jpg` and sends photo + uncompressed document to admin Telegram IDs.

#### 8. `parachi-price-updates` (`parachi_price_updates.py`)
- **Core Technology**: Pillow (PIL), Schedule, Requests.
- **Function**: Multi-channel currency price banner publisher.
- **Workflow**:
  1. Executes scheduled jobs at 12:00 PM and 20:00 PM (Tehran Time).
  2. Fetches live rates, opens template `assets/images/new_banner_v2.png`.
  3. Stamps Tehran current time, Jalali date, and 11 currency rates onto node coordinates.
  4. Saves output banner to `assets/images/output.jpg` and broadcasts it to 12 Telegram channels/groups.

#### 9. `update_handler` (`scrapper/update_handler.py`)
- **Core Technology**: Pyrogram Userbot, Regex.
- **Function**: Channel scraper that monitors third-party trade channels (Fexpal, Patriex, Tetherland) and syncs trades into Parachi.
- **Workflow**:
  1. Listens to target channel IDs.
  2. Parses incoming messages via regex (`fexpal_regex`, `patriex_regex`).
  3. Extracts currency, action (buy/sell), amount, payment method, and price.
  4. Inserts trade request into `bot.db` and publishes formatted announcement to Parachi channels.

---

### 📂 Directory Layout

```text
/root/bid
├── assets/
│   ├── fonts/           # TrueType Font files (.ttf)
│   └── images/          # Image templates & output banners (.png, .jpg)
├── configs/             # YAML and Python configuration modules
├── data/                # Persistent runtime JSONs (seen_orders.json, currency_cache.json)
├── helpers/             # Database ORM models, state manager, & utilities
├── plugins/             # Pyrogram bot plugins (admin, user, inline)
├── scrapper/            # Channel scraping module & database models
├── parachi_price_story_image/ # Sub-service for story banner rendering
├── bot.db               # Primary SQLite database
├── bot_users.db         # User authentication SQLite database
├── docker-compose.yml   # Multi-service container orchestration
├── Dockerfile           # Container build specification (Python 3.12 + C build toolchain)
├── requirements.txt     # Python dependencies (frozen)
├── deploy.sh            # One-click deployment script from scratch
├── build.sh             # Interactive / CLI container builder
├── restart.sh           # Interactive / CLI container restarter
├── stop.sh              # Interactive / CLI container stopper
└── logs.sh              # Interactive / CLI live log viewer

⚡ Quick Deployment & CLI Management Guide

1. Full Deployment from Scratch

cd /root/bid
./deploy.sh

2. Interactive CLI Management Commands

Run any script without parameters for an interactive ANSI color menu, or pass
service names directly:

  - Build Containers:
      - Menu: ./build.sh
      - CLI: ./build.sh bid_bot parachi-auth-bot
  - Restart Containers:
      - Menu: ./restart.sh
      - CLI: ./restart.sh order-book
  - Stop Containers:
      - Menu: ./stop.sh
      - CLI: ./stop.sh navasan-to-bale
  - Stream Live Logs:
      - Menu: ./logs.sh
      - CLI: ./logs.sh bid_bot

🇮🇷 راهنمای جامع فارسی (Persian Developer Guide)

🚀 درباره پروژه

پلتفرم پاراچی (Parachi / BID) یک سیستم اتوماسیون معاملاتی و اطلاع‌رسانی مدرن بر
پایه میکروسرویس‌ها است که جهت تسهیل معاملات ارزی همتا-به-همتا (P2P)، احراز هویت
کاربران، پایش دفتر سفارشات (Order Book)، استعلام نرخ لحظه‌ای و تولید بنرهای
گرافیکی برای شبکه‌های اجتماعی طراحی شده است.

🧩 بررسی تخصصی کارکرد و گردش‌کار سرویس‌ها (Workflows)

۱. bid_bot (main.py)

  - کارکرد: ربات اصلی تلگرام جهت ثبت درخواست‌های خرید/فروش ارز و ارسال پیشنهاد
    قیمت.
  - گردش‌کار: کاربر نوع ارز، نوع معامله، مقدار، روش پرداخت (وایز، زوولوت، تتر
    و...) و قیمت پیشنهادی را وارد می‌کند -> پس از تایید ادمین، آگهی در کانال
    قرار می‌گیرد -> سایر کاربران با دکمه "ارسال پیشنهاد" قیمت پیشنهادی خود را
    ارسال می‌کنند -> مالک آگهی پیشنهاد را قبول یا رد می‌کند.

۲. bid_backuper (backuper.py)

  - کارکرد: سرویس بک‌آپ‌گیری خودکار دیتابیس و خروجی اکسل.
  - گردش‌کار: هر ۱۵ دقیقه یک‌بار اجرا می‌شود -> جدول کاربران را به فایل اکسل
    (users.xlsx) تبدیل کرده و از دیتابیس کپی می‌گیرد -> فایل‌ها را همراه با
    تاریخ شمسی به آیدی تلگرام ادمین‌ها ارسال می‌کند.

۳. bid_transactions_report (transactions_daily_report.py)

  - کارکرد: تولید گزارش‌های مالی و آمار روزانه معاملات.
  - گردش‌کار: در ساعت‌های ۲۱:۰۰ و ۲۳:۵۹ گزارش شروع قیمت، بیشترین قیمت، کمترین
    قیمت و قیمت پایانی یورو و تتر را محاسبه کرده و در کانال اصلی منتشر می‌کند.

۴. navasan-to-bale (navasan_to_bale.py)

  - کارکرد: ارسال نرخ‌های لحظه‌ای ارز به پیام‌رسان بله.
  - گردش‌کار: هر ۵ دقیقه نرخ‌های لحظه‌ای را به صورت فایل prices.json دریافت کرده
    و به کانال بله ارسال می‌کند.

۵. order-book (order-book.py)

  - کارکرد: پایش لحظه‌ای سفارشات سایت و انتشار در گروه‌های تلگرامی.
  - گردش‌کار: هر ۱۰ ثانیه سفارشات جدید سایت پاراچی را دریافت می‌کند -> متن آگهی
    را با فونت فارسی و تاریخ شمسی قالب‌بندی کرده و بر اساس نوع ارز به گروه‌های
    کشور مربوطه (کانادا، ترکیه، آلمان، فرانسه و...) ارسال می‌کند.

۶. parachi-auth-bot (parachi_auth_bot.py)

  - کارکرد: ربات احراز هویت کاربران و مدیریت دسترسی گروه‌ها.
  - گردش‌کار: شماره تماس کاربر را دریافت و فرمت آن را با کشور انتخابی چک می‌کند
    -> عضویت در گروه مربوطه را بررسی کرده و لینک اختصاصی ورود به وب‌اپلیکیشن را
    صادر می‌کند -> پیام‌های کاربران غیر احراز هویت شده در گروه‌ها را به صورت
    خودکار حذف می‌کند.

۷. parachi-price-story-image (parachi_price_story_image/app.py)

  - کارکرد: موتور رندر بنرهای استوری قیمت ارزها.
  - گردش‌کار: در ساعت‌های ۰۰:۰۰ و ۱۲:۰۰ بنر قیمت ۱۱ ارز مختلف را روی قالب استوری
    با فونت فارسی رندر کرده و به صورت تصویر و فایل برای ادمین‌ها ارسال می‌کند.

۸. parachi-price-updates (parachi_price_updates.py)

  - کارکرد: ارسال بنرهای گرافیکی نرخ ارز به کانال‌ها.
  - گردش‌کار: در ساعت‌های ۱۲:۰۰ و ۲۰:۰۰ بنر قیمت‌ها را با تاریخ و ساعت روز ایجاد
    کرده و به ۱۲ کانال و گروه تلگرامی ارسال می‌کند.

۹. update_handler (scrapper/update_handler.py)

  - کارکرد: اسکرپر و شنودکننده کانال‌های معاملاتی.
  - گردش‌کار: پیام‌های کانال‌های هدف را دریافت کرده، اطلاعات معامله را استخراج
    کرده و به صورت اتوماتیک در سیستم پاراچی ثبت و منتشر می‌کند.

⚡ دستورات سریع مدیریت سرویس‌ها

# استقرار کامل از صفر
/root/bid/deploy.sh

# ساخت کانتینرها (منوی تعاملی یا CLI)
/root/bid/build.sh

# ری‌استارت سرویس‌ها
/root/bid/restart.sh

# متوقف کردن سرویس‌ها
/root/bid/stop.sh

# مشاهده لاگ زنده سرویس‌ها
/root/bid/logs.sh

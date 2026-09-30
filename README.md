# مهارت‌یار — پلتفرم تبادل مهارت و خدمات

پروژهٔ درس برنامه‌نویسی وب با **Django** و **PostgreSQL**.
سامانه‌ای که کاربران در آن مهارت و خدمات خود را ثبت می‌کنند، دیگران آن‌ها را جستجو می‌کنند،
**درخواست تبادل** می‌دهند، از طریق **پیام** گفتگو می‌کنند و در نهایت **مدیر سیستم** تبادل را
تأیید یا رد می‌کند. نتیجهٔ تأییدشده در **تاریخچهٔ تبادل** ثبت می‌شود.

---

## ۱. پشتهٔ فناوری

| بخش | فناوری |
|---|---|
| Backend | Django 5.2 LTS روی Python 3.12 |
| دیتابیس | PostgreSQL 17 |
| فرانت‌اند | Django Templates + Bootstrap 5.3 (RTL) |
| فرم‌ها | فرم‌های بومی Django با کلاس‌های Bootstrap |
| احراز هویت | بک‌اند سفارشی «ایمیل یا موبایل» |
| فایل و تصویر | Pillow |
| فایل‌های استاتیک | WhiteNoise |
| تست | Django TestCase (۹۴ تست) |
| دیپلوی | Gunicorn + WhiteNoise + Docker |

> **چرا بدون React؟** صورت پروژه هیچ نیازی به SPA، API یا احراز هویت توکنی اعلام نکرده بود.
> افزودن React یعنی JWT + CORS + DRF + مدیریت state؛ این‌ها زمان پروژه را می‌بلعند و نمرهٔ بخش
> «کار با Django» را کم می‌کنند. طراحی رابط کاملاً Bootstrap-based است.

---

## ۲. راه‌اندازی سریع

### پیش‌نیازها
- Python 3.12 یا بالاتر
- PostgreSQL 14 یا بالاتر

### گام ۱ — محیط مجازی و وابستگی‌ها

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### گام ۲ — تنظیم متغیرهای محیطی

فایل `.env.example` را به `.env` کپی کنید و مقادیر را پر کنید:

```ini
SECRET_KEY=یک-کلید-تصادفی-طولانی
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=webdan
DB_USER=webdan
DB_PASSWORD=رمز-دیتابیس
DB_HOST=127.0.0.1
DB_PORT=5432
```

برای ساخت کلید تصادفی:

```powershell
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

### گام ۳ — ساخت دیتابیس

```sql
CREATE ROLE webdan LOGIN PASSWORD 'رمز-شما' CREATEDB;
CREATE DATABASE webdan OWNER webdan ENCODING 'UTF8' TEMPLATE template0;
```

### گام ۴ — مهاجرت و دادهٔ نمونه

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
```

### گام ۵ — اجرا

```powershell
python manage.py runserver
```

سایت روی <http://127.0.0.1:8000> و پنل مدیریت روی <http://127.0.0.1:8000/admin/> در دسترس است.

### حساب‌های آمادهٔ نمایش

| نقش | ورود | رمز |
|---|---|---|
| مدیر سیستم | `admin@skillyar.ir` | `Admin#1405` |
| کاربر نمونه | `sara@skillyar.ir` | `Demo#1405` |
| کاربر نمونه | `ali@skillyar.ir` | `Demo#1405` |

---

## ۳. دستورهای پرکاربرد

| دستور | کاربرد |
|---|---|
| `python manage.py runserver` | اجرای سرور توسعه |
| `python manage.py test` | اجرای ۹۴ تست خودکار |
| `python manage.py check` | بررسی سلامت تنظیمات |
| `python manage.py seed_demo` | ساخت دادهٔ نمونه |
| `python manage.py seed_demo --reset` | پاک کردن داده و ساخت مجدد |
| `python manage.py daily_report` | چاپ گزارش روزانه در کنسول |
| `python manage.py daily_report --date 2026-09-30` | گزارش یک روز مشخص |
| `python manage.py collectstatic` | جمع‌آوری فایل‌های استاتیک |
| `python manage.py createsuperuser` | ساخت مدیر ارشد |

---

## ۴. ساختار پروژه

```
webdan/
├── config/                 تنظیمات، نشانی‌های ریشه، WSGI/ASGI
│   ├── settings.py
│   └── urls.py
├── core/                   ابزارهای مشترک
│   ├── views.py            صفحهٔ اصلی
│   ├── forms.py            میکسین Bootstrap برای فرم‌ها
│   ├── decorators.py       admin_required
│   ├── context_processors.py
│   ├── testing.py          کارخانهٔ دادهٔ تست
│   └── templatetags/       تگ‌های صفحه‌بندی و سطح مهارت
├── accounts/               احراز هویت و پروفایل
│   ├── models.py           User (سفارشی) و Profile
│   ├── backends.py         ورود با ایمیل یا موبایل
│   ├── validators.py       اعتبارسنجی رمز با پیام فارسی
│   ├── signals.py          ساخت خودکار Profile
│   └── management/commands/seed_demo.py, daily_report.py
├── skills/                 دسته‌بندی، مهارت، دنبال کردن
│   ├── models.py           Category, Skill, Watch
│   ├── services.py         منطق فیلتر، جستجو و پیشنهاد
│   ├── forms.py
│   └── views.py
├── exchanges/              تبادل، پیام، گزارش، اعلان
│   ├── models.py           Exchange, Message, Report, Notification
│   ├── signals.py          اعلان خودکار تغییر وضعیت
│   ├── forms.py
│   └── views.py
├── dashboard/              پنل مدیریت و گزارش روزانه
│   ├── reports.py          محاسبهٔ آمار
│   ├── forms.py
│   └── views.py
├── templates/
│   ├── base.html           قالب پایه (RTL، فونت وزیرمتن)
│   ├── partials/           navbar، footer، skill_card، pagination، form_field
│   ├── core/               صفحهٔ اصلی
│   ├── accounts/           احراز هویت و پروفایل
│   ├── skills/             فهرست، جزئیات، فرم، حذف
│   ├── exchanges/          تبادل، گفتگو، بررسی، گزارش
│   └── dashboard/          صفحات مدیریت
├── static/css/main.css     دیزاین‌سیستم و توکن‌های رنگ
├── static/js/main.js
├── docs/plans/             سند معماری
├── design-system/          خروجی ابزار طراحی رابط
├── manage.py
└── requirements.txt
```

---

## ۵. مدل‌های داده

| مدل | اپ | نقش |
|---|---|---|
| `User` | accounts | کاربر سفارشی با ایمیل/موبایل، نقش کاربر یا مدیر |
| `Profile` | accounts | شهر، معرفی، آواتار |
| `Category` | skills | دسته‌بندی مهارت‌ها |
| `Skill` | skills | مهارت یا خدمت: عنوان، نوع، دسته‌بندی، سطح ۱ تا ۵، توضیحات، برچسب |
| `Watch` | skills | دنبال کردن مهارت (یکتا برای هر کاربر و مهارت) |
| `Exchange` | exchanges | درخواست تبادل با وضعیت و یادداشت مدیر |
| `Message` | exchanges | پیام‌های داخل هر تبادل |
| `Report` | exchanges | گزارش کاربر دربارهٔ کاربر یا مهارت |
| `Notification` | exchanges | اعلان‌های داخلی |

### گردش وضعیت تبادل

```
ثبت درخواست        → pending
     ↓
مدیر بررسی می‌کند  → admin_review
     ↓
تأیید مدیر         → approved ──→ completed
     ↓
رد مدیر            → rejected  (admin_note اجباری)
```

هر تغییر وضعیت به‌صورت خودکار برای هر دو طرف `Notification` می‌سازد
(سیگنال `post_save` در `exchanges/signals.py`).
پیام‌ها تا پیش از تصمیم نهایی باز می‌مانند.

---

## ۶. نقش‌ها و کنترل دسترسی

| نقش | دسترسی |
|---|---|
| کاربر مهمان | صفحهٔ اصلی، فهرست و جستجوی مهارت‌ها، جزئیات مهارت، ثبت‌نام و ورود |
| کاربر | ثبت و مدیریت مهارت خود، دنبال کردن، درخواست تبادل، پیام، گزارش، پنل شخصی |
| مدیر | تأیید/رد تبادل، مدیریت کاربران و نقش‌ها، مهارت‌ها، دسته‌بندی‌ها، گزارش‌ها، گزارش روزانه |

کنترل دسترسی در سه لایه انجام می‌شود:
1. دکوراتور `@login_required` برای صفحات کاربر
2. دکوراتور `@admin_required` (در `core/decorators.py`) برای پنل مدیریت
3. بررسی مالکیت در ویو: `get_object_or_404(Skill, pk=pk, owner=request.user)`

---

## ۷. قابلیت‌های پیاده‌شده

- **صفحهٔ اصلی** با آمار لحظه‌ای، دسته‌بندی‌ها، تازه‌ترین مهارت‌ها و توضیح چهار قدم کار
- **ثبت‌نام ساده** با ایمیل یا موبایل، اعتبارسنجی رمز با پیام فارسی
- **ورود با ایمیل یا موبایل** (بک‌اند سفارشی)
- **بازیابی رمز عبور** با ایمیل
- **پروفایل شخصی** با ویرایش اطلاعات و آپلود آواتار
- **پروفایل عمومی** کاربران به‌همراه فهرست مهارت‌هایشان
- **مدیریت مهارت‌ها**: ثبت، ویرایش، حذف، فعال/غیرفعال
- **جستجو و فیلتر** بر اساس عنوان، توضیحات، برچسب، دسته‌بندی، نوع، حداقل سطح و شهر
- **پیشنهاد هوشمند**: مهارت‌های هم‌دسته یا هم‌برچسب با مهارت‌های خود کاربر
- **مهارت‌های مشابه** در صفحهٔ جزئیات
- **دنبال کردن** مهارت و فهرست «مهارت‌های دنبال‌شده»
- **درخواست تبادل** با انتخاب مهارت پیشنهادی
- **گفتگوی دوطرفه** داخل هر تبادل
- **اعلان‌ها** با نشانگر در نوار بالا
- **تأیید/رد تبادل توسط مدیر** با یادداشت اجباری برای رد
- **تاریخچهٔ تبادل** شامل موارد تأییدشده و تکمیل‌شده
- **گزارش‌گیری کاربران و مهارت‌ها** با دلیل انتخابی
- **پنل مدیریت** با مدیریت کاربران، نقش‌ها، مهارت‌ها، دسته‌بندی‌ها، تبادل‌ها و گزارش‌ها
- **گزارش روزانه** هم در پنل مدیریت و هم در کنسول
- **رابط کاربری راست‌به‌چپ**، واکنش‌گرا، با رعایت دسترس‌پذیری

---

## ۸. تست‌ها

```powershell
python manage.py test
```

۹۴ تست در چهار اپ نوشته شده است و همگی سبز هستند:

| اپ | پوشش تست |
|---|---|
| `accounts` | ساخت خودکار پروفایل، یکتایی موبایل، ورود با ایمیل و موبایل، ثبت‌نام، اعتبارسنجی، کنترل دسترسی، ویرایش پروفایل |
| `skills` | مدل‌ها، CRUD، مالکیت، جستجو و هر فیلتر، پیشنهاد و مهارت مشابه، دنبال کردن |
| `exchanges` | اعتبارسنجی مدل، سیگنال اعلان، ایجاد درخواست، کنترل دسترسی، پیام، تأیید و رد مدیر، گزارش‌ها |
| `dashboard` | کنترل نقش، مدیریت کاربر/مهارت/دسته‌بندی/گزارش، آمار و گزارش روزانه |

---

## ۹. دیپلوی

### گزینهٔ ۱ — Docker

```bash
docker compose up --build
```

متغیرهای محیطی را در یک فایل `.env` کنار `docker-compose.yml` قرار دهید.

### گزینهٔ ۲ — Render / Railway / VPS

```bash
pip install gunicorn
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

در محیط تولید حتماً `DEBUG=False` بگذارید و `ALLOWED_HOSTS` را با دامنهٔ واقعی تنظیم کنید.

---

## ۱۰. نکات امنیتی رعایت‌شده

- `SECRET_KEY` و اطلاعات دیتابیس فقط در `.env` (در گیت نیست)
- رمزها به‌صورت هش‌شده ذخیره می‌شوند (`set_password` با PBKDF2)
- خروج فقط با درخواست `POST` و توکن CSRF
- توکن CSRF روی تمام فرم‌ها
- کنترل مالکیت روی ویوهای ویرایش و حذف
- حذف حساب خود یا مدیر ارشد توسط مدیر ممنوع است
- محتوا در قالب‌ها escape می‌شود و `X_FRAME_OPTIONS = DENY`
- محدودیت حجم آپلود آواتار (۲ مگابایت)
- وقتی `DEBUG=False` باشد به‌صورت خودکار فعال می‌شوند:
  `SESSION_COOKIE_SECURE`، `CSRF_COOKIE_SECURE`، `SECURE_SSL_REDIRECT`،
  `SECURE_CONTENT_TYPE_NOSNIFF`، `SECURE_REFERRER_POLICY` و تشخیص پروکسی HTTPS

بررسی تنظیمات امنیتی پیش از دیپلوی:

```powershell
python manage.py check --deploy
```

پس از `DEBUG=False` فقط یک هشدار باقی می‌ماند: `SECURE_HSTS_SECONDS` تنظیم نشده است.
این عمدی است — HSTS را باید فقط وقتی مطمئنید سایت همیشه روی HTTPS است فعال کنید.
برای فعال‌سازی، متغیر محیطی `SECURE_HSTS_SECONDS=31536000` را تنظیم کنید.

---

## ۱۱. نگاشت نیازمندی‌های صورت پروژه به پیاده‌سازی

| نیازمندی | کجا |
|---|---|
| صفحهٔ اصلی، مهارت‌های نمایشی، جستجوی سریع | `core/views.py` و `templates/core/home.html` |
| ثبت‌نام با موبایل یا ایمیل، ورود، بازیابی رمز | `accounts/` |
| پروفایل شخصی، اعلان‌ها، تاریخچهٔ تبادل | `accounts/` و `exchanges/` |
| فهرست مهارت‌ها با دسته‌بندی، فیلتر و جستجو | `skills/services.py` و `templates/skills/skill_list.html` |
| صفحهٔ جزئیات مهارت، تبادل، پیام، تأیید | `templates/skills/skill_detail.html` و `exchanges/` |
| پنل مدیریت | `dashboard/` |
| گزارش روزانه | `dashboard/reports.py` و فرمان `daily_report` |
| پیام سیستم (داخلی) | مدل `Message` در `exchanges/` |
| CRUD کاربران و مهارت‌ها (Backend) | `dashboard/views.py` |

سند معماری و جزئیات فازبندی: [`docs/plans/00-architecture.md`](docs/plans/00-architecture.md)

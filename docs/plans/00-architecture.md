# پلتفرم تبادل مهارت و خدمات — سند معماری و نقشه راه

> سند مرجع کل پروژه. هر فاز به یک deliverable قابل تست ختم می‌شود و بعد از آن commit می‌شود.

## ۱. هدف پروژه

سامانه‌ای که کاربران در آن **مهارت و خدمات خود را ثبت می‌کنند**، دیگران آن‌ها را **جستجو و فیلتر** می‌کنند،
**درخواست تبادل** می‌دهند، از طریق **پیام** گفتگو می‌کنند و در نهایت **مدیر سیستم** تبادل را **تأیید یا رد** می‌کند.
نتیجهٔ تأییدشده در **تاریخچهٔ تبادل** کاربران ثبت می‌شود.

## ۲. بازیگران و دسترسی

| بازیگر | دسترسی |
|---|---|
| کاربر مهمان (Guest) | صفحهٔ اصلی، فهرست مهارت‌ها، جستجو، جزئیات مهارت، ثبت‌نام/ورود |
| کاربر (User) | همهٔ بالا + ثبت مهارت، ویرایش/حذف مهارت خودش، دنبال کردن، درخواست تبادل، پیام، گزارش |
| مدیر (Admin) | همهٔ بالا + تأیید/رد تبادل، مدیریت کاربران، دسته‌بندی‌ها، گزارش‌ها، آمار و گزارش روزانه |

پیاده‌سازی: `is_staff`/`is_superuser` برای مدیر، `@staff_member_required` روی ویوهای مدیریتی.
نیازی به `django.contrib.auth.models.Group` نیست.

## ۳. پشتهٔ فناوری

| بخش | انتخاب | دلیل |
|---|---|---|
| Backend | Django 5.2 LTS (Python 3.12) | در سرفصل دوره هست؛ نسخهٔ LTS |
| دیتابیس | PostgreSQL 17 | در سرفصل دوره هست؛ مناسب دیپلوی |
| فرانت | Django Templates + Bootstrap 5.3 (CDN) | بدون درگیری CORS/JWT؛ تحویل سریع و مطمئن |
| فرم‌ها | `django-bootstrap5` + ` crispy-forms` | رندر و اعتبارسنجی استاندارد |
| آپلود | Pillow | آواتار |
| تنظیمات | `python-dotenv` | جداسازی SECRET_KEY و کارنامهٔ دیتابیس |
| استاتیک | `whitenoise` | سرو فایل‌های استاتیک بدون Nginx |
| دیپلوی | Docker + Render/Railway | `gunicorn` + `whitenoise` + `DEBUG=False` |

**چرا بدون React در نسخهٔ اصلی:** صورت پروژه هیچ نیازی به SPA/API/احراز هویت توکنی اعلام نکرده است.
افزودنٔ React یعنی JWT + CORS + DRF + مدیریت state؛ این‌ها زمان پروژه را می‌بلعند و نمرهٔ بخش
«کار با Django» را کم می‌کنند. React فقط به‌عنوان **افزونهٔ اختیاری** برای صفحهٔ جستجوی زنده نگه داشته می‌شود.

## ۴. ساختار پوشه‌ها

```
webdan/
├── manage.py
├── requirements.txt
├── .env                  # محلی، در گیت نیست
├── .env.example
├── .gitignore
├── README.md
├── config/               # settings, urls, wsgi, asgi
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/             # ثبت‌نام، ورود، پروفایل
│   ├── models.py         # Profile
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── signals.py        # ساخت خودکار Profile هنگام ساخت User
│   ├── management/commands/seed_demo.py
│   └── tests/
├── skills/               # Category, Skill, Watch
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests/
├── exchanges/            # Exchange, Message, Report, Notification
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests/
├── dashboard/            # ویوهای مدیریتی مدیر + گزارش روزانه
│   ├── views.py
│   ├── urls.py
│   ├── reports.py        # منطق محاسبهٔ آمار روزانه
│   └── tests/
├── templates/
│   ├── base.html
│   ├── partials/         # navbar, footer, skill_card, pagination
│   ├── accounts/
│   ├── skills/
│   ├── exchanges/
│   └── dashboard/
├── static/css|js|img/
├── media/                # آواتارها (در گیت نیست)
└── docs/plans/
```

**قانون:** هر فایل یک مسئولیت. مدل‌ها در `models.py`، فقط منطق نمایش در `views.py`، فقط فرم در `forms.py`.

## ۵. مدل‌های داده

### accounts.Profile
| فیلد | نوع | توضیح |
|---|---|---|
| `user` | OneToOne → User | `related_name="profile"` |
| `phone` | CharField(20) | یکتا، اختیاری — ورود با موبایل |
| `city` | CharField(64) | برای فیلتر |
| `bio` | TextField(500) | توضیح کوتاه |
| `avatar` | ImageField | `media/avatars/` |
| `created_at` | DateTime | |

سیگنال `post_save` روی `User` → ساخت خودکار `Profile`.

### skills.Category
`title` (یکتا)، `slug` (یکتا، `SlugField`)، `description`، `created_at`

### skills.Skill  — «مهارت/خدمت»
| فیلد | نوع | توضیح |
|---|---|---|
| `owner` | FK → User | `related_name="skills"` |
| `title` | CharField(120) | عنوان |
| `type` | CharField | `skill` (مهارت) یا `service` (خدمت) |
| `category` | FK → Category | `related_name="skills"` |
| `level` | PositiveSmallInteger | ۱ تا ۵، `choices=LEVELS` |
| `description` | TextField | توضیحات |
| `tags` | CharField(200) | برچسب‌ها، جدا شده با کاما |
| `is_active` | Boolean | خاموش/روشن کردن آگهی |
| `created_at` | DateTime | |

- `Meta.ordering = ["-created_at"]`
- `__str__` → `title`
- property `get_absolute_url()` → `/skills/<pk>/slug/`
- property `tags_list` → لیست تگ‌ها
- ایندکس روی `title` و `category`

### skills.Watch  — «مهارت‌های مشاهده‌شده / علاقه‌مندی»
| فیلد | نوع |
|---|---|
| `user` | FK → User |
| `skill` | FK → Skill |
| `created_at` | DateTime |

`Meta.unique_together = [("user", "skill")]` → دنبال کردن دوباره خطا نمی‌دهد.

### exchanges.Exchange  — «درخواست تبادل»
| فیلد | نوع | توضیح |
|---|---|---|
| `requester` | FK → User | فرستندهٔ درخواست |
| `provider` | FK → User | صاحب مهارت |
| `skill` | FK → Skill | مهارت مورد تقاضا |
| `offered_skill` | FK → Skill | nullable — مهارتی که کاربر در ازایش پیشنهاد می‌دهد |
| `title` | CharField(120) | |
| `description` | TextField | |
| `status` | CharField | `pending / admin_review / approved / rejected / completed` |
| `admin_note` | TextField | دلیل رد یا توضیح مدیر |
| `reviewed_by` | FK → User (null) | مدیر بررسی‌کننده |
| `reviewed_at` | DateTime (null) | |
| `created_at` | DateTime | |

قواعد:
- `requester != provider` (در `clean()` اعتبارسنجی شود)
- تغییر وضعیت → ساخت `Notification` برای طرف مقابل (سیگنال `post_save`)
- `Meta.ordering = ["-created_at"]`

### exchanges.Message — «پیام‌های سیستم (داخلی)»
| فیلد | نوع |
|---|---|
| `exchange` | FK → Exchange, `related_name="messages"` |
| `sender` | FK → User |
| `body` | TextField (حداکثر ۲۰۰۰) |
| `is_read` | Boolean |
| `created_at` | DateTime |

دسترسی: فقط `exchange.requester`، `exchange.provider` و مدیر.

### exchanges.Report — «گزارش‌ها»
| فیلد | نوع |
|---|---|
| `reporter` | FK → User |
| `target_user` | FK → User (null) |
| `target_skill` | FK → Skill (null) |
| `reason` | CharField (choices: spam, abuse, wrong_info, other) |
| `description` | TextField |
| `status` | CharField (`open / resolved`) |
| `handled_by` | FK → User (null) |
| `created_at` | DateTime |

حداقل یکی از `target_user`/`target_skill` باید پر باشد.

### exchanges.Notification — «اعلان‌ها»
`user`، `text`، `url`، `is_read`، `created_at`
نمایش به‌صورت badge در navbar + صفحهٔ «اعلان‌های من».

## ۶. نمودار جریان تبادل

```
ثبت درخواست        → pending
   ↓
مدیر مشاهده می‌کند → admin_review
   ↓
تأیید مدیر         → approved ──→ completed (توسط یکی از طرفین)
   ↓
رد مدیر            → rejected  (admin_note اجباری)
   ↓
Notification برای هر دو طرف
پیام‌ها فقط تا قبل از approved/rejected باز است
```

## ۷. نگاشت نیازمندی‌ها به فازها

| نیازمندی صورت پروژه | فاز |
|---|---|
| Home Page، پرچربرگ، معرفی مهارت، جستجوی سریع | ۳ |
| ثبت‌نام با موبایل/ایمیل، ورود، رمز عبور | ۴ |
| پروفایل شخصی، اطلاعات، مهارت‌های مشاهده‌شده | ۵، ۷ |
| تاریخچهٔ تبادل | ۱۰ |
| فهرست مهارت‌ها + دسته‌بندی/فیلتر/جستجو | ۶ |
| صفحهٔ جزئیات مهارت + اطلاعات کامل | ۷ |
| درخواست تبادل | ۸ |
| پیام‌ها و اعلان‌ها | ۹ |
| تأیید تبادل توسط مدیر | ۱۰ |
| مدیریت کاربران، سطح دسترسی، حذف | ۱۱ |
| مدیریت مهارت‌ها (حذف/تأیید/بررسی)، دسته‌بندی | ۱۱ |
| مدیریت درخواست‌های تبادل، گزارش‌های فعال | ۱۰، ۱۱ |
| شمارش کاربر/مهارت/تبادل | ۱۱ |
| گزارش روزانه | ۱۱ |
| CRUD کاربران و مهارت‌ها (Backend) | ۵، ۶، ۱۱ |
| ثبت‌نام/ورود (Backend) | ۴ |
| نمایش نقش کاربر برای مدیر | ۱۱ |
| لینک ارتباط پشتیبانی | ۳ (فوتر) |

## ۸. فازبندی اجرا

هر فاز: کد → تست → اجرا → تأیید → commit.

| فاز | محتوا | خروجی قابل تست |
|---|---|---|
| **۱** | venv، Django، PostgreSQL، `.env`، git، requirements | `manage.py check` بدون خطا، اتصال DB |
| **۲** | اپ‌ها + تمام مدل‌ها + migration + admin | `manage.py check`, `migrate`, admin قابل استفاده |
| **۳** | قالب پایه Bootstrap، استاتیک، Home | صفحهٔ اصلی رندر می‌شود |
| **۴** | ثبت‌نام/ورود/خروج/رمز | ثبت‌نام کاربر جدید کار می‌کند |
| **۵** | پروفایل + مهارت‌های من | ویرایش پروفایل و آپلود آواتار |
| **۶** | CRUD مهارت + فهرست + فیلتر + جستجو | ثبت و جستجوی مهارت |
| **۷** | جزئیات مهارت + watch + مشابه | صفحهٔ جزئیات و دنبال کردن |
| **۸** | درخواست تبادل | ثبت درخواست و دیدن لیست‌ها |
| **۹** | پیام + اعلان | گفتگوی دوطرفه در تبادل |
| **۱۰** | تأیید/رد مدیر + تاریخچه | چرخهٔ کامل تأیید |
| **۱۱** | گزارش‌ها + پنل مدیر + گزارش روزانه | آمار و گزارش‌ها در پنل مدیر |
| **۱۲** | seed دادهٔ نمونه + تست‌ها | `manage.py test` سبز، دادهٔ نمایشی |
| **۱۳** | README، Docker، دیپلوی، جمع‌بندی | تحویل نهایی |

## ۹. دستورهای توسعه

```powershell
# فعال‌سازی
.\.venv\Scripts\Activate.ps1

# اجرا
python manage.py runserver

# تست
python manage.py test

# بررسی
python manage.py check

# دادهٔ نمونه
python manage.py seed_demo

# گزارش روزانه (در کنسول)
python manage.py daily_report
```

## ۱۰. قوانین سراسری

- `SECRET_KEY` و اطلاعات دیتابیس **فقط** در `.env`. `.env.example` با مقدار خالی در گیت.
- در `.gitignore`: `.venv/`, `.env`, `__pycache__/`, `db.sqlite3`, `media/`, `staticfiles/`
- هر ویوی حساس: چک احراز هویت + چک مالکیت + چک نقش مدیر.
- هر مدل `__str__` دارد. هر ویوی فهرست `paginate_by = 12`.
- متن‌های فارسی، جهت صفحه `rtl` و فونت Vazirmatn.
- بدون کامنت بی‌مورد در کد؛ فقط کامنت برای «چرا»، نه «چه».
- commit بعد از هر فاز با پیام کوتاه انگلیسی.

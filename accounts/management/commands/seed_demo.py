"""ساخت دادهٔ نمونه برای توسعه و نمایش پروژه.

اجرا:  python manage.py seed_demo          (افزودن به داده‌های موجود)
        python manage.py seed_demo --reset  (پاک کردن همه و ساخت از نو)
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from exchanges.models import Exchange, ExchangeStatus, Message, Notification
from skills.models import Category, Skill, SkillType

User = get_user_model()

DEMO_PASSWORD = "Demo#1405"

CATEGORIES = [
    ("برنامه‌نویسی و توسعه وب", "آموزش و اجرای پروژه‌های نرم‌افزاری"),
    ("طراحی گرافیک", "لوگو، بنر، هویت بصری"),
    ("مدیریت و کسب‌وکار", "حسابداری، بازاریابی، برنامه‌ریزی"),
    ("زبان و ترجمه", "آموزش و ترجمهٔ زبان"),
    ("تولید محتوا", "نویسندگی، ویدیو، تدوین"),
    ("فنی و تعمیرات", "تعمیرات و خدمات فنی"),
]

USERS = [
    ("sara@skillyar.ir", "سارا محمدی", "09121110001", "طراح گرافیک با ۶ سال سابقه"),
    ("ali@skillyar.ir", "علی رضایی", "09121110002", "برنامه‌نویس پایتون و جنگو"),
    ("maryam@skillyar.ir", "مریم حسینی", "09121110003", "مدرس زبان انگلیسی"),
    ("reza@skillyar.ir", "رضا کاظمی", "09121110004", "تولیدکنندهٔ محتوای ویدیویی"),
    ("niloofar@skillyar.ir", "نیلوفر شریفی", "09121110005", "حسابدار و مشاور مالی"),
    ("amir@skillyar.ir", "امیر نجفی", "09121110006", "تکنسین برق و تعمیرات"),
]

SKILLS = [
    ("sara@skillyar.ir", "طراحی لوگو مینیمال", SkillType.SERVICE, "طراحی گرافیک", 4,
     "طراحی لوگو مینیمال و مدرن برای کسب‌وکار شما در کمتر از ۴۸ ساعت.", "لوگو, برندینگ, حداقل"),
    ("sara@skillyar.ir", "آموزش فتوشاپ از صفر", SkillType.SKILL, "طراحی گرافیک", 5,
     "آموزش کامل فتوشاپ از ابتدا تا تسلط بر ابزارهای حرفه‌ای طراحی.", "فتوشاپ, آموزش, گرافیک"),
    ("ali@skillyar.ir", "آموزش پایتون از صفر", SkillType.SKILL, "برنامه‌نویسی و توسعه وب", 5,
     "آموزش پایتون از مبانی تا نوشتن پروژه‌های واقعی، همراه با تمرین.", "پایتون, آموزش, برنامه‌نویسی"),
    ("ali@skillyar.ir", "توسعه وب با جنگو", SkillType.SKILL, "برنامه‌نویسی و توسعه وب", 4,
     "آموزش جنگو و ساخت وب‌سایت کامل با دیتابیس و پنل مدیریت.", "جنگو, وب, پایتون"),
    ("ali@skillyar.ir", "رفع باگ پروژه‌های پایتون", SkillType.SERVICE, "برنامه‌نویسی و توسعه وب", 4,
     "بررسی و رفع خطاهای پروژه‌های پایتونی شما به‌صورت ریموت.", "پایتون, دیباگ, خدمات"),
    ("maryam@skillyar.ir", "آموزش مکالمهٔ انگلیسی", SkillType.SKILL, "زبان و ترجمه", 5,
     "آموزش مکالمهٔ انگلیسی برای سطح متوسط با جلسات آنلاین.", "انگلیسی, زبان, مکالمه"),
    ("maryam@skillyar.ir", "ترجمهٔ مقالهٔ علمی", SkillType.SERVICE, "زبان و ترجمه", 4,
     "ترجمهٔ تخصصی مقالات علمی با رعایت اصطلاحات فنی.", "ترجمه, انگلیسی, مقاله"),
    ("reza@skillyar.ir", "تدوین ویدیوی یوتیوب", SkillType.SERVICE, "تولید محتوا", 4,
     "تدوین ویدیوی یوتیوب با زیرنویس و افکت صوتی.", "ویدیو, تدوین, یوتیوب"),
    ("reza@skillyar.ir", "نویسندگی محتوای سایت", SkillType.SKILL, "تولید محتوا", 3,
     "نویسندگی محتوای سئو شده برای وب‌سایت‌ها و فروشگاه‌های اینترنتی.", "محتوا, سئو, نوشتن"),
    ("niloofar@skillyar.ir", "مشاورهٔ مالی و مالیاتی", SkillType.SERVICE, "مدیریت و کسب‌وکار", 5,
     "مشاورهٔ مالیاتی و تنظیم دفاتر مالی برای کسب‌وکارهای کوچک.", "مالی, مالیات, مشاوره"),
    ("niloofar@skillyar.ir", "حسابداری پیشرفته", SkillType.SKILL, "مدیریت و کسب‌وکار", 4,
     "آموزش حسابداری پیشرفته و کار با نرم‌افزار سپیدار.", "حسابداری, آموزش, مالی"),
    ("amir@skillyar.ir", "تعمیرات برق ساختمان", SkillType.SERVICE, "فنی و تعمیرات", 4,
     "بررسی و تعمیر سیم‌کشی و تأسیسات برقی ساختمان.", "برق, تعمیرات, فنی"),
    ("amir@skillyar.ir", "نصب و سرویس کولر گازی", SkillType.SERVICE, "فنی و تعمیرات", 3,
     "نصب، سرویس و شارژ گاز کولرهای اسپلیت.", "کولر, سرویس, فنی"),
]

EXCHANGES = [
    ("ali@skillyar.ir", "sara@skillyar.ir", "طراحی لوگو مینیمال", "آموزش پایتون از صفر",
     "یادگیری پایتون در ازای طراحی لوگو برای پروژهٔ شخصی‌ام",
     ExchangeStatus.APPROVED),
    ("maryam@skillyar.ir", "ali@skillyar.ir", "توسعه وب با جنگو", "ترجمهٔ مقالهٔ علمی",
     "نیاز به ترجمهٔ چند مقالهٔ فنی دارم، در ازای آموزش جنگو", ExchangeStatus.PENDING),
    ("reza@skillyar.ir", "sara@skillyar.ir", "آموزش فتوشاپ از صفر", "تدوین ویدیوی یوتیوب",
     "آموزش فتوشاپ می‌خواهم و در ازایش ویدیوی آموزشی می‌سازم", ExchangeStatus.COMPLETED),
]


class Command(BaseCommand):
    help = "ساخت دادهٔ نمونهٔ کاربران، مهارت‌ها و درخواست‌های تبادل."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="همهٔ داده‌های کاربران، مهارت‌ها و تبادلها را پاک می‌کند.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        if options["reset"]:
            self.stdout.write("پاک کردن داده‌های قبلی...")
            Notification.objects.all().delete()
            Message.objects.all().delete()
            Exchange.objects.all().delete()
            Skill.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(email__endswith="@skillyar.ir").exclude(is_superuser=True).delete()

        categories = self._create_categories()
        users = self._create_users()
        self._create_skills(users, categories)
        self._create_exchanges(users)

        self.stdout.write(self.style.SUCCESS("دادهٔ نمونه با موفقیت ساخته شد."))
        self.stdout.write("  رمز همهٔ کاربران نمونه: " + DEMO_PASSWORD)
        self.stdout.write("  ورود مدیر: admin@skillyar.ir / Admin#1405")

    def _create_categories(self) -> dict[str, Category]:
        result = {}
        for title, description in CATEGORIES:
            category, _ = Category.objects.get_or_create(
                title=title, defaults={"description": description}
            )
            result[title] = category
        self.stdout.write(f"  دسته‌بندی‌ها: {len(result)}")
        return result

    def _create_users(self) -> dict[str, User]:
        result = {}
        for email, full_name, phone, bio in USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"full_name": full_name, "phone": phone, "role": "user"},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            profile = user.profile
            profile.bio = bio
            profile.save()
            result[email] = user
        self.stdout.write(f"  کاربران: {len(result)}")
        return result

    def _create_skills(self, users: dict[str, User], categories: dict[str, Category]) -> None:
        for owner_email, title, skill_type, category_title, level, description, tags in SKILLS:
            owner = users[owner_email]
            Skill.objects.update_or_create(
                owner=owner,
                title=title,
                defaults={
                    "type": skill_type,
                    "category": categories[category_title],
                    "level": level,
                    "description": description,
                    "tags": tags,
                    "is_active": True,
                },
            )
        self.stdout.write(f"  مهارت‌ها: {Skill.objects.count()}")

    def _create_exchanges(self, users: dict[str, User]) -> None:
        for requester_email, provider_email, skill_title, offered_title, description, status in EXCHANGES:
            requester = users[requester_email]
            provider = users[provider_email]
            skill = Skill.objects.filter(owner=provider, title=skill_title).first()
            offered = Skill.objects.filter(owner=requester, title=offered_title).first()
            if not skill:
                continue
            exchange, created = Exchange.objects.get_or_create(
                requester=requester,
                provider=provider,
                skill=skill,
                title=f"درخواست {skill_title}",
                defaults={
                    "offered_skill": offered,
                    "description": description,
                    "status": status,
                    "reviewed_by": User.objects.filter(is_superuser=True).first(),
                    "reviewed_at": timezone.now() if status != ExchangeStatus.PENDING else None,
                },
            )
            if created and exchange.can_message:
                Message.objects.create(
                    exchange=exchange,
                    sender=requester,
                    body="سلام، برای تبادل تمایل دارم. چه زمانی برای صحبت مناسب است؟",
                )
                Message.objects.create(
                    exchange=exchange,
                    sender=provider,
                    body="سلام، خوشحال می‌شوم. آخرین هفته بعد از ساعت ۱۸ در دسترس‌ام.",
                )
        self.stdout.write(f"  درخواست‌های تبادل: {Exchange.objects.count()}")

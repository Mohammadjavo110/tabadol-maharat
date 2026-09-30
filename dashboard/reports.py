"""محاسبهٔ آمار سامانه و گزارش روزانه."""

from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from exchanges.models import Exchange, ExchangeStatus, Message, Report, ReportStatus
from skills.models import Category, Skill

User = get_user_model()


def _day_bounds(day):
    start = timezone.make_aware(datetime.combine(day, time.min), timezone.get_current_timezone())
    return start, start + timedelta(days=1)


def daily_stats(day=None) -> dict:
    """آمار فعالیت‌های یک روز مشخص."""
    day = day or timezone.localdate()
    start, end = _day_bounds(day)
    in_range = {"created_at__gte": start, "created_at__lt": end}

    return {
        "date": day,
        "new_users": User.objects.filter(
            date_joined__gte=start, date_joined__lt=end
        ).count(),
        "new_skills": Skill.objects.filter(**in_range).count(),
        "new_exchanges": Exchange.objects.filter(**in_range).count(),
        "new_messages": Message.objects.filter(**in_range).count(),
        "new_reports": Report.objects.filter(**in_range).count(),
        "reviewed_today": Exchange.objects.filter(
            reviewed_at__gte=start, reviewed_at__lt=end
        ).count(),
        "approved_today": Exchange.objects.filter(
            reviewed_at__gte=start,
            reviewed_at__lt=end,
            status__in=[ExchangeStatus.APPROVED, ExchangeStatus.COMPLETED],
        ).count(),
    }


def totals() -> dict:
    """آمار کلی سامانه."""
    return {
        "users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "staff_users": User.objects.filter(is_staff=True).count(),
        "skills": Skill.objects.count(),
        "active_skills": Skill.objects.filter(is_active=True).count(),
        "inactive_skills": Skill.objects.filter(is_active=False).count(),
        "categories": Category.objects.count(),
        "exchanges": Exchange.objects.count(),
        "approved_exchanges": Exchange.objects.filter(
            status__in=[ExchangeStatus.APPROVED, ExchangeStatus.COMPLETED]
        ).count(),
        "pending_exchanges": Exchange.objects.filter(
            status__in=[ExchangeStatus.PENDING, ExchangeStatus.ADMIN_REVIEW]
        ).count(),
        "messages": Message.objects.count(),
        "open_reports": Report.objects.filter(status=ReportStatus.OPEN).count(),
        "all_reports": Report.objects.count(),
    }


def top_skills_by_watches(limit: int = 5):
    return (
        Skill.objects.filter(is_active=True)
        .annotate(total_watches=Count("watches", distinct=True))
        .order_by("-total_watches")[:limit]
    )


def top_categories(limit: int = 5):
    return (
        Category.objects.annotate(
            skills_count=Count("skills", distinct=True),
            active_skills=Count("skills", filter=Q(skills__is_active=True), distinct=True),
        )
        .order_by("-skills_count")[:limit]
    )


def busiest_users(limit: int = 5):
    """کاربرانی که بیشترین درخواست تبادل داده‌اند."""
    return (
        User.objects.filter(sent_exchanges__isnull=False)
        .annotate(exchange_count=Count("sent_exchanges", distinct=True))
        .order_by("-exchange_count")[:limit]
    )


DAILY_REPORT_LABELS = [
    ("new_users", "کاربر جدید"),
    ("new_skills", "مهارت/خدمت جدید"),
    ("new_exchanges", "درخواست تبادل جدید"),
    ("new_messages", "پیام جدید"),
    ("reviewed_today", "درخواست بررسی‌شده"),
    ("approved_today", "تبادل تأییدشده"),
    ("new_reports", "گزارش جدید"),
]


def format_daily_report(day=None) -> str:
    """گزارش روزانه به‌صورت متن قابل چاپ."""
    stats = daily_stats(day)
    overall = totals()
    persian_date = timezone.localtime(timezone.now()).strftime("%Y/%m/%d")

    lines = [
        "=" * 46,
        "گزارش روزانه سامانه تبادل مهارت و خدمات",
        f"تاریخ: {persian_date}",
        "=" * 46,
        "",
        "— آمار امروز —",
    ]
    for key, label in DAILY_REPORT_LABELS:
        lines.append(f"  {label}: {stats[key]}")

    lines += ["", "— آمار کل سامانه —"]
    lines += [
        f"  کل کاربران: {overall['users']} (فعال: {overall['active_users']})",
        f"  مدیر سیستم: {overall['staff_users']}",
        f"  کل مهارت‌ها: {overall['skills']} (فعال: {overall['active_skills']})",
        f"  دسته‌بندی‌ها: {overall['categories']}",
        f"  کل تبادلها: {overall['exchanges']} (تأییدشده: {overall['approved_exchanges']})",
        f"  در انتظار بررسی: {overall['pending_exchanges']}",
        f"  پیام‌ها: {overall['messages']}",
        f"  گزارش‌های باز: {overall['open_reports']}",
        "=" * 46,
    ]
    return "\n".join(lines)

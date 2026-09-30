"""چاپ گزارش روزانهٔ سامانه در کنسول.

اجرا:  python manage.py daily_report
"""

from django.core.management.base import BaseCommand

from dashboard.reports import daily_stats, format_daily_report, totals


class Command(BaseCommand):
    help = "گزارش روزانهٔ فعالیت سامانه را در کنسول چاپ می‌کند."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--date",
            dest="day",
            help="تاریخ گزارش به فرمت YYYY-MM-DD (پیش‌فرض: امروز)",
        )

    def handle(self, *args, **options) -> None:
        from datetime import date

        day = None
        if options.get("day"):
            try:
                day = date.fromisoformat(options["day"])
            except ValueError:
                self.stderr.write(self.style.ERROR("قالب تاریخ نامعتبر است. نمونهٔ درست: 2026-09-30"))
                return

        self.stdout.write(format_daily_report(day))
        self.stdout.write("")

        stats = daily_stats(day)
        if not any(
            stats[key] for key in ("new_users", "new_skills", "new_exchanges", "new_messages")
        ):
            self.stdout.write(self.style.WARNING("امروز فعالیت جدیدی ثبت نشده است."))
        else:
            self.stdout.write(self.style.SUCCESS("گزارش با موفقیت تولید شد."))

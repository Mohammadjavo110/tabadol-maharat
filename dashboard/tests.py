from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from io import StringIO

from core.testing import make_admin, make_category, make_skill, make_user
from dashboard.reports import daily_stats, format_daily_report, totals
from exchanges.models import Exchange, ExchangeStatus, Report, ReportReason, ReportStatus
from skills.models import Category as make_category_model
from skills.models import Skill


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.user = make_user(email="user@test.ir")
        self.paths = [
            reverse("dashboard:home"),
            reverse("dashboard:users"),
            reverse("dashboard:skills"),
            reverse("dashboard:categories"),
            reverse("dashboard:exchanges"),
            reverse("dashboard:reports"),
            reverse("dashboard:daily_report"),
        ]

    def test_anonymous_redirected(self):
        for path in self.paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 302)

    def test_regular_user_blocked(self):
        self.client.force_login(self.user)
        for path in self.paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, reverse("accounts:dashboard"))

    def test_staff_has_access(self):
        self.client.force_login(self.admin)
        for path in self.paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)


class UserManagementTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.user = make_user(email="user@test.ir", full_name="کاربر عادی")
        self.url = reverse("dashboard:users")

    def test_toggle_active(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:user_toggle_active", args=[self.user.pk]))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_cannot_deactivate_self(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:user_toggle_active", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_change_role(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:user_change_role", args=[self.user.pk]), {"role": "admin"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "admin")
        self.assertTrue(self.user.is_staff)

    def test_cannot_delete_superuser(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:user_delete", args=[self.admin.pk]))
        self.assertEqual(type(self.admin).objects.filter(pk=self.admin.pk).count(), 1)

    def test_delete_user_cascades(self):
        category = make_category()
        make_skill(self.user, category)
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:user_delete", args=[self.user.pk]))
        self.assertFalse(type(self.user).objects.filter(pk=self.user.pk).exists())
        self.assertEqual(Skill.objects.count(), 0)


class SkillManagementTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.owner = make_user(email="owner@test.ir")
        self.skill = make_skill(self.owner, make_category())

    def test_toggle_skill_active(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:skill_toggle_active", args=[self.skill.pk]))
        self.skill.refresh_from_db()
        self.assertFalse(self.skill.is_active)

    def test_search_skills(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:skills"), {"q": "پایتون"})
        self.assertContains(response, self.skill.title)


class CategoryManagementTests(TestCase):
    def setUp(self):
        self.admin = make_admin()

    def test_create_category(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("dashboard:categories"),
            {"title": "ووکال و موسیقی", "description": "آموزش و اجرای موسیقی"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            make_category_model.objects.filter(title="ووکال و موسیقی").exists()
        )

    def test_short_category_title_rejected(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("dashboard:categories"), {"title": "ab"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(make_category_model.objects.filter(title="ab").exists())

    def test_edit_category(self):
        category = make_category("قدیمی")
        self.client.force_login(self.admin)
        self.client.post(
            reverse("dashboard:category_edit", args=[category.pk]),
            {"title": "جدید", "description": "توضیح"},
        )
        category.refresh_from_db()
        self.assertEqual(category.title, "جدید")

    def test_delete_category_removes_skills(self):
        category = make_category("حذف‌شونده")
        make_skill(make_user(email="o@test.ir"), category)
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:category_delete", args=[category.pk]))
        self.assertEqual(Skill.objects.count(), 0)


class ReportManagementTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.reporter = make_user(email="reporter@test.ir")
        self.report = Report.objects.create(
            reporter=self.reporter,
            target_user=self.reporter,
            reason=ReportReason.ABUSE,
            description="رفتار نامناسب کاربر در گفتگو.",
        )

    def test_open_reports_listed_by_default(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:reports"))
        self.assertContains(response, "رفتار نامناسب")

    def test_resolve_report(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("dashboard:report_update", args=[self.report.pk]), {"action": "resolve"}
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.RESOLVED)
        self.assertEqual(self.report.handled_by, self.admin)

    def test_reopen_report(self):
        self.report.status = ReportStatus.RESOLVED
        self.report.save()
        self.client.force_login(self.admin)
        self.client.post(
            reverse("dashboard:report_update", args=[self.report.pk]), {"action": "reopen"}
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.OPEN)


class DailyReportTests(TestCase):
    def setUp(self):
        self.provider = make_user(email="p@test.ir")
        self.requester = make_user(email="r@test.ir")
        self.skill = make_skill(self.provider, make_category())
        Exchange.objects.create(
            requester=self.requester,
            provider=self.provider,
            skill=self.skill,
            title="درخواست",
            description="توضیحات کامل درخواست برای بررسی توسط مدیریت.",
        )

    def test_totals_reflect_data(self):
        result = totals()
        self.assertEqual(result["users"], 2)
        self.assertEqual(result["skills"], 1)
        self.assertEqual(result["exchanges"], 1)
        self.assertEqual(result["pending_exchanges"], 1)

    def test_daily_stats_keys_present(self):
        stats = daily_stats()
        for key in (
            "new_users",
            "new_skills",
            "new_exchanges",
            "new_messages",
            "approved_today",
        ):
            self.assertIn(key, stats)

    def test_formatted_report_contains_totals(self):
        text = format_daily_report()
        self.assertIn("گزارش روزانه", text)
        self.assertIn("کل کاربران", text)

    def test_management_command_runs(self):
        out = StringIO()
        call_command("daily_report", stdout=out)
        self.assertIn("گزارش روزانه", out.getvalue())


class AdminExchangeListTests(TestCase):
    def test_filter_by_status(self):
        admin = make_admin()
        provider = make_user(email="p@test.ir")
        requester = make_user(email="r@test.ir")
        skill = make_skill(provider, make_category())
        Exchange.objects.create(
            requester=requester,
            provider=provider,
            skill=skill,
            title="درخواست تأییدشده",
            description="توضیحات کامل درخواست برای بررسی توسط مدیریت.",
            status=ExchangeStatus.APPROVED,
        )
        client = self.client
        client.force_login(admin)
        response = client.get(reverse("dashboard:exchanges"), {"status": "approved"})
        self.assertContains(response, "درخواست تأییدشده")

        response = client.get(reverse("dashboard:exchanges"), {"status": "pending"})
        self.assertNotContains(response, "درخواست تأییدشده")

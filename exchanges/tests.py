from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.testing import make_admin, make_category, make_skill, make_user
from exchanges.models import Exchange, ExchangeStatus, Message, Notification, Report, ReportReason
from skills.models import Skill


class ExchangeModelTests(TestCase):
    def setUp(self):
        self.provider = make_user(email="provider@test.ir")
        self.requester = make_user(email="requester@test.ir")
        self.category = make_category()
        self.skill = make_skill(self.provider, self.category)

    def _make(self, **extra):
        defaults = {
            "requester": self.requester,
            "provider": self.provider,
            "skill": self.skill,
            "title": "درخواست تبادل",
            "description": "توضیحات کامل درخواست برای بررسی اعتبارسنجی.",
        }
        defaults.update(extra)
        return Exchange.objects.create(**defaults)

    def test_requester_cannot_equal_provider(self):
        exchange = Exchange(
            requester=self.provider,
            provider=self.provider,
            skill=self.skill,
            title="تست",
            description="توضیحات کافی برای عبور از اعتبارسنجی.",
        )
        with self.assertRaises(ValidationError):
            exchange.full_clean()

    def test_cannot_request_own_skill(self):
        exchange = Exchange(
            requester=self.provider,
            provider=self.requester,
            skill=self.skill,
            title="تست",
            description="توضیحات کافی برای عبور از اعتبارسنجی.",
        )
        with self.assertRaises(ValidationError):
            exchange.full_clean()

    def test_offered_skill_must_belong_to_requester(self):
        foreign = make_skill(self.provider, self.category, title="مهارت دیگر")
        exchange = Exchange(
            requester=self.requester,
            provider=self.provider,
            skill=self.skill,
            offered_skill=foreign,
            title="تست",
            description="توضیحات کافی برای عبور از اعتبارسنجی.",
        )
        with self.assertRaises(ValidationError):
            exchange.full_clean()

    def test_can_message_before_decision(self):
        exchange = self._make()
        self.assertTrue(exchange.can_message)
        self.assertFalse(exchange.is_final)

    def test_messages_closed_after_rejection(self):
        exchange = self._make(status=ExchangeStatus.REJECTED)
        self.assertFalse(exchange.can_message)
        self.assertTrue(exchange.is_final)

    def test_counterpart_for_both_sides(self):
        exchange = self._make()
        self.assertEqual(exchange.counterpart_for(self.requester), self.provider)
        self.assertEqual(exchange.counterpart_for(self.provider), self.requester)
        self.assertIsNone(exchange.counterpart_for(make_user(email="x@test.ir")))


class NotificationSignalTests(TestCase):
    def setUp(self):
        self.provider = make_user(email="provider@test.ir")
        self.requester = make_user(email="requester@test.ir")
        self.skill = make_skill(self.provider, make_category())

    def test_provider_notified_on_creation(self):
        Notification.objects.all().delete()
        Exchange.objects.create(
            requester=self.requester,
            provider=self.provider,
            skill=self.skill,
            title="درخواست",
            description="توضیحات درخواست برای بررسی توسط مدیریت.",
        )
        self.assertTrue(
            Notification.objects.filter(user=self.provider, is_read=False).exists()
        )

    def test_both_notified_on_approval(self):
        exchange = Exchange.objects.create(
            requester=self.requester,
            provider=self.provider,
            skill=self.skill,
            title="درخواست",
            description="توضیحات درخواست برای بررسی توسط مدیریت.",
        )
        Notification.objects.all().delete()
        exchange.status = ExchangeStatus.APPROVED
        exchange.save()

        texts = set(Notification.objects.values_list("text", flat=True))
        self.assertEqual(len(Notification.objects.all()), 2)
        self.assertIn("درخواست تبادل شما تأیید شد.", texts)

    def test_no_notification_when_status_unchanged(self):
        exchange = Exchange.objects.create(
            requester=self.requester,
            provider=self.provider,
            skill=self.skill,
            title="درخواست",
            description="توضیحات درخواست برای بررسی توسط مدیریت.",
        )
        Notification.objects.all().delete()
        exchange.save()
        self.assertEqual(Notification.objects.count(), 0)


class ExchangeViewTests(TestCase):
    def setUp(self):
        self.provider = make_user(email="provider@test.ir", full_name="ارائه‌دهنده")
        self.requester = make_user(email="requester@test.ir", full_name="درخواست‌کننده")
        self.stranger = make_user(email="stranger@test.ir")
        self.category = make_category()
        self.skill = make_skill(self.provider, self.category, title="آموزش پایتون")
        self.exchange = Exchange.objects.create(
            requester=self.requester,
            provider=self.provider,
            skill=self.skill,
            title="درخواست تبادل پایتون",
            description="توضیحات کامل درخواست برای بررسی توسط مدیریت سامانه.",
        )

    def test_create_requires_login(self):
        url = reverse("exchanges:create", args=[self.skill.pk])
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_cannot_request_own_skill(self):
        self.client.force_login(self.provider)
        response = self.client.get(reverse("exchanges:create", args=[self.skill.pk]))
        self.assertRedirects(response, self.skill.get_absolute_url())

    def test_create_exchange(self):
        self.client.force_login(self.requester)
        response = self.client.post(
            reverse("exchanges:create", args=[self.skill.pk]),
            {
                "title": "تبادل با طراحی لوگو",
                "description": "من پایتون آموزش می‌دهم و در ازای آن لوگو می‌خواهم.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Exchange.objects.count(), 2)
        self.assertTrue(Notification.objects.filter(user=self.provider).exists())

    def test_stranger_cannot_view_exchange(self):
        self.client.force_login(self.stranger)
        response = self.client.get(reverse("exchanges:detail", args=[self.exchange.pk]))
        self.assertEqual(response.status_code, 302)

    def test_requester_can_view(self):
        self.client.force_login(self.requester)
        response = self.client.get(reverse("exchanges:detail", args=[self.exchange.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "درخواست تبادل پایتون")

    def test_send_message(self):
        self.client.force_login(self.provider)
        response = self.client.post(
            reverse("exchanges:detail", args=[self.exchange.pk]),
            {"body": "سلام، در دسترس هستم."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Message.objects.filter(exchange=self.exchange).exists())
        self.assertTrue(Notification.objects.filter(user=self.requester).exists())

    def test_cannot_message_after_rejection(self):
        self.exchange.status = ExchangeStatus.REJECTED
        self.exchange.save()
        self.client.force_login(self.requester)
        self.client.post(
            reverse("exchanges:detail", args=[self.exchange.pk]), {"body": "سلام"}
        )
        self.assertFalse(Message.objects.filter(exchange=self.exchange).exists())

    def test_mark_completed_only_when_approved(self):
        self.client.force_login(self.requester)
        self.client.post(reverse("exchanges:detail", args=[self.exchange.pk]), {"mark_completed": "1"})
        self.exchange.refresh_from_db()
        self.assertEqual(self.exchange.status, ExchangeStatus.PENDING)

        self.exchange.status = ExchangeStatus.APPROVED
        self.exchange.save()
        self.client.post(reverse("exchanges:detail", args=[self.exchange.pk]), {"mark_completed": "1"})
        self.exchange.refresh_from_db()
        self.assertEqual(self.exchange.status, ExchangeStatus.COMPLETED)

    def test_history_only_shows_approved(self):
        self.exchange.status = ExchangeStatus.APPROVED
        self.exchange.save()
        self.client.force_login(self.requester)
        self.assertContains(self.client.get(reverse("exchanges:history")), self.exchange.title)


class AdminReviewTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.requester = make_user(email="requester@test.ir")
        self.skill = make_skill(make_user(email="provider@test.ir"), make_category())
        self.exchange = Exchange.objects.create(
            requester=self.requester,
            provider=self.skill.owner,
            skill=self.skill,
            title="درخواست تبادل",
            description="توضیحات کامل درخواست برای بررسی توسط مدیریت سامانه.",
        )
        self.url = reverse("exchanges:review", args=[self.exchange.pk])

    def test_non_staff_blocked(self):
        self.client.force_login(self.requester)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_approve(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {"action": "approve", "admin_note": "تأیید شد."})
        self.assertEqual(response.status_code, 302)
        self.exchange.refresh_from_db()
        self.assertEqual(self.exchange.status, ExchangeStatus.APPROVED)
        self.assertEqual(self.exchange.reviewed_by, self.admin)

    def test_reject_requires_note(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {"action": "reject", "admin_note": "  "})
        self.assertEqual(response.status_code, 200)
        self.exchange.refresh_from_db()
        self.assertEqual(self.exchange.status, ExchangeStatus.PENDING)

    def test_reject_with_note(self):
        self.client.force_login(self.admin)
        self.client.post(self.url, {"action": "reject", "admin_note": "شرح نامناسب."})
        self.exchange.refresh_from_db()
        self.assertEqual(self.exchange.status, ExchangeStatus.REJECTED)
        self.assertEqual(self.exchange.admin_note, "شرح نامناسب.")


class ReportTests(TestCase):
    def setUp(self):
        self.reporter = make_user(email="reporter@test.ir")
        self.owner = make_user(email="owner@test.ir")
        self.skill = make_skill(self.owner, make_category())

    def test_report_requires_target(self):
        self.client.force_login(self.reporter)
        response = self.client.post(
            reverse("exchanges:report_create"),
            {"reason": ReportReason.SPAM, "description": "توضیح کافی برای گزارش."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Report.objects.count(), 0)

    def test_create_report_for_skill(self):
        self.client.force_login(self.reporter)
        response = self.client.post(
            reverse("exchanges:report_create"),
            {
                "skill": self.skill.pk,
                "reason": ReportReason.WRONG_INFO,
                "description": "اطلاعات این مهارت نادرست است.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(Report.objects.first().target_skill, self.skill)


class SkillDeletionCascadeTests(TestCase):
    def test_deleting_skill_deletes_its_exchanges(self):
        requester = make_user(email="r@test.ir")
        provider = make_user(email="p@test.ir")
        skill = make_skill(provider, make_category())
        Exchange.objects.create(
            requester=requester,
            provider=provider,
            skill=skill,
            title="درخواست",
            description="توضیحات کامل درخواست برای بررسی توسط مدیریت.",
        )
        self.assertEqual(Exchange.objects.count(), 1)
        Skill.objects.filter(pk=skill.pk).delete()
        self.assertEqual(Exchange.objects.count(), 0)

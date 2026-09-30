from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from core.testing import make_category, make_skill, make_user
from skills.models import Skill, SkillType, Watch
from skills.services import filter_skills, similar_skills, suggested_skills_for


class SkillModelTests(TestCase):
    def setUp(self):
        self.owner = make_user(email="owner@test.ir")
        self.category = make_category()

    def test_tags_list_parsing(self):
        skill = make_skill(self.owner, self.category, tags="پایتون, آموزش , , جنگو")
        self.assertEqual(skill.tags_list, ["پایتون", "آموزش", "جنگو"])

    def test_category_slug_generated(self):
        self.assertTrue(self.category.slug.startswith("cat-"))

    def test_watch_unique_per_user(self):
        from django.db import IntegrityError, transaction

        skill = make_skill(self.owner, self.category)
        Watch.objects.create(user=self.owner, skill=skill)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Watch.objects.create(user=self.owner, skill=skill)

    def test_watchers_count(self):
        skill = make_skill(self.owner, self.category)
        Watch.objects.create(user=make_user(email="w1@test.ir"), skill=skill)
        Watch.objects.create(user=make_user(email="w2@test.ir"), skill=skill)
        self.assertEqual(skill.watchers_count, 2)


class SkillCrudTests(TestCase):
    def setUp(self):
        self.owner = make_user(email="owner@test.ir")
        self.category = make_category()
        self.skill = make_skill(self.owner, self.category)

    def test_create_requires_login(self):
        url = reverse("skills:create")
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_create_skill(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("skills:create"),
            {
                "title": "طراحی لوگو",
                "type": SkillType.SERVICE,
                "category": self.category.pk,
                "level": 3,
                "description": "طراحی لوگو مینیمال برای کسب‌وکارها.",
                "tags": "لوگو, گرافیک",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Skill.objects.get(title="طراحی لوگو")
        self.assertEqual(created.owner, self.owner)
        self.assertEqual(created.tags_list, ["لوگو", "گرافیک"])

    def test_short_description_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("skills:create"),
            {
                "title": "تست",
                "type": SkillType.SKILL,
                "category": self.category.pk,
                "level": 1,
                "description": "کوتاه",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Skill.objects.filter(title="تست").exists())

    def test_owner_can_edit(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("skills:edit", args=[self.skill.pk]),
            {
                "title": "عنوان تازه",
                "type": SkillType.SKILL,
                "category": self.category.pk,
                "level": 5,
                "description": "توضیحات کامل و به‌روزشدهٔ مهارت.",
                "tags": "پایتون",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.title, "عنوان تازه")

    def test_other_user_cannot_edit(self):
        intruder = make_user(email="intruder@test.ir")
        self.client.force_login(intruder)
        response = self.client.get(reverse("skills:edit", args=[self.skill.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_delete(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("skills:delete", args=[self.skill.pk]))
        self.assertRedirects(response, reverse("skills:my_skills"))
        self.assertFalse(Skill.objects.filter(pk=self.skill.pk).exists())

    def test_my_skills_only_shows_own(self):
        make_skill(make_user(email="other@test.ir"), self.category, title="مهارت دیگری")
        self.client.force_login(self.owner)
        response = self.client.get(reverse("skills:my_skills"))
        self.assertContains(response, self.skill.title)
        self.assertNotContains(response, "مهارت دیگری")


class SkillFilterTests(TestCase):
    def setUp(self):
        self.cat_a = make_category("برنامه‌نویسی")
        self.cat_b = make_category("گرافیک")
        self.owner = make_user(email="owner@test.ir", full_name="علی رضایی")
        self.base = Skill.objects.filter(is_active=True)

        self.python = make_skill(self.owner, self.cat_a, title="آموزش پایتون", tags="پایتون, آموزش")
        self.logo = make_skill(
            self.owner,
            self.cat_b,
            title="طراحی لوگو",
            type=SkillType.SERVICE,
            tags="لوگو, گرافیک",
            level=3,
        )

    def test_search_by_title(self):
        result = filter_skills(self.base, {"q": "پایتون"})
        self.assertIn(self.python, result)
        self.assertNotIn(self.logo, result)

    def test_search_by_tag(self):
        result = filter_skills(self.base, {"q": "لوگو"})
        self.assertEqual(list(result), [self.logo])

    def test_filter_by_category(self):
        result = filter_skills(self.base, {"category": self.cat_b.pk})
        self.assertEqual(list(result), [self.logo])

    def test_filter_by_type(self):
        result = filter_skills(self.base, {"type": SkillType.SERVICE})
        self.assertEqual(list(result), [self.logo])

    def test_filter_by_minimum_level(self):
        result = filter_skills(self.base, {"level": 4})
        self.assertIn(self.python, result)
        self.assertNotIn(self.logo, result)

    def test_inactive_skills_hidden(self):
        self.python.is_active = False
        self.python.save()
        result = filter_skills(self.base, {})
        self.assertNotIn(self.python, result)

    def test_list_view_respects_search(self):
        response = self.client.get(reverse("skills:list"), {"q": "پایتون"})
        self.assertContains(response, "آموزش پایتون")
        self.assertNotContains(response, "طراحی لوگو")

    def test_list_renders_a_row_per_skill(self):
        response = self.client.get(reverse("skills:list"))
        self.assertEqual(response.content.count(b"ledger-row"), 2)
        self.assertContains(response, "ledger-head")


class LiquidGlassRenderingTests(TestCase):
    """هیچ صفحه‌ای نباید بدون سطح شیشه‌ای رندر شود."""

    def setUp(self):
        self.owner = make_user(email="owner@test.ir", full_name="سارا محمدی")
        self.category = make_category("برنامه‌نویسی")
        self.skill = make_skill(self.owner, self.category, title="آموزش پایتون")

    def test_css_ships_liquid_glass_tokens(self):
        css = Path(settings.STATICFILES_DIRS[0]) / "css" / "main.css"
        text = css.read_text(encoding="utf-8")
        for token in ("backdrop-filter", "--glass-bg", "prefers-color-scheme",
                      "prefers-reduced-motion", "@supports not"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_no_blur_support_fallback_exists(self):
        css = (Path(settings.STATICFILES_DIRS[0]) / "css" / "main.css").read_text(encoding="utf-8")
        self.assertIn("@supports not ((backdrop-filter: blur(1px))", css)

    def test_home_has_hero_glass_and_stat_tiles(self):
        body = self.client.get(reverse("home")).content.decode()
        self.assertIn("hero-glass", body)
        self.assertIn("stat-tile", body)

    def test_theme_toggle_present_for_guests(self):
        body = self.client.get(reverse("home")).content.decode()
        self.assertIn("data-theme-toggle", body)

    def test_navbar_uses_glass(self):
        body = self.client.get(reverse("home")).content.decode()
        self.assertIn("navbar-skill", body)


class LedgerRenderingTests(TestCase):
    """پارشال سطر دفترچه باید متغیر درست را بگیرد وگرنه بی‌سروصدا خالی رندر می‌شود."""

    def setUp(self):
        self.owner = make_user(email="owner@test.ir", full_name="سارا محمدی")
        self.category = make_category("برنامه‌نویسی")
        self.skill = make_skill(self.owner, self.category, title="آموزش پایتون")

    def test_home_shows_ledger_rows(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "آموزش پایتون")
        self.assertIn("ledger-row", response.content.decode())

    def test_public_profile_shows_ledger_rows(self):
        response = self.client.get(reverse("accounts:public_profile", args=[self.owner.pk]))
        self.assertContains(response, "آموزش پایتون")
        self.assertIn("ledger-row", response.content.decode())

    def test_dashboard_shows_ledger_rows(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "آموزش پایتون")
        self.assertIn("ledger-row", response.content.decode())

    def test_my_skills_shows_ledger_rows(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("skills:my_skills"))
        self.assertContains(response, "آموزش پایتون")
        self.assertIn("ledger-row", response.content.decode())

    def test_similar_skills_render(self):
        other = make_user(email="other@test.ir")
        make_skill(other, self.category, title="آموزش جنگو")
        response = self.client.get(reverse("skills:detail", args=[self.skill.pk]))
        self.assertContains(response, "آموزش جنگو")
        self.assertContains(response, "مهارت‌های مشابه")

    def test_watches_page_renders_skill_title(self):
        watcher = make_user(email="watcher@test.ir")
        Watch.objects.create(user=watcher, skill=self.skill)
        self.client.force_login(watcher)
        response = self.client.get(reverse("accounts:watches"))
        self.assertContains(response, "آموزش پایتون")
        self.assertIn("ledger-row", response.content.decode())


class SuggestionTests(TestCase):
    def setUp(self):
        self.cat = make_category("برنامه‌نویسی")
        self.alice = make_user(email="alice@test.ir")
        self.bob = make_user(email="bob@test.ir")
        self.alice_skill = make_skill(self.alice, self.cat, title="آموزش پایتون", tags="پایتون")
        self.bob_skill = make_skill(self.bob, self.cat, title="آموزش جنگو", tags="جنگو")

    def test_suggestions_exclude_own_skills(self):
        result = suggested_skills_for(self.alice)
        self.assertIn(self.bob_skill, result)
        self.assertNotIn(self.alice_skill, result)

    def test_suggestions_empty_for_guest(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertEqual(list(suggested_skills_for(AnonymousUser())), [])

    def test_similar_skills_same_category(self):
        result = similar_skills(self.alice_skill)
        self.assertIn(self.bob_skill, result)
        self.assertNotIn(self.alice_skill, result)


class WatchTests(TestCase):
    def setUp(self):
        self.owner = make_user(email="owner@test.ir")
        self.watcher = make_user(email="watcher@test.ir")
        self.skill = make_skill(self.owner, make_category())
        self.url = reverse("skills:toggle_watch", args=[self.skill.pk])

    def test_toggle_requires_login(self):
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_toggle_on_then_off(self):
        self.client.force_login(self.watcher)
        self.client.post(self.url)
        self.assertTrue(Watch.objects.filter(user=self.watcher, skill=self.skill).exists())

        self.client.post(self.url)
        self.assertFalse(Watch.objects.filter(user=self.watcher, skill=self.skill).exists())

    def test_toggle_requires_post(self):
        self.client.force_login(self.watcher)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_watches_page_lists_watch(self):
        Watch.objects.create(user=self.watcher, skill=self.skill)
        self.client.force_login(self.watcher)
        response = self.client.get(reverse("accounts:watches"))
        self.assertContains(response, self.skill.title)

from django.test import TestCase, override_settings
from django.urls import reverse

from core.templatetags.skillyar_tags import _content_version, static_ver


class StaticVersionTests(TestCase):
    """URL فایل استاتیک باید با تغییر محتوا عوض شود تا کش مرورگر دور بخورد."""

    def test_version_is_a_short_hash(self):
        version = _content_version("css/main.css")
        self.assertEqual(len(version), 8)
        self.assertNotEqual(version, "0", "main.css پیدا نشد")

    def test_unknown_file_falls_back(self):
        self.assertEqual(_content_version("css/does-not-exist.css"), "0")

    def test_static_ver_includes_version_param(self):
        url = static_ver("css/main.css")
        self.assertIn("css/main.css", url)
        self.assertIn("?v=", url)

    def test_version_changes_when_file_changes(self):
        from pathlib import Path

        from django.conf import settings

        css = Path(settings.STATICFILES_DIRS[0]) / "css" / "main.css"
        original = css.read_bytes()
        before = _content_version("css/main.css")
        try:
            css.write_bytes(original + b"\n/* probe */\n")
            after = _content_version("css/main.css")
        finally:
            css.write_bytes(original)
        self.assertNotEqual(before, after, "هش به تغییر محتوا حساس نیست")

    def test_pages_reference_versioned_assets(self):
        body = self.client.get(reverse("home")).content.decode()
        self.assertIn("/static/css/main.css?v=", body)
        self.assertIn("/static/js/main.js?v=", body)


class SecurityHeaderTests(TestCase):
    def test_security_headers_present(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "same-origin")


class NotFoundPageTests(TestCase):
    @override_settings(DEBUG=True)
    def test_missing_page_gives_guidance_not_blank(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        body = response.content.decode()
        self.assertIn("این صفحه وجود ندارد", body)
        self.assertIn("/does-not-exist/", body)

    def test_production_404_uses_django_default(self):
        response = self.client.get("/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("این صفحه وجود ندارد", response.content.decode())
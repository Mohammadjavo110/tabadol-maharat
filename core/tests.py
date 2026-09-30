from django.test import TestCase, override_settings
from django.urls import reverse


class StaticCacheTests(TestCase):
    """در حالت توسعه نباید CSS قدیمی از کش مرورگر سرو شود."""

    @override_settings(DEBUG=True)
    def test_static_files_are_not_cached_in_debug(self):
        response = self.client.get("/static/css/main.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])

    def test_pages_are_cacheable_in_production(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("no-store", response.get("Cache-Control", ""))

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

    def test_production_404_stays_empty(self):
        self.assertEqual(self.client.get("/does-not-exist/").status_code, 404)

# Create your tests here.

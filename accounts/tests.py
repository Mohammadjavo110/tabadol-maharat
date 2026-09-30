from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from core.testing import TEST_PASSWORD, make_user

User = get_user_model()


class UserModelTests(TestCase):
    def test_profile_created_automatically(self):
        user = make_user(email="a@test.ir")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_phone_is_unique(self):
        make_user(email="a@test.ir", phone="09120000000")
        with self.assertRaises(Exception):
            make_user(email="b@test.ir", phone="09120000000")

    def test_invalid_phone_rejected(self):
        user = make_user(email="a@test.ir", phone="12345")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_str_prefers_full_name(self):
        self.assertEqual(str(make_user(email="a@test.ir", full_name="سارا")), "سارا")
        self.assertEqual(str(make_user(email="b@test.ir")), "b@test.ir")

    def test_create_superuser_sets_admin_role(self):
        admin = User.objects.create_superuser(email="s@test.ir", password=TEST_PASSWORD)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_admin_role)


class AuthenticationBackendTests(TestCase):
    def setUp(self):
        self.user = make_user(email="ali@test.ir", phone="09121234567", full_name="علی")

    def test_login_with_email(self):
        self.assertTrue(self.client.login(username="ali@test.ir", password=TEST_PASSWORD))

    def test_login_with_phone(self):
        self.assertTrue(self.client.login(username="09121234567", password=TEST_PASSWORD))

    def test_login_email_is_case_insensitive(self):
        self.assertTrue(self.client.login(username="ALI@TEST.IR", password=TEST_PASSWORD))

    def test_wrong_password_fails(self):
        self.assertFalse(self.client.login(username="ali@test.ir", password="wrong"))

    def test_unknown_identifier_fails(self):
        self.assertFalse(self.client.login(username="nobody@test.ir", password=TEST_PASSWORD))


class RegisterViewTests(TestCase):
    url = reverse("accounts:register")

    def test_get_shows_form(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_successful_registration_logs_user_in(self):
        response = self.client.post(
            self.url,
            {
                "full_name": "سارا محمدی",
                "email": "sara@test.ir",
                "phone": "09121234567",
                "password1": "Strong#Pass1",
                "password2": "Strong#Pass1",
            },
        )
        self.assertRedirects(response, reverse("accounts:dashboard"))
        user = User.objects.get(email="sara@test.ir")
        self.assertEqual(user.full_name, "سارا محمدی")
        self.assertTrue(user.check_password("Strong#Pass1"))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_duplicate_email_rejected(self):
        make_user(email="taken@test.ir")
        response = self.client.post(
            self.url,
            {
                "full_name": "دیگری",
                "email": "taken@test.ir",
                "phone": "09121234567",
                "password1": "Strong#Pass1",
                "password2": "Strong#Pass1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "email", "کاربری با این ایمیل قبلاً ثبت‌نام کرده است.")

    def test_mismatched_passwords_rejected(self):
        response = self.client.post(
            self.url,
            {
                "full_name": "تست",
                "email": "new@test.ir",
                "phone": "09121234567",
                "password1": "Strong#Pass1",
                "password2": "Different#99",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="new@test.ir").exists())

    def test_weak_password_rejected(self):
        response = self.client.post(
            self.url,
            {
                "full_name": "تست",
                "email": "weak@test.ir",
                "phone": "09121234567",
                "password1": "1234",
                "password2": "1234",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="weak@test.ir").exists())


class AccessControlTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

    def test_logout_requires_post(self):
        user = make_user(email="a@test.ir")
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_via_post(self):
        user = make_user(email="a@test.ir")
        self.client.force_login(user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("home"))


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = make_user(email="a@test.ir", full_name="قدیمی")
        self.url = reverse("accounts:profile")

    def test_update_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "full_name": "جدید",
                "email": "a@test.ir",
                "phone": "09129999999",
                "city": "تهران",
                "bio": "توضیح کوتاه دربارهٔ من.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "جدید")
        self.assertEqual(self.user.profile.city, "تهران")

    def test_phone_already_taken_rejected(self):
        make_user(email="b@test.ir", phone="09121110000")
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "full_name": "نام",
                "email": "a@test.ir",
                "phone": "09121110000",
                "city": "",
                "bio": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.phone, "09121110000")

    def test_public_profile_is_visible_to_guests(self):
        response = self.client.get(reverse("accounts:public_profile", args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "قدیمی")

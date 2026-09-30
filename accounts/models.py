from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

phone_validator = RegexValidator(
    regex=r"^09\d{9}$",
    message="شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود (مثال: 09121234567).",
)


class Role(models.TextChoices):
    USER = "user", "کاربر"
    ADMIN = "admin", "مدیر سیستم"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("ایمیل الزامی است.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", Role.USER)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("مدیر باید is_staff=True داشته باشد.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("مدیر باید is_superuser=True داشته باشد.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("ایمیل", unique=True)
    phone = models.CharField(
        "موبایل",
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[phone_validator],
        help_text="برای ورود با موبایل الزامی است.",
    )
    full_name = models.CharField("نام و نام خانوادگی", max_length=120, blank=True)
    role = models.CharField("نقش", max_length=10, choices=Role.choices, default=Role.USER)
    is_staff = models.BooleanField("دسترسی به پنل مدیریت", default=False)
    is_active = models.BooleanField("حساب فعال است", default=True)
    date_joined = models.DateTimeField("تاریخ عضویت", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ["-date_joined"]
        indexes = [models.Index(fields=["role"])]

    def __str__(self) -> str:
        return self.full_name or self.email

    @property
    def is_admin_role(self) -> bool:
        return self.is_staff or self.role == Role.ADMIN

    @property
    def display_name(self) -> str:
        return self.full_name or self.email

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.display_name.split(" ")[0]

    @property
    def avatar_url(self) -> str:
        if hasattr(self, "profile") and self.profile.avatar:
            return self.profile.avatar.url
        return "https://api.dicebear.com/9.x/initials/svg?seed=" + self.display_name


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="کاربر",
    )
    city = models.CharField("شهر", max_length=64, blank=True)
    bio = models.TextField("درباره من", max_length=500, blank=True)
    avatar = models.ImageField("تصویر پروفایل", upload_to="avatars/%Y/%m/", blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self) -> str:
        return f"پروفایل {self.user}"

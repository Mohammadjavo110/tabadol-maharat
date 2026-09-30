from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    title = models.CharField("عنوان", max_length=80, unique=True)
    slug = models.SlugField("نامک", max_length=100, unique=True, blank=True)
    description = models.CharField("توضیح", max_length=250, blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        if not self.slug:
            base = slugify(self.title, allow_unicode=False) or "cat"
            self.slug = f"{base}-{self.pk}"
            super().save(update_fields=["slug"])

    def get_absolute_url(self) -> str:
        return reverse("skills:list") + f"?category={self.pk}"


class SkillType(models.TextChoices):
    SKILL = "skill", "مهارت"
    SERVICE = "service", "خدمت"


class Level(models.IntegerChoices):
    BEGINNER = 1, "مقدم"
    NOVICE = 2, "مبتدی"
    INTERMEDIATE = 3, "متوسط"
    ADVANCED = 4, "پیشرفته"
    EXPERT = 5, "حرفه‌ای"


class Skill(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skills",
        verbose_name="مالک",
    )
    title = models.CharField("عنوان", max_length=120)
    type = models.CharField("نوع", max_length=10, choices=SkillType.choices)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="skills",
        verbose_name="دسته‌بندی",
    )
    level = models.PositiveSmallIntegerField("سطح", choices=Level.choices, default=Level.BEGINNER)
    description = models.TextField("توضیحات")
    tags = models.CharField("برچسب‌ها", max_length=200, blank=True, help_text="با کاما جدا کنید.")
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "مهارت / خدمت"
        verbose_name_plural = "مهارت‌ها و خدمات"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["category", "type"]),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("skills:detail", args=[self.pk])

    @property
    def tags_list(self) -> list[str]:
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    @property
    def is_service(self) -> bool:
        return self.type == SkillType.SERVICE

    @property
    def watchers_count(self) -> int:
        return self.watches.count()


class Watch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watches",
        verbose_name="کاربر",
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="watches", verbose_name="مهارت")
    created_at = models.DateTimeField("تاریخ دنبال کردن", auto_now_add=True)

    class Meta:
        verbose_name = "دنبال‌شده"
        verbose_name_plural = "دنبال‌شده‌ها"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "skill"], name="unique_user_skill_watch"),
        ]

    def __str__(self) -> str:
        return f"{self.user} ← {self.skill}"

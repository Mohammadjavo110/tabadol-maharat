from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class ExchangeStatus(models.TextChoices):
    PENDING = "pending", "در انتظار بررسی مدیر"
    ADMIN_REVIEW = "admin_review", "در حال بررسی"
    APPROVED = "approved", "تأییدشده"
    REJECTED = "rejected", "ردشده"
    COMPLETED = "completed", "تکمیل‌شده"


class Exchange(models.Model):
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_exchanges",
        verbose_name="درخواست‌کننده",
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_exchanges",
        verbose_name="ارائه‌دهنده",
    )
    skill = models.ForeignKey(
        "skills.Skill",
        on_delete=models.CASCADE,
        related_name="exchanges",
        verbose_name="مهارت مورد تقاضا",
    )
    offered_skill = models.ForeignKey(
        "skills.Skill",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="offered_in_exchanges",
        verbose_name="مهارت پیشنهادی من",
    )
    title = models.CharField("عنوان", max_length=120)
    description = models.TextField("توضیحات درخواست")
    status = models.CharField(
        "وضعیت",
        max_length=15,
        choices=ExchangeStatus.choices,
        default=ExchangeStatus.PENDING,
    )
    admin_note = models.TextField("یادداشت مدیر", blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_exchanges",
        verbose_name="بررسی‌شده توسط",
    )
    reviewed_at = models.DateTimeField("زمان بررسی", null=True, blank=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        verbose_name = "درخواست تبادل"
        verbose_name_plural = "درخواست‌های تبادل"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["requester", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.requester} ← {self.provider}"

    def clean(self) -> None:
        errors: dict[str, str] = {}
        if self.requester_id and self.provider_id and self.requester_id == self.provider_id:
            errors["provider"] = "نمی‌توانید مهارت خودتان را از خودتان درخواست کنید."
        if self.requester_id and self.skill_id and self.skill.owner_id == self.requester_id:
            errors["skill"] = "این مهارت متعلق به خود شماست."
        if self.offered_skill_id and self.offered_skill.owner_id != self.requester_id:
            errors["offered_skill"] = "مهارت پیشنهادی باید متعلق به خودتان باشد."
        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self) -> str:
        return reverse("exchanges:detail", args=[self.pk])

    @property
    def is_final(self) -> bool:
        return self.status in {ExchangeStatus.APPROVED, ExchangeStatus.REJECTED, ExchangeStatus.COMPLETED}

    @property
    def is_accepted(self) -> bool:
        return self.status in {ExchangeStatus.APPROVED, ExchangeStatus.COMPLETED}

    @property
    def can_message(self) -> bool:
        return not self.is_final

    def counterpart_for(self, user) -> "object | None":
        if user.pk == self.requester_id:
            return self.provider
        if user.pk == self.provider_id:
            return self.requester
        return None

    def involves(self, user) -> bool:
        return user.is_authenticated and user.pk in {self.requester_id, self.provider_id}

    @property
    def target(self) -> "object":
        return f"{self.requester} ⇄ {self.provider}"


class Message(models.Model):
    exchange = models.ForeignKey(
        Exchange,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="تبادل",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="فرستنده",
    )
    body = models.TextField("متن پیام", max_length=2000)
    is_read = models.BooleanField("خوانده شده", default=False)
    created_at = models.DateTimeField("زمان ارسال", auto_now_add=True)

    class Meta:
        verbose_name = "پیام"
        verbose_name_plural = "پیام‌ها"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["exchange", "created_at"])]

    def __str__(self) -> str:
        return f"{self.sender}: {self.body[:40]}"


class ReportReason(models.TextChoices):
    SPAM = "spam", "هرزنامه"
    ABUSE = "abuse", "بدرفتاری"
    WRONG_INFO = "wrong_info", "اطلاعات نادرست"
    FRAUD = "fraud", "کلاهبرداری"
    OTHER = "other", "سایر"


class ReportStatus(models.TextChoices):
    OPEN = "open", "فعال"
    RESOLVED = "resolved", "رسیدگی‌شده"


class Report(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="گزارش‌دهنده",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports_against",
        verbose_name="کاربر گزارش‌شده",
    )
    target_skill = models.ForeignKey(
        "skills.Skill",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name="مهارت گزارش‌شده",
    )
    reason = models.CharField("دلیل", max_length=15, choices=ReportReason.choices)
    description = models.TextField("توضیحات")
    status = models.CharField(
        "وضعیت",
        max_length=10,
        choices=ReportStatus.choices,
        default=ReportStatus.OPEN,
    )
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_reports",
        verbose_name="رسیدگی‌شده توسط",
    )
    handled_at = models.DateTimeField("زمان رسیدگی", null=True, blank=True)
    created_at = models.DateTimeField("تاریخ گزارش", auto_now_add=True)

    class Meta:
        verbose_name = "گزارش"
        verbose_name_plural = "گزارش‌ها"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        target = self.target_user or self.target_skill
        return f"گزارش {self.get_reason_display()} درباره {target}"

    def clean(self) -> None:
        if not self.target_user_id and not self.target_skill_id:
            raise ValidationError({"target_user": "حداقل یکی از کاربر یا مهارت را انتخاب کنید."})

    @property
    def target_label(self) -> str:
        return str(self.target_user or self.target_skill)


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="کاربر",
    )
    text = models.CharField("متن", max_length=255)
    url = models.CharField("نشانی", max_length=255, blank=True)
    is_read = models.BooleanField("خوانده شده", default=False)
    created_at = models.DateTimeField("زمان", auto_now_add=True)

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self) -> str:
        return f"{self.user} ← {self.text}"

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import NoReverseMatch

from exchanges.models import Exchange, ExchangeStatus, Notification


def exchange_url(exchange: Exchange) -> str:
    """تا وقتی مسیرها ساخته نشده‌اند، سیگنال نباید باعث خطا شود."""
    try:
        return exchange.get_absolute_url()
    except NoReverseMatch:
        return ""


STATUS_MESSAGES = {
    ExchangeStatus.PENDING: "درخواست تبادل شما ثبت شد و در انتظار بررسی مدیر است.",
    ExchangeStatus.ADMIN_REVIEW: "درخواست تبادل شما در حال بررسی توسط مدیر است.",
    ExchangeStatus.APPROVED: "درخواست تبادل شما تأیید شد.",
    ExchangeStatus.REJECTED: "درخواست تبادل شما رد شد.",
    ExchangeStatus.COMPLETED: "تبادل به پایان رسید و در تاریخچه ثبت شد.",
}


@receiver(pre_save, sender=Exchange)
def remember_previous_status(sender, instance: Exchange, **kwargs) -> None:
    if instance.pk:
        instance._previous_status = (
            sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        )
    else:
        instance._previous_status = None


@receiver(post_save, sender=Exchange)
def notify_status_change(sender, instance: Exchange, created: bool, **kwargs) -> None:
    if created:
        message = STATUS_MESSAGES[ExchangeStatus.PENDING]
        for recipient in (instance.provider,):
            Notification.objects.create(
                user=recipient,
                text=f"درخواست جدیدی برای «{instance.skill.title}» از {instance.requester} دارید.",
                url=exchange_url(instance),
            )
        return

    previous = getattr(instance, "_previous_status", None)
    if previous == instance.status:
        return

    text = STATUS_MESSAGES.get(instance.status)
    if not text:
        return

    for recipient in (instance.requester, instance.provider):
        Notification.objects.create(
            user=recipient,
            text=text,
            url=exchange_url(instance),
        )

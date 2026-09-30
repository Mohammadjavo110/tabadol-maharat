from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import NoReverseMatch

from exchanges.models import Exchange, ExchangeStatus, Notification


def exchange_url(exchange: Exchange) -> str:
    """ØªØ§ ÙˆÙ‚ØªÛŒ Ù…Ø³ÛŒØ±Ù‡Ø§ Ø³Ø§Ø®ØªÙ‡ Ù†Ø´Ø¯Ù‡â€ŒØ§Ù†Ø¯ØŒ Ø³ÛŒÚ¯Ù†Ø§Ù„ Ù†Ø¨Ø§ÛŒØ¯ Ø¨Ø§Ø¹Ø« Ø®Ø·Ø§ Ø´ÙˆØ¯."""
    try:
        return exchange.get_absolute_url()
    except NoReverseMatch:
        return ""


STATUS_MESSAGES = {
    ExchangeStatus.PENDING: "Ø¯Ø±Ø®ÙˆØ§Ø³Øª ØªØ¨Ø§Ø¯Ù„ Ø´Ù…Ø§ Ø«Ø¨Øª Ø´Ø¯ Ùˆ Ø¯Ø± Ø§Ù†ØªØ¸Ø§Ø± Ø¨Ø±Ø±Ø³ÛŒ Ù…Ø¯ÛŒØ± Ø§Ø³Øª.",
    ExchangeStatus.ADMIN_REVIEW: "Ø¯Ø±Ø®ÙˆØ§Ø³Øª ØªØ¨Ø§Ø¯Ù„ Ø´Ù…Ø§ Ø¯Ø± Ø­Ø§Ù„ Ø¨Ø±Ø±Ø³ÛŒ ØªÙˆØ³Ø· Ù…Ø¯ÛŒØ± Ø§Ø³Øª.",
    ExchangeStatus.APPROVED: "Ø¯Ø±Ø®ÙˆØ§Ø³Øª ØªØ¨Ø§Ø¯Ù„ Ø´Ù…Ø§ ØªØ£ÛŒÛŒØ¯ Ø´Ø¯.",
    ExchangeStatus.REJECTED: "Ø¯Ø±Ø®ÙˆØ§Ø³Øª ØªØ¨Ø§Ø¯Ù„ Ø´Ù…Ø§ Ø±Ø¯ Ø´Ø¯.",
    ExchangeStatus.COMPLETED: "ØªØ¨Ø§Ø¯Ù„ Ø¨Ù‡ Ù¾Ø§ÛŒØ§Ù† Ø±Ø³ÛŒØ¯ Ùˆ Ø¯Ø± ØªØ§Ø±ÛŒØ®Ú†Ù‡ Ø«Ø¨Øª Ø´Ø¯.",
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
                text=f"Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ø¬Ø¯ÛŒØ¯ÛŒ Ø¨Ø±Ø§ÛŒ Â«{instance.skill.title}Â» Ø§Ø² {instance.requester} Ø¯Ø§Ø±ÛŒØ¯.",
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

from django.conf import settings


def site_context(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
        "SUPPORT_PHONE": settings.SUPPORT_PHONE,
    }


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notifications_count": 0}
    return {
        "unread_notifications_count": request.user.notifications.filter(is_read=False).count()
    }

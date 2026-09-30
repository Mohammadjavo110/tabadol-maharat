from django.conf import settings


def site_context(request):
    return {
        "SITE_NAME": "مهارت‌یار",
        "SUPPORT_EMAIL": getattr(settings, "SUPPORT_EMAIL", "support@skillyar.ir"),
        "SUPPORT_PHONE": getattr(settings, "SUPPORT_PHONE", "021-12345678"),
    }

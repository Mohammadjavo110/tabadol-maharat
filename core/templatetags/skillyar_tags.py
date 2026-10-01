import hashlib
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag(takes_context=True)
def page_url(context, page_number):
    """ساخت نشانی صفحه‌بندی با حفظ سایر پارامترهای جستجو."""
    request = context.get("request")
    if request is None:
        return f"?page={page_number}"
    query = request.GET.copy()
    query["page"] = page_number
    return f"?{query.urlencode()}"


@register.filter
def level_bars(level, max_level=5):
    """لیستی از بولین برمی‌گرداند تا در قالب به‌صورت میلهٔ سطح رندر شود."""
    try:
        value = int(level)
    except (TypeError, ValueError):
        value = 0
    return [index <= value for index in range(1, int(max_level) + 1)]


def _content_version(path: str) -> str:
    """هش کوتاه محتوای فایل — با هر ویرایش تغییر می‌کند."""
    for base in getattr(settings, "STATICFILES_DIRS", []):
        candidate = Path(base) / path
        if candidate.is_file():
            return hashlib.sha1(candidate.read_bytes()).hexdigest()[:8]
    return "0"


@register.simple_tag
def static_ver(path: str) -> str:
    """نشانی فایل استاتیک با پارامتر نسخه.

    مرورگر فایل‌های استاتیک را کش می‌کند. چون ``runserver`` در حالت توسعه هیچ
    هدر کشی نمی‌فرستد، تغییر CSS بدون عوض شدن URL دیده نمی‌شود. با اضافه کردن
    هش محتوا به نشانی، هر ویرایش یک URL تازه می‌سازد و مرورگر ناچار به دریافت
    نسخهٔ جدید می‌شود.
    """
    return f"{static(path)}?v={_content_version(path)}"
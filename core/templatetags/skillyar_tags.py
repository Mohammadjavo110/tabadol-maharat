from django import template

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
def level_filled(level, max_level=5):
    """لیستی از بولین برمی‌گرداند تا در قالب به‌صورت نقطه‌های سطح رندر شود."""
    try:
        value = int(level)
    except (TypeError, ValueError):
        value = 0
    return [index <= value for index in range(1, int(max_level) + 1)]


@register.filter
def get_item(mapping, key):
    if hasattr(mapping, "get"):
        return mapping.get(key)
    return None

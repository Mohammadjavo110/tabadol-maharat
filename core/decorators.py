from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect


def admin_required(view_func):
    """فقط کاربرانی که is_staff دارند اجازهٔ دسترسی دارند."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{'/accounts/login/'}?next={request.path}")
        if not request.user.is_staff:
            messages.error(request, "این بخش فقط برای مدیر سیستم در دسترس است.")
            return redirect("accounts:dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper

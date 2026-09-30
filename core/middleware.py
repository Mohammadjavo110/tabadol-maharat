"""میان‌افزارهای سبک پروژه."""

from django.conf import settings
from django.http import HttpResponse


class NoStoreStaticMiddleware:
    """در حالت توسعه، فایل‌های استاتیک هرگز نباید از کش مرورگر سرو شوند.

    بدون این هدر، مرورگر با کش تقریبی تصمیم می‌گیرد و ممکن است نسخهٔ قدیمی CSS/JS را
    نشان دهد حتی وقتی فایل روی دیسک عوض شده است. این مشکل هنگام بازطراحی رابط کاربری
    چندین بار پیش آمد، پس در حالت توسعه صریحاً غیرفعال می‌شود.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.DEBUG and request.path_info.startswith(settings.STATIC_URL):
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response


class SecurityHeadersMiddleware:
    """هدرهای امنیتی پایه که Django به‌صورت پیش‌فرض نمی‌فرستد."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("Referrer-Policy", "same-origin")
        return response


class SimpleConsole404Middleware:
    """در حالت توسعه، صفحهٔ ۴۰۴ به‌جای صفحهٔ سفید خالی، راهنمایی می‌دهد."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.DEBUG and response.status_code == 404:
            response = HttpResponse(_not_found_body(request), status=404)
        return response


def _not_found_body(request) -> str:
    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>صفحه پیدا نشد — ۴۰۴</title>
<style>
  body {{ font-family: system-ui, Tahoma, sans-serif; background: #f6f8f7; color: #1c1c1e;
          display: grid; place-items: center; min-height: 100vh; margin: 0; padding: 2rem; }}
  .box {{ background: #fff; border: 1px solid #d8e1e3; border-radius: 16px;
          padding: 2rem; max-width: 34rem; line-height: 1.9; }}
  h1 {{ margin: 0 0 .5rem; font-size: 1.4rem; }}
  code {{ background: #eef2f1; padding: .1rem .4rem; border-radius: 6px; direction: ltr;
          display: inline-block; }}
  a {{ color: #006bdf; }}
</style></head>
<body><div class="box">
  <h1>این صفحه وجود ندارد</h1>
  <p>نشانی زیر در سامانه تعریف نشده است:</p>
  <p><code>{request.path}</code></p>
  <p>شاید تبادل یا مهارتی که دنبالش بودی حذف شده باشد.</p>
  <p><a href="/">بازگشت به صفحهٔ اصلی</a></p>
</div></body></html>"""
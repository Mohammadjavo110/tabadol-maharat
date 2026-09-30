from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from config.settings import PAGINATE_BY
from core.decorators import admin_required
from dashboard.forms import CategoryForm
from dashboard.reports import (
    busiest_users,
    daily_stats,
    format_daily_report,
    top_categories,
    top_skills_by_watches,
    totals,
)
from exchanges.models import Exchange, ExchangeStatus, Report, ReportStatus
from skills.models import Category, Skill

User = get_user_model()


def _paginate(request, queryset):
    return Paginator(queryset, PAGINATE_BY).get_page(request.GET.get("page"))


@admin_required
def home(request):
    context = {
        "totals": totals(),
        "today": daily_stats(),
        "top_skills": top_skills_by_watches(),
        "top_categories": top_categories(),
        "busiest_users": busiest_users(),
        "pending_exchanges": Exchange.objects.filter(
            status__in=[ExchangeStatus.PENDING, ExchangeStatus.ADMIN_REVIEW]
        )
        .select_related("requester", "provider", "skill")
        .order_by("-created_at")[:8],
        "open_reports": Report.objects.filter(status=ReportStatus.OPEN)
        .select_related("reporter")
        .order_by("-created_at")[:8],
    }
    return render(request, "dashboard/home.html", context)


@admin_required
def daily_report(request):
    from datetime import date

    try:
        day = date.fromisoformat(request.GET.get("date", "")) if request.GET.get("date") else None
    except ValueError:
        day = None
    if day is None:
        day = timezone.localdate()

    context = {
        "day": day,
        "stats": daily_stats(day),
        "totals": totals(),
        "report_text": format_daily_report(day),
    }
    return render(request, "dashboard/daily_report.html", context)


@admin_required
def user_list(request):
    users = (
        User.objects.select_related("profile")
        .annotate(
            skills_count=Count("skills", distinct=True),
            sent_count=Count("sent_exchanges", distinct=True),
        )
        .order_by("-date_joined")
    )
    query = (request.GET.get("q") or "").strip()
    if query:
        users = users.filter(
            Q(email__icontains=query) | Q(full_name__icontains=query) | Q(phone__icontains=query)
        )
    role = request.GET.get("role") or ""
    if role in {"user", "admin"}:
        users = users.filter(role=role)

    return render(
        request,
        "dashboard/users.html",
        {
            "page_obj": _paginate(request, users),
            "query": query,
            "current_role": role,
            "totals": totals(),
        },
    )


@admin_required
@require_POST
def user_toggle_active(request, pk: int):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.error(request, "نمی‌توانید حساب خودتان را غیرفعال کنید.")
    elif target.is_superuser:
        messages.error(request, "حساب مدیر ارشد قابل تغییر نیست.")
    else:
        target.is_active = not target.is_active
        target.save(update_fields=["is_active"])
        state = "فعال" if target.is_active else "غیرفعال"
        messages.success(request, f"حساب «{target.display_name}» {state} شد.")
    return redirect("dashboard:users")


@admin_required
@require_POST
def user_change_role(request, pk: int):
    target = get_object_or_404(User, pk=pk)
    new_role = request.POST.get("role")

    if new_role not in {"user", "admin"}:
        messages.error(request, "نقش انتخاب‌شده معتبر نیست.")
    elif target == request.user:
        messages.error(request, "نمی‌توانید نقش حساب خودتان را تغییر دهید.")
    elif target.is_superuser:
        messages.error(request, "نقش مدیر ارشد قابل تغییر نیست.")
    else:
        target.role = new_role
        target.is_staff = new_role == "admin"
        target.save(update_fields=["role", "is_staff"])
        label = "مدیر سیستم" if new_role == "admin" else "کاربر"
        messages.success(request, f"نقش «{target.display_name}» به {label} تغییر کرد.")
    return redirect("dashboard:users")


@admin_required
@require_POST
def user_delete(request, pk: int):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.error(request, "نمی‌توانید حساب خودتان را حذف کنید.")
    elif target.is_superuser:
        messages.error(request, "حساب مدیر ارشد قابل حذف نیست.")
    else:
        name = target.display_name
        target.delete()
        messages.success(request, f"حساب «{name}» و اطلاعات وابستهٔ آن حذف شد.")
    return redirect("dashboard:users")


@admin_required
def exchange_list(request):
    exchanges = Exchange.objects.select_related("requester", "provider", "skill").order_by(
        "-created_at"
    )
    status = request.GET.get("status") or ""
    if status:
        exchanges = exchanges.filter(status=status)
    query = (request.GET.get("q") or "").strip()
    if query:
        exchanges = exchanges.filter(
            Q(title__icontains=query) | Q(requester__email__icontains=query)
        )

    return render(
        request,
        "dashboard/exchanges.html",
        {
            "page_obj": _paginate(request, exchanges),
            "status_choices": ExchangeStatus.choices,
            "current_status": status,
            "query": query,
            "totals": totals(),
        },
    )


@admin_required
def report_list(request):
    reports = Report.objects.select_related(
        "reporter", "target_user", "target_skill", "handled_by"
    ).order_by("-created_at")
    status = request.GET.get("status") or ReportStatus.OPEN
    reports = reports.filter(status=status)

    return render(
        request,
        "dashboard/reports.html",
        {
            "page_obj": _paginate(request, reports),
            "current_status": status,
            "totals": totals(),
        },
    )


@admin_required
@require_POST
def report_update(request, pk: int):
    report = get_object_or_404(Report, pk=pk)
    action = request.POST.get("action")

    if action == "resolve":
        report.status = ReportStatus.RESOLVED
    elif action == "reopen":
        report.status = ReportStatus.OPEN
    else:
        return redirect("dashboard:reports")

    report.handled_by = request.user
    report.handled_at = timezone.now()
    report.save(update_fields=["status", "handled_by", "handled_at"])
    messages.success(request, "وضعیت گزارش به‌روزرسانی شد.")
    return redirect("dashboard:reports")


@admin_required
def skill_list(request):
    skills = (
        Skill.objects.select_related("owner", "category")
        .annotate(total_watches=Count("watches", distinct=True))
        .order_by("-created_at")
    )
    query = (request.GET.get("q") or "").strip()
    if query:
        skills = skills.filter(Q(title__icontains=query) | Q(owner__email__icontains=query))

    return render(
        request,
        "dashboard/skills.html",
        {
            "page_obj": _paginate(request, skills),
            "query": query,
            "totals": totals(),
        },
    )


@admin_required
@require_POST
def skill_toggle_active(request, pk: int):
    skill = get_object_or_404(Skill, pk=pk)
    skill.is_active = not skill.is_active
    skill.save(update_fields=["is_active"])
    state = "فعال" if skill.is_active else "غیرفعال"
    messages.success(request, f"مهارت «{skill.title}» {state} شد.")
    return redirect("dashboard:skills")


@admin_required
@require_POST
def skill_delete(request, pk: int):
    skill = get_object_or_404(Skill, pk=pk)
    title = skill.title
    skill.delete()
    messages.success(request, f"مهارت «{title}» حذف شد.")
    return redirect("dashboard:skills")


@admin_required
def category_list(request):
    categories = Category.objects.annotate(
        skills_count=Count("skills", distinct=True),
        active_skills=Count("skills", filter=Q(skills__is_active=True), distinct=True),
    )
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "دسته‌بندی جدید ثبت شد.")
        return redirect("dashboard:categories")

    return render(request, "dashboard/categories.html", {"categories": categories, "form": form})


@admin_required
def category_edit(request, pk: int):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "دسته‌بندی به‌روزرسانی شد.")
        return redirect("dashboard:categories")
    return render(
        request,
        "dashboard/category_edit.html",
        {"form": form, "category": category},
    )


@admin_required
@require_POST
def category_delete(request, pk: int):
    category = get_object_or_404(Category, pk=pk)
    count = category.skills.count()
    title = category.title
    category.delete()
    messages.warning(request, f"دسته‌بندی «{title}» و {count} مهارت وابسته حذف شد.")
    return redirect("dashboard:categories")

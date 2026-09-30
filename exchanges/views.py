from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from config.settings import PAGINATE_BY
from core.decorators import admin_required
from exchanges.forms import ExchangeCreateForm, ExchangeReviewForm, MessageForm, ReportForm
from exchanges.models import Exchange, ExchangeStatus, Message, Notification, Report
from skills.models import Skill

User = get_user_model()


def _paginate(request, queryset):
    return Paginator(queryset, PAGINATE_BY).get_page(request.GET.get("page"))


def _visible_exchanges(user):
    return Exchange.objects.filter(Q(requester=user) | Q(provider=user))


def _get_exchange_for_user(request, pk):
    exchange = get_object_or_404(
        Exchange.objects.select_related("requester", "provider", "skill", "offered_skill"),
        pk=pk,
    )
    if not exchange.involves(request.user) and not request.user.is_staff:
        return None
    return exchange


def _list_context(request, queryset, **extra):
    current_status = request.GET.get("status") or ""
    if current_status:
        queryset = queryset.filter(status=current_status)
    context = {
        "page_obj": _paginate(request, queryset),
        "total_count": queryset.count(),
        "status_choices": ExchangeStatus.choices,
        "current_status": current_status,
    }
    context.update(extra)
    return context


@login_required
def exchange_create(request, skill_pk: int):
    skill = get_object_or_404(
        Skill.objects.select_related("owner", "owner__profile"), pk=skill_pk, is_active=True
    )

    if skill.owner_id == request.user.pk:
        messages.error(request, "نمی‌توانید برای مهارت خودتان درخواست تبادل ثبت کنید.")
        return redirect(skill.get_absolute_url())

    form = ExchangeCreateForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        exchange = form.save(commit=False)
        exchange.skill = skill
        exchange.provider = skill.owner
        exchange.requester = request.user
        exchange.save()
        messages.success(request, "درخواست تبادل ثبت شد و پس از بررسی مدیر نهایی می‌شود.")
        return redirect(exchange.get_absolute_url())

    return render(
        request,
        "exchanges/exchange_form.html",
        {"form": form, "skill": skill, "provider": skill.owner},
    )


@login_required
def exchange_list(request):
    queryset = _visible_exchanges(request.user).select_related(
        "requester", "provider", "skill"
    )
    return render(
        request,
        "exchanges/exchange_list.html",
        _list_context(
            request,
            queryset,
            page_title="همهٔ تبادلهای من",
            page_subtitle="درخواست‌هایی که فرستاده‌اید یا دریافت کرده‌اید.",
        ),
    )


@login_required
def exchange_sent(request):
    queryset = Exchange.objects.filter(requester=request.user).select_related(
        "provider", "skill"
    )
    return render(
        request,
        "exchanges/exchange_list.html",
        _list_context(
            request,
            queryset,
            page_title="درخواست‌های ارسالی من",
            page_subtitle="درخواست‌هایی که برای مهارت دیگران فرستاده‌اید.",
        ),
    )


@login_required
def exchange_received(request):
    queryset = Exchange.objects.filter(provider=request.user).select_related(
        "requester", "skill"
    )
    return render(
        request,
        "exchanges/exchange_list.html",
        _list_context(
            request,
            queryset,
            page_title="درخواست‌های دریافتی من",
            page_subtitle="درخواست‌هایی که دیگران برای مهارت‌های شما فرستاده‌اند.",
        ),
    )


@login_required
def exchange_history(request):
    queryset = _visible_exchanges(request.user).filter(
        status__in=[ExchangeStatus.APPROVED, ExchangeStatus.COMPLETED]
    ).select_related("requester", "provider", "skill")
    return render(
        request,
        "exchanges/exchange_list.html",
        _list_context(
            request,
            queryset,
            page_title="تاریخچهٔ تبادل",
            page_subtitle="تبادلهایی که توسط مدیریت تأیید یا تکمیل شده‌اند.",
            is_history=True,
        ),
    )


@login_required
def exchange_detail(request, pk: int):
    exchange = _get_exchange_for_user(request, pk)
    if exchange is None:
        messages.error(request, "به این درخواست دسترسی ندارید.")
        return redirect("exchanges:list")

    Message.objects.filter(exchange=exchange, is_read=False).exclude(
        sender=request.user
    ).update(is_read=True)

    if request.method == "POST":
        if "mark_completed" in request.POST:
            if exchange.status != ExchangeStatus.APPROVED:
                messages.error(request, "فقط تبادل تأییدشده قابل تکمیل شدن است.")
            else:
                exchange.status = ExchangeStatus.COMPLETED
                exchange.save()
                messages.success(request, "تبادل به‌عنوان تکمیل‌شده ثبت شد.")
            return redirect("exchanges:detail", pk=exchange.pk)

        form = MessageForm(request.POST)
        if not exchange.can_message:
            messages.error(request, "گفتگو برای این درخواست بسته شده است.")
        elif form.is_valid():
            message = form.save(commit=False)
            message.exchange = exchange
            message.sender = request.user
            message.save()
            recipient = exchange.counterpart_for(request.user)
            if recipient:
                Notification.objects.create(
                    user=recipient,
                    text=f"پیام جدید از {request.user.display_name} در «{exchange.title}»",
                    url=exchange.get_absolute_url(),
                )
            return redirect("exchanges:detail", pk=exchange.pk)
    else:
        form = MessageForm()

    context = {
        "exchange": exchange,
        "message_list": exchange.messages.select_related("sender"),
        "form": form,
        "counterpart": exchange.counterpart_for(request.user),
    }
    return render(request, "exchanges/exchange_detail.html", context)


@admin_required
def exchange_review(request, pk: int):
    exchange = get_object_or_404(
        Exchange.objects.select_related("requester", "provider", "skill"), pk=pk
    )
    form = ExchangeReviewForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        action = form.cleaned_data["action"]
        exchange.admin_note = form.cleaned_data["admin_note"].strip()
        exchange.reviewed_by = request.user
        exchange.reviewed_at = timezone.now()

        if action == "approve":
            exchange.status = ExchangeStatus.APPROVED
            messages.success(request, "درخواست تأیید شد.")
        elif action == "reject":
            exchange.status = ExchangeStatus.REJECTED
            messages.success(request, "درخواست رد شد.")
        else:
            exchange.status = ExchangeStatus.ADMIN_REVIEW
            messages.info(request, "درخواست در وضعیت بررسی قرار گرفت.")

        exchange.save()
        return redirect("exchanges:detail", pk=exchange.pk)

    return render(request, "exchanges/exchange_review.html", {"exchange": exchange, "form": form})


@login_required
def report_create(request):
    skill_pk = request.POST.get("skill") or request.GET.get("skill")
    user_pk = request.POST.get("target_user") or request.GET.get("user")

    if skill_pk:
        target_skill = get_object_or_404(Skill, pk=skill_pk)
        target_user = None
    elif user_pk:
        target_skill = None
        target_user = get_object_or_404(User.objects.filter(is_active=True), pk=user_pk)
    else:
        target_skill = None
        target_user = None

    if target_skill is None and target_user is None:
        empty_data = QueryDict("", mutable=True)
        form = ReportForm(request.POST or empty_data)
        form.add_error(None, "موضوع گزارش مشخص نیست.")
    else:
        report = Report(
            reporter=request.user, target_skill=target_skill, target_user=target_user
        )
        form = ReportForm(request.POST or None, instance=report)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "گزارش شما ثبت شد و توسط مدیریت بررسی می‌شود.")
            return redirect("home")

    return render(
        request,
        "exchanges/report_form.html",
        {"form": form, "target_skill": target_skill, "target_user": target_user},
    )

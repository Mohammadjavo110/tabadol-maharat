from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import LoginForm, ProfileForm, RegisterForm
from exchanges.models import Exchange, ExchangeStatus
from skills.models import Skill, Watch

User = get_user_model()


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"خوش آمدید {user.display_name}! حساب شما با موفقیت ساخته شد.")
        return redirect("accounts:dashboard")

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get("next") or request.POST.get("next")
        return redirect(next_url or "accounts:dashboard")

    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "از حساب خود خارج شدید.")
    return redirect("home")


@login_required
def dashboard(request):
    user = request.user
    my_skills = Skill.objects.filter(owner=user).select_related("category")
    sent = Exchange.objects.filter(requester=user).select_related("provider", "skill")
    received = Exchange.objects.filter(provider=user).select_related("requester", "skill")
    open_exchanges = (sent | received).filter(status=ExchangeStatus.PENDING).distinct()

    context = {
        "my_skills_count": my_skills.count(),
        "active_skills_count": my_skills.filter(is_active=True).count(),
        "sent_count": sent.count(),
        "received_count": received.count(),
        "open_exchanges": open_exchanges.order_by("-created_at")[:5],
        "recent_skills": my_skills.order_by("-created_at")[:5],
        "watches_count": Watch.objects.filter(user=user).count(),
        "notifications": user.notifications.all()[:5],
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "اطلاعات پروفایل با موفقیت ذخیره شد.")
        return redirect("accounts:profile")

    context = {
        "form": form,
        "profile_user": request.user,
        "skills_count": Skill.objects.filter(owner=request.user).count(),
    }
    return render(request, "accounts/profile.html", context)


def public_profile(request, pk: int):
    profile_user = get_object_or_404(
        User.objects.select_related("profile"), pk=pk, is_active=True
    )
    skills = Skill.objects.filter(owner=profile_user, is_active=True).select_related("category")
    context = {
        "profile_user": profile_user,
        "skills": skills[:12],
        "skills_count": skills.count(),
    }
    return render(request, "accounts/public_profile.html", context)


@login_required
def watches(request):
    watched = (
        Watch.objects.filter(user=request.user)
        .select_related("skill", "skill__owner", "skill__category")
        .order_by("-created_at")
    )
    return render(
        request,
        "accounts/watches.html",
        {"watches": watched, "watches_count": watched.count()},
    )


@login_required
def notifications(request):
    items = request.user.notifications.all()
    if request.method == "POST":
        items.update(is_read=True)
        messages.success(request, "همهٔ اعلان‌ها خوانده‌شده علامت خوردند.")
        return redirect("accounts:notifications")
    return render(
        request,
        "accounts/notifications.html",
        {"notifications": items, "unread_count": items.filter(is_read=False).count()},
    )

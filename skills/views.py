from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from config.settings import PAGINATE_BY
from skills.forms import SkillFilterForm, SkillForm
from skills.models import Skill, Watch
from skills.services import filter_skills, similar_skills, suggested_skills_for


def _paginate(request, queryset):
    return Paginator(queryset, PAGINATE_BY).get_page(request.GET.get("page"))


def skill_list(request):
    form = SkillFilterForm(request.GET or None)
    queryset = (
        Skill.objects.filter(is_active=True)
        .select_related("owner", "category")
        .prefetch_related("watches")
    )
    queryset = filter_skills(queryset, request.GET) if form.is_valid() else queryset

    context = {
        "form": form,
        "page_obj": _paginate(request, queryset),
        "suggestions": suggested_skills_for(request.user),
        "has_filters": form.has_filters,
    }
    return render(request, "skills/skill_list.html", context)


def skill_detail(request, pk: int):
    skill = get_object_or_404(
        Skill.objects.select_related("owner", "owner__profile", "category"), pk=pk
    )

    is_owner = request.user.is_authenticated and skill.owner_id == request.user.pk
    if not skill.is_active and not is_owner and not request.user.is_staff:
        messages.error(request, "این مورد غیرفعال شده است.")
        return redirect("skills:list")

    exchange = None
    existing = None
    if request.user.is_authenticated and not is_owner:
        existing = Watch.objects.filter(user=request.user, skill=skill).first()
        exchange = skill.exchanges.filter(requester=request.user).exclude(
            status__in=["rejected"]
        ).first()

    context = {
        "skill": skill,
        "is_owner": is_owner,
        "is_watched": existing is not None,
        "existing_exchange": exchange,
        "similar_skills": similar_skills(skill),
    }
    return render(request, "skills/skill_detail.html", context)


@login_required
def my_skills(request):
    skills = (
        Skill.objects.filter(owner=request.user)
        .select_related("category")
        .prefetch_related("watches")
    )
    counts = {
        "total": skills.count(),
        "active": skills.filter(is_active=True).count(),
        "inactive": skills.filter(is_active=False).count(),
    }
    context = {"skills": skills, "counts": counts, "page_obj": _paginate(request, skills)}
    return render(request, "skills/my_skills.html", context)


@login_required
def skill_create(request):
    form = SkillForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        skill = form.save(commit=False)
        skill.owner = request.user
        skill.save()
        messages.success(request, f"مهارت «{skill.title}» با موفقیت ثبت شد.")
        return redirect(skill.get_absolute_url())

    return render(
        request,
        "skills/skill_form.html",
        {"form": form, "page_title": "ثبت مهارت جدید", "submit_label": "ثبت مهارت"},
    )


@login_required
def skill_edit(request, pk: int):
    skill = get_object_or_404(Skill, pk=pk, owner=request.user)
    form = SkillForm(request.POST or None, instance=skill)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "تغییرات با موفقیت ذخیره شد.")
        return redirect(skill.get_absolute_url())

    return render(
        request,
        "skills/skill_form.html",
        {
            "form": form,
            "skill": skill,
            "page_title": "ویرایش مهارت",
            "submit_label": "ذخیرهٔ تغییرات",
        },
    )


@login_required
def skill_delete(request, pk: int):
    skill = get_object_or_404(Skill, pk=pk, owner=request.user)

    if request.method == "POST":
        title = skill.title
        skill.delete()
        messages.success(request, f"مهارت «{title}» حذف شد.")
        return redirect("skills:my_skills")

    return render(request, "skills/skill_confirm_delete.html", {"skill": skill})


@login_required
@require_POST
def toggle_watch(request, pk: int):
    skill = get_object_or_404(Skill, pk=pk, is_active=True)
    watch = Watch.objects.filter(user=request.user, skill=skill).first()

    if watch:
        watch.delete()
        messages.info(request, f"دنبال کردن «{skill.title}» لغو شد.")
    else:
        Watch.objects.create(user=request.user, skill=skill)
        messages.success(request, f"«{skill.title}» به مهارت‌های دنبال‌شده اضافه شد.")

    return redirect(skill.get_absolute_url())

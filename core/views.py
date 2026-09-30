from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import render

from exchanges.models import Exchange, ExchangeStatus
from skills.models import Category, Skill


def home(request):
    latest_skills = Skill.objects.filter(is_active=True).select_related("owner", "category")[:6]
    live_trade = (
        Exchange.objects.filter(status=ExchangeStatus.PENDING)
        .select_related("requester", "provider", "skill", "offered_skill")
        .order_by("-created_at")
        .first()
    )
    context = {
        "latest_skills": latest_skills,
        "live_trade": live_trade,
        "categories": Category.objects.annotate(skills_count=Count("skills"))[:8],
        "stats": {
            "users": get_user_model().objects.filter(is_active=True).count(),
            "skills": Skill.objects.filter(is_active=True).count(),
            "exchanges": Exchange.objects.filter(
                status__in=[ExchangeStatus.APPROVED, ExchangeStatus.COMPLETED]
            ).count(),
        },
        "search_query": request.GET.get("q", ""),
    }
    return render(request, "core/home.html", context)

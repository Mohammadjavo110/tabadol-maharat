from django.db.models import Q

from skills.models import Skill


def filter_skills(queryset, data: dict):
    """فیلتر و جستجوی فهرست مهارت‌ها بر اساس دادهٔ فرم."""
    query = (data.get("q") or "").strip()
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__icontains=query)
            | Q(owner__full_name__icontains=query)
        )

    category = data.get("category")
    if category:
        queryset = queryset.filter(category=category)

    skill_type = data.get("type")
    if skill_type:
        queryset = queryset.filter(type=skill_type)

    level = data.get("level")
    if level:
        queryset = queryset.filter(level__gte=int(level))

    city = (data.get("city") or "").strip()
    if city:
        queryset = queryset.filter(owner__profile__city__icontains=city)

    return queryset.distinct()


def _tag_query(tags: list[str]) -> Q:
    query = Q()
    for tag in tags:
        query |= Q(tags__icontains=tag)
    return query


def suggested_skills_for(user, limit: int = 6):
    """مهارت‌هایی که با مهارت‌های خود کاربر هم‌دسته یا هم‌برچسب‌اند."""
    if not user.is_authenticated:
        return Skill.objects.none()

    own_skills = Skill.objects.filter(owner=user)
    category_ids = set(own_skills.values_list("category_id", flat=True))
    tags = {tag.lower() for skill in own_skills for tag in skill.tags_list}

    queryset = Skill.objects.filter(is_active=True).exclude(owner=user)
    conditions = Q()

    if category_ids:
        conditions |= Q(category_id__in=category_ids)
    if tags:
        conditions |= _tag_query(sorted(tags))
    if not conditions:
        return queryset.order_by("-created_at")[:limit]

    return queryset.filter(conditions).distinct().order_by("-level", "-created_at")[:limit]


def similar_skills(skill, limit: int = 4):
    base = Skill.objects.filter(is_active=True).exclude(pk=skill.pk)
    matches = base.filter(Q(category=skill.category) | _tag_query(skill.tags_list)).distinct()
    return matches.order_by("-level", "-created_at")[:limit]

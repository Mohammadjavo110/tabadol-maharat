"""ابزارهای مشترک برای نوشتن تست‌ها."""

from django.contrib.auth import get_user_model

from skills.models import Category, Skill, SkillType

User = get_user_model()

TEST_PASSWORD = "Test#1405"


def make_user(email="user@test.ir", password=TEST_PASSWORD, **extra):
    return User.objects.create_user(email=email, password=password, **extra)


def make_admin(email="admin@test.ir", password=TEST_PASSWORD, full_name="مدیر"):
    return User.objects.create_superuser(email=email, password=password, full_name=full_name)


def make_category(title="برنامه‌نویسی"):
    return Category.objects.create(title=title)


def make_skill(owner, category, title="آموزش پایتون", **extra):
    defaults = {
        "type": SkillType.SKILL,
        "level": 4,
        "description": "توضیح کامل دربارهٔ مهارت و خدمات ارائه‌شده.",
        "tags": "پایتون, آموزش",
    }
    defaults.update(extra)
    return Skill.objects.create(owner=owner, category=category, title=title, **defaults)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import Profile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "full_name", "phone", "role", "is_staff", "is_active", "date_joined"]
    list_filter = ["role", "is_staff", "is_active", "date_joined"]
    search_fields = ["email", "full_name", "phone"]
    ordering = ["-date_joined"]
    readonly_fields = ["last_login", "date_joined"]
    filter_horizontal = ["groups", "user_permissions"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("اطلاعات شخصی", {"fields": ["full_name", "phone"]}),
        (
            "دسترسی و نقش",
            {"fields": ["role", "is_staff", "is_active", "is_superuser", "groups", "user_permissions"]},
        ),
        ("تاریخ‌ها", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "email",
                    "full_name",
                    "phone",
                    "password1",
                    "password2",
                    "role",
                    "is_staff",
                    "is_active",
                ],
            },
        ),
    ]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "city", "has_avatar", "created_at"]
    list_filter = ["city"]
    search_fields = ["user__email", "user__full_name", "city"]
    list_select_related = ["user"]

    @admin.display(boolean=True, description="تصویر")
    def has_avatar(self, obj: Profile) -> bool:
        return bool(obj.avatar)

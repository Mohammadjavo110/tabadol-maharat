from django.contrib import admin

from skills.models import Category, Skill, Watch


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "skills_count", "created_at"]
    search_fields = ["title", "description"]
    ordering = ["title"]

    @admin.display(description="تعداد مهارت")
    def skills_count(self, obj: Category) -> int:
        return obj.skills.count()


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "type", "category", "level", "is_active", "created_at"]
    list_filter = ["type", "level", "is_active", "category", "created_at"]
    search_fields = ["title", "description", "tags", "owner__email", "owner__full_name"]
    list_select_related = ["owner", "category"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["owner"]
    actions = ["activate_selected", "deactivate_selected"]

    @admin.action(description="فعال کردن")
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} مهارت فعال شد.")

    @admin.action(description="غیرفعال کردن")
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} مهارت غیرفعال شد.")


@admin.register(Watch)
class WatchAdmin(admin.ModelAdmin):
    list_display = ["user", "skill", "created_at"]
    list_select_related = ["user", "skill"]
    search_fields = ["user__email", "skill__title"]

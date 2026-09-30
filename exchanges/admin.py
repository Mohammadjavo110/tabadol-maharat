from django.contrib import admin

from exchanges.models import Exchange, Message, Notification, Report


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ["title", "requester", "provider", "status", "created_at", "reviewed_by"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "description", "requester__email", "provider__email"]
    list_select_related = ["requester", "provider", "skill"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["requester", "provider", "skill", "offered_skill"]
    actions = ["approve_selected", "reject_selected"]

    @admin.action(description="تأیید درخواست‌های انتخاب‌شده")
    def approve_selected(self, request, queryset):
        updated = 0
        for exchange in queryset:
            exchange.status = "approved"
            exchange.reviewed_by = request.user
            exchange.save()
            updated += 1
        self.message_user(request, f"{updated} درخواست تأیید شد.")

    @admin.action(description="رد درخواست‌های انتخاب‌شده")
    def reject_selected(self, request, queryset):
        updated = 0
        for exchange in queryset:
            exchange.status = "rejected"
            exchange.reviewed_by = request.user
            exchange.save()
            updated += 1
        self.message_user(request, f"{updated} درخواست رد شد.")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["sender", "exchange", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["body", "sender__email"]
    list_select_related = ["sender", "exchange"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["target_label", "reason", "reporter", "status", "created_at"]
    list_filter = ["status", "reason", "created_at"]
    search_fields = ["description", "reporter__email", "target_user__email", "target_skill__title"]
    list_select_related = ["reporter", "target_user", "target_skill", "handled_by"]
    actions = ["resolve_selected"]

    @admin.action(description="رسیدگی‌شده علامت زدن")
    def resolve_selected(self, request, queryset):
        from django.utils import timezone

        count = 0
        for report in queryset:
            report.status = "resolved"
            report.handled_by = request.user
            report.handled_at = timezone.now()
            report.save()
            count += 1
        self.message_user(request, f"{count} گزارش رسیدگی‌شده علامت خورد.")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "text", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["text", "user__email"]
    list_select_related = ["user"]

    @admin.action(description="خوانده‌شده علامت زدن")
    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} اعلان خوانده شد.")

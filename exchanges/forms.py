from django import forms
from django.core.exceptions import ValidationError

from core.forms import BootstrapFormMixin
from exchanges.models import Exchange, Message, Report, ReportReason
from skills.models import Skill


class ExchangeCreateForm(BootstrapFormMixin, forms.ModelForm):
    offered_skill = forms.ModelChoiceField(
        label="مهارتی که در ازای آن پیشنهاد می‌دهید (اختیاری)",
        required=False,
        queryset=Skill.objects.none(),
        help_text="اگر مهارتی دارید که می‌توانید در ازای این خدمت ارائه دهید، انتخاب کنید.",
    )

    class Meta:
        model = Exchange
        fields = ["title", "description", "offered_skill"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "مثلاً: تبادل آموزش پایتون با طراحی لوگو"}),
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "توضیح دهید چه چیزی از طرف مقابل می‌خواهید و چه پیشنهادی دارید.",
                }
            ),
        }
        labels = {"title": "عنوان درخواست", "description": "توضیحات"}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["offered_skill"].queryset = (
            Skill.objects.filter(owner=user, is_active=True).select_related("category")
        )

    def clean_title(self) -> str:
        title = (self.cleaned_data.get("title") or "").strip()
        if len(title) < 5:
            raise ValidationError("عنوان درخواست باید حداقل ۵ کاراکتر باشد.")
        return title

    def clean_description(self) -> str:
        description = (self.cleaned_data.get("description") or "").strip()
        if len(description) < 20:
            raise ValidationError("توضیحات باید حداقل ۲۰ کاراکتر باشد.")
        return description


class MessageForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "پیام خود را بنویسید…", "maxlength": 2000}
            )
        }
        labels = {"body": "متن پیام"}


class ReportForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "description"]
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": "مشکل را با جزئیات توضیح دهید."}
            )
        }
        labels = {"reason": "دلیل گزارش", "description": "توضیحات"}

    def clean_description(self) -> str:
        description = (self.cleaned_data.get("description") or "").strip()
        if len(description) < 10:
            raise ValidationError("توضیحات باید حداقل ۱۰ کاراکتر باشد.")
        return description


class ExchangeReviewForm(BootstrapFormMixin, forms.Form):
    action = forms.ChoiceField(
        label="تصمیم",
        choices=[("approve", "تأیید درخواست"), ("reject", "رد درخواست"), ("review", "شروع بررسی")],
        widget=forms.RadioSelect(),
    )
    admin_note = forms.CharField(
        label="یادداشت مدیر",
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="برای رد درخواست الزامی است و برای طرفین ارسال می‌شود.",
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("action") == "reject" and not (cleaned_data.get("admin_note") or "").strip():
            self.add_error("admin_note", "برای رد درخواست، دلیل را بنویسید.")
        return cleaned_data


__all__ = [
    "ExchangeCreateForm",
    "MessageForm",
    "ReportForm",
    "ExchangeReviewForm",
    "ReportReason",
]

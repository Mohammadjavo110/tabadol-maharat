from django import forms

from core.forms import BootstrapFormMixin
from skills.models import Category, Level, Skill, SkillType


class SkillForm(BootstrapFormMixin, forms.ModelForm):
    tags = forms.CharField(
        label="برچسب‌ها",
        required=False,
        max_length=200,
        help_text="کلیدواژه‌ها را با کاما جدا کنید. مثال: پایتون, آموزش, برنامه‌نویسی",
    )

    class Meta:
        model = Skill
        fields = ["title", "type", "category", "level", "description", "tags", "is_active"]
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 5, "placeholder": "توضیح دهید چه چیزی ارائه می‌دهید و چه انتظاری دارید."}
            ),
            "title": forms.TextInput(attrs={"placeholder": "مثلاً: آموزش پایتون از صفر"}),
        }
        labels = {
            "title": "عنوان",
            "type": "نوع",
            "category": "دسته‌بندی",
            "level": "سطح",
            "description": "توضیحات",
            "is_active": "این مورد فعال باشد",
        }

    def clean_tags(self) -> str:
        raw = self.cleaned_data.get("tags") or ""
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        return ",".join(dict.fromkeys(parts))[:200]

    def clean_description(self) -> str:
        description = (self.cleaned_data.get("description") or "").strip()
        if len(description) < 20:
            raise forms.ValidationError("توضیحات باید حداقل ۲۰ کاراکتر باشد.")
        return description


class SkillFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(
        label="جستجو",
        required=False,
        max_length=80,
        widget=forms.TextInput(
            attrs={"placeholder": "عنوان، توضیحات یا برچسب…", "type": "search"}
        ),
    )
    category = forms.ModelChoiceField(
        label="دسته‌بندی",
        required=False,
        queryset=Category.objects.all(),
        empty_label="همهٔ دسته‌بندی‌ها",
    )
    type = forms.ChoiceField(
        label="نوع",
        required=False,
        choices=[("", "مهارت و خدمت")] + list(SkillType.choices),
    )
    level = forms.ChoiceField(
        label="حداقل سطح",
        required=False,
        choices=[("", "هر سطح")] + [(str(value), label) for value, label in Level.choices],
    )
    city = forms.CharField(
        label="شهر",
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"placeholder": "مثلاً: تهران"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"

    @property
    def has_filters(self) -> bool:
        return any(self.data.get(name) for name in ("q", "category", "type", "level", "city"))

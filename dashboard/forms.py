from django import forms

from core.forms import BootstrapFormMixin
from skills.models import Category


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "مثلاً: برنامه‌نویسی و توسعهٔ وب"}),
            "description": forms.TextInput(attrs={"placeholder": "توضیح کوتاه دسته‌بندی"}),
        }
        labels = {"title": "عنوان", "description": "توضیح"}

    def clean_title(self) -> str:
        title = (self.cleaned_data.get("title") or "").strip()
        if len(title) < 3:
            raise forms.ValidationError("عنوان دسته‌بندی باید حداقل ۳ کاراکتر باشد.")
        return title

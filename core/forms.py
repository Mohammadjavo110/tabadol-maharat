from django import forms

CHECKBOX_INPUT_TYPES = {"checkbox", "radio"}


class BootstrapFormMixin:
    """کلاس‌های Bootstrap را به ویجت‌های فرم اضافه می‌کند و کلاس‌های پیش‌فرض را پاک می‌کند."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def _apply_bootstrap_classes(self) -> None:
        for name, field in self.fields.items():
            widget = field.widget
            input_type = getattr(widget, "input_type", None)

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
                continue
            if isinstance(widget, forms.RadioSelect):
                widget.attrs.setdefault("class", "form-check-input")
                continue
            if isinstance(widget, (forms.CheckboxSelectMultiple, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
                continue
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
                continue
            if input_type in CHECKBOX_INPUT_TYPES:
                widget.attrs.setdefault("class", "form-check-input")
                continue

            css_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{css_class} form-control".strip()
            if name in self.fields and self.fields[name].required is False:
                widget.attrs.setdefault("aria-describedby", f"{name}-help")


def plain_password_field(password_field):
    """فیلد رمز عبور را بدون نمایش دکمهٔ چشم پیکربندی می‌کند."""
    password_field.widget.render_value = False
    return password_field

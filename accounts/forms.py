from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from core.forms import BootstrapFormMixin

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="ایمیل یا موبایل",
        max_length=150,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "placeholder": "example@mail.com یا 09121234567",
            }
        ),
    )
    password = forms.CharField(
        label="رمز عبور",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "ایمیل، موبایل یا رمز عبور درست نیست.",
        "inactive": "حساب کاربری شما غیرفعال شده است. با پشتیبانی تماس بگیرید.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["password"].widget.attrs["class"] = "form-control"

    def clean_username(self) -> str:
        return (self.cleaned_data.get("username") or "").strip()


class RegisterForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(
        label="نام و نام خانوادگی",
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "مثلاً: سارا محمدی"}),
    )
    email = forms.EmailField(
        label="ایمیل",
        widget=forms.EmailInput(attrs={"placeholder": "example@mail.com"}),
    )
    phone = forms.CharField(
        label="شمارهٔ موبایل",
        max_length=11,
        help_text="با ۰۹ شروع شود و ۱۱ رقم باشد. برای ورود با موبایل استفاده می‌شود.",
        widget=forms.TextInput(attrs={"placeholder": "09121234567", "inputmode": "numeric"}),
    )
    password1 = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="حداقل ۸ کاراکتر و ترکیبی از حرف و عدد.",
    )
    password2 = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("کاربری با این ایمیل قبلاً ثبت‌نام کرده است.")
        return email

    def clean_phone(self) -> str:
        phone = self.cleaned_data["phone"].strip()
        if not phone.isdigit():
            raise ValidationError("شمارهٔ موبایل فقط باید شامل رقم باشد.")
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("کاربری با این شمارهٔ موبایل قبلاً ثبت‌نام کرده است.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "تکرار رمز عبور با رمز عبور یکسان نیست.")

        if password1:
            try:
                password_validation.validate_password(password1)
            except ValidationError as error:
                self.add_error("password1", error)

        return cleaned_data

    def save(self) -> User:
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            phone=self.cleaned_data["phone"],
            full_name=self.cleaned_data["full_name"],
            password=self.cleaned_data["password1"],
        )


class ProfileForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(label="نام و نام خانوادگی", max_length=120)
    email = forms.EmailField(label="ایمیل", disabled=True)
    phone = forms.CharField(label="شمارهٔ موبایل", max_length=11, required=False)
    city = forms.CharField(label="شهر", max_length=64, required=False)
    bio = forms.CharField(
        label="دربارهٔ من",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="حداکثر ۵۰۰ کاراکتر.",
    )
    avatar = forms.ImageField(
        label="تصویر پروفایل",
        required=False,
        help_text="تصویر مربعی با حجم کمتر از ۲ مگابایت.",
    )

    def __init__(self, *args, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["email"].initial = user.email
        self.fields["phone"].initial = user.phone or ""

    def clean_phone(self) -> str:
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return ""
        if not phone.isdigit() or not (phone.startswith("09") and len(phone) == 11):
            raise ValidationError("شمارهٔ موبایل باید ۱۱ رقم و با ۰۹ شروع شود.")
        clash = User.objects.filter(phone=phone).exclude(pk=self.user.pk)
        if clash.exists():
            raise ValidationError("این شمارهٔ موبایل برای کاربر دیگری ثبت شده است.")
        return phone

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and avatar.size > 2 * 1024 * 1024:
            raise ValidationError("حجم تصویر نباید بیشتر از ۲ مگابایت باشد.")
        return avatar

    def save(self) -> User:
        user = self.user
        user.full_name = self.cleaned_data["full_name"]
        user.phone = self.cleaned_data["phone"] or None
        user.save()

        profile = user.profile
        profile.city = self.cleaned_data["city"]
        profile.bio = self.cleaned_data["bio"]
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            profile.avatar = avatar
        profile.save()
        return user

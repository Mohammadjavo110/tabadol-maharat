"""اعتبارسنجهای رمز عبور با پیام‌های فارسی."""

from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    MinimumLengthValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
)


class PersianUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
    def get_error_message(self) -> str:
        return "رمز عبور بیش از حد شبیه اطلاعات شخصی شماست."


class PersianMinimumLengthValidator(MinimumLengthValidator):
    def get_error_message(self) -> str:
        return "رمز عبور باید حداقل %(min_length)d کاراکتر باشد."


class PersianCommonPasswordValidator(CommonPasswordValidator):
    def get_error_message(self) -> str:
        return "این رمز عبور بیش از حد حدس‌زدنی است. رمز دیگری انتخاب کنید."


class PersianNumericPasswordValidator(NumericPasswordValidator):
    def get_error_message(self) -> str:
        return "رمز عبور نباید تماماً از رقم باشد."

from decimal import Decimal

from django import forms


class RatingDecimalField(forms.DecimalField):
    """
    Поле принимает дробные оценки с точкой или запятой.

    Примеры:
        3.5
        3,5
        5
    """

    default_error_messages = {
        "invalid": "Введите число, например 4,5 или 4.5.",
        "min_value": (
            "Оценка не может быть меньше %(limit_value)s."
        ),
        "max_value": (
            "Оценка не может быть больше %(limit_value)s."
        ),
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("min_value", Decimal("1.0"))
        kwargs.setdefault("max_value", Decimal("5.0"))
        kwargs.setdefault("max_digits", 2)
        kwargs.setdefault("decimal_places", 1)

        kwargs.setdefault(
            "widget",
            forms.TextInput(
                attrs={
                    "class": "form-control",
                    "inputmode": "decimal",
                    "placeholder": "Например: 4,5",
                    "autocomplete": "off",
                }
            ),
        )

        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip()
            value = value.replace(" ", "")
            value = value.replace(",", ".")

        return super().to_python(value)
from decimal import Decimal

from django import forms

from .models import Survey
from .models import SurveySample


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


class SurveyForm(forms.ModelForm):
    """
    Форма создания и редактирования опроса.

    Статус не редактируется напрямую.
    Для изменения статуса используются отдельные кнопки.
    """

    class Meta:
        model = Survey

        fields = (
            "title",
            "description",
            "allow_multiple_submissions",
        )

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Например: Дегустация супа-пюре"
                    ),
                    "autofocus": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Краткое описание формы для участников"
                    ),
                }
            ),
            "allow_multiple_submissions": (
                forms.CheckboxInput(
                    attrs={
                        "class": "form-check-input",
                    }
                )
            ),
        }


class SurveySampleForm(forms.ModelForm):
    """
    Форма создания и редактирования образца.
    """

    class Meta:
        model = SurveySample

        fields = (
            "name",
            "description",
            "is_active",
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Образец №1",
                    "autofocus": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Название продукции, рецептура, "
                        "условия хранения и другие сведения"
                    ),
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
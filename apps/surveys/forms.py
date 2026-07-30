from decimal import Decimal
from .models import SurveyProtocol
from django import forms

from .models import Survey, SurveyQuestion, SurveySample


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


class PublicSurveyForm(forms.Form):
    """
    Динамическая форма для заполнения участником.

    Для каждого активного образца создаётся отдельный набор
    активных вопросов.
    """

    full_name = forms.CharField(
        label="ФИО",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "name",
                "placeholder": "Иванов Иван Иванович",
            }
        ),
    )

    position = forms.CharField(
        label="Должность",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "organization-title",
                "placeholder": "Инженер-технолог",
            }
        ),
    )

    def __init__(self, *args, survey, **kwargs):
        self.survey = survey

        super().__init__(*args, **kwargs)

        self.samples = list(
            survey.samples.filter(
                is_active=True,
            ).order_by(
                "order",
                "id",
            )
        )

        self.questions = list(
            survey.questions.filter(
                is_active=True,
            ).order_by(
                "order",
                "id",
            )
        )

        for sample in self.samples:
            for question in self.questions:
                field_name = self.get_answer_field_name(
                    sample_id=sample.pk,
                    question_id=question.pk,
                )

                if (
                    question.question_type
                    == SurveyQuestion.QuestionType.RATING
                ):
                    self.fields[field_name] = RatingDecimalField(
                        label=question.title,
                        required=question.is_required,
                        min_value=question.minimum_value,
                        max_value=question.maximum_value,
                        help_text=(
                            f"Оценка от "
                            f"{question.minimum_value} "
                            f"до {question.maximum_value}"
                        ),
                    )
                else:
                    self.fields[field_name] = forms.CharField(
                        label=question.title,
                        required=question.is_required,
                        widget=forms.Textarea(
                            attrs={
                                "class": "form-control",
                                "rows": 3,
                                "placeholder": (
                                    "Комментарий необязателен"
                                ),
                            }
                        ),
                    )

    @staticmethod
    def get_answer_field_name(
        sample_id,
        question_id,
    ):
        return (
            f"sample_{sample_id}_"
            f"question_{question_id}"
        )

    def get_sample_blocks(self):
        """
        Возвращает данные для удобного вывода в шаблоне.
        """

        blocks = []

        for sample in self.samples:
            fields = []

            for question in self.questions:
                field_name = self.get_answer_field_name(
                    sample_id=sample.pk,
                    question_id=question.pk,
                )

                fields.append(
                    {
                        "question": question,
                        "field": self[field_name],
                    }
                )

            blocks.append(
                {
                    "sample": sample,
                    "fields": fields,
                }
            )

        return blocks

class SurveyProtocolForm(forms.ModelForm):
    """
    Форма реквизитов итогового протокола.
    """

    class Meta:
        model = SurveyProtocol

        fields = (
            "document_code",
            "protocol_number",
            "protocol_date",
            "responsible_employee",
            "tasting_goal",
            "room_conditions",
            "product_conditions",
            "conclusion",
            "signer_position",
            "signer_name",
        )

        widgets = {
            "document_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "КК-Ф-020",
                }
            ),
            "protocol_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "304",
                    "autofocus": True,
                }
            ),
            "protocol_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "class": "form-control",
                    "type": "date",
                },
            ),
            "responsible_employee": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Мальцева Е.С.",
                }
            ),
            "tasting_goal": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Органолептическая оценка продукции..."
                    ),
                }
            ),
            "room_conditions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "product_conditions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Температура готовых блюд..."
                    ),
                }
            ),
            "conclusion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "По результатам дегустации..."
                    ),
                }
            ),
            "signer_position": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Нач. ОРП",
                }
            ),
            "signer_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Холина О.В.",
                }
            ),
        }

        localized_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["protocol_date"].input_formats = [
            "%Y-%m-%d",
            "%d.%m.%Y",
        ]

    def clean_protocol_number(self):
        value = self.cleaned_data.get(
            "protocol_number",
            "",
        ).strip()

        if not value:
            raise forms.ValidationError(
                "Укажите номер протокола."
            )

        return value

    def clean_responsible_employee(self):
        value = self.cleaned_data.get(
            "responsible_employee",
            "",
        ).strip()

        if not value:
            raise forms.ValidationError(
                "Укажите ответственного сотрудника."
            )

        return value

    def clean_tasting_goal(self):
        value = self.cleaned_data.get(
            "tasting_goal",
            "",
        ).strip()

        if not value:
            raise forms.ValidationError(
                "Укажите цель дегустации."
            )

        return value

    def clean_conclusion(self):
        value = self.cleaned_data.get(
            "conclusion",
            "",
        ).strip()

        if not value:
            raise forms.ValidationError(
                "Укажите заключение."
            )

        return value


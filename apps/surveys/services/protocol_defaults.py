from django.utils import timezone

from apps.surveys.models import SurveyProtocol


COPIED_PROTOCOL_FIELDS = (
    "document_code",
    "responsible_employee",
    "tasting_goal",
    "room_conditions",
    "product_conditions",
    "conclusion",
    "signer_position",
    "signer_name",
)


def get_previous_protocol(*, survey):
    """
    Возвращает последний заполненный протокол другой формы.

    Сначала учитывается дата протокола, затем ID записи.
    Текущая форма исключается.
    """

    return (
        SurveyProtocol.objects
        .exclude(survey=survey)
        .exclude(protocol_number="")
        .order_by(
            "-protocol_date",
            "-id",
        )
        .first()
    )


def get_next_protocol_number() -> str:
    """
    Возвращает максимальный числовой номер протокола + 1.

    Нечисловые номера, например 304-А, в автоматическом
    расчёте не учитываются.
    """

    protocol_numbers = (
        SurveyProtocol.objects
        .exclude(protocol_number="")
        .values_list(
            "protocol_number",
            flat=True,
        )
    )

    numeric_numbers = []

    for value in protocol_numbers:
        normalized_value = str(value).strip()

        if normalized_value.isdigit():
            numeric_numbers.append(
                int(normalized_value)
            )

    if not numeric_numbers:
        return "1"

    return str(max(numeric_numbers) + 1)


def build_protocol_initial_data(*, survey):
    """
    Формирует начальные значения нового протокола.
    """

    previous_protocol = get_previous_protocol(
        survey=survey,
    )

    initial_data = {
        "protocol_number": get_next_protocol_number(),
        "protocol_date": timezone.localdate(),
    }

    if previous_protocol is None:
        initial_data.update(
            {
                "document_code": "КК-Ф-020",
                "signer_position": "Нач. ОРП",
            }
        )

        return initial_data

    for field_name in COPIED_PROTOCOL_FIELDS:
        initial_data[field_name] = getattr(
            previous_protocol,
            field_name,
        )

    return initial_data
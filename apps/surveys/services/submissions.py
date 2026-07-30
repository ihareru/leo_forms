from django.db import transaction

from apps.surveys.models import Answer, Submission, SurveyQuestion


def get_client_ip(request):
    """
    Возвращает IP-адрес клиента.

    При работе через Nginx сначала проверяется
    заголовок X-Forwarded-For.
    """

    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR",
        "",
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


@transaction.atomic
def create_submission_from_form(
    *,
    survey,
    form,
    request,
):
    """
    Создаёт заполнение и все связанные ответы
    в одной транзакции.
    """

    submission = Submission.objects.create(
        survey=survey,
        full_name=form.cleaned_data["full_name"].strip(),
        position=form.cleaned_data["position"].strip(),
        ip_address=get_client_ip(request),
        user_agent=request.META.get(
            "HTTP_USER_AGENT",
            "",
        )[:2000],
    )

    answers = []

    for sample in form.samples:
        for question in form.questions:
            field_name = form.get_answer_field_name(
                sample_id=sample.pk,
                question_id=question.pk,
            )

            value = form.cleaned_data.get(field_name)

            answer = Answer(
                submission=submission,
                sample=sample,
                question=question,
            )

            if (
                question.question_type
                == SurveyQuestion.QuestionType.RATING
            ):
                answer.numeric_value = value
            else:
                answer.text_value = (
                    value.strip()
                    if isinstance(value, str)
                    else ""
                )

            answers.append(answer)

    Answer.objects.bulk_create(answers)

    return submission
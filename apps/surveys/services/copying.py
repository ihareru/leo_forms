from django.db import transaction

from apps.surveys.models import Survey
from apps.surveys.models import SurveyQuestion
from apps.surveys.models import SurveySample


@transaction.atomic
def copy_survey(
    *,
    source_survey,
    owner,
):
    """
    Создаёт независимую копию формы.

    Копируются:
    - название;
    - описание;
    - настройка повторных ответов;
    - образцы;
    - вопросы.

    Не копируются:
    - ответы;
    - реквизиты протокола;
    - DOCX-протоколы;
    - статус;
    - публичный UUID;
    - даты публикации и закрытия.
    """

    copied_survey = Survey.objects.create(
        owner=owner,
        title=f"Копия — {source_survey.title}",
        description=source_survey.description,
        status=Survey.Status.DRAFT,
        allow_multiple_submissions=(
            source_survey.allow_multiple_submissions
        ),
    )

    # Сигнал post_save уже создал стандартные вопросы.
    # Удаляем их перед копированием реального набора вопросов.
    copied_survey.questions.all().delete()

    source_samples = (
        source_survey.samples
        .order_by(
            "order",
            "id",
        )
    )

    copied_samples = [
        SurveySample(
            survey=copied_survey,
            name=sample.name,
            description=sample.description,
            order=sample.order,
            is_active=sample.is_active,
        )
        for sample in source_samples
    ]

    SurveySample.objects.bulk_create(
        copied_samples,
    )

    source_questions = (
        source_survey.questions
        .order_by(
            "order",
            "id",
        )
    )

    copied_questions = [
        SurveyQuestion(
            survey=copied_survey,
            title=question.title,
            code=question.code,
            question_type=question.question_type,
            is_required=question.is_required,
            order=question.order,
            minimum_value=question.minimum_value,
            maximum_value=question.maximum_value,
            decimal_places=question.decimal_places,
            is_active=question.is_active,
        )
        for question in source_questions
    ]

    SurveyQuestion.objects.bulk_create(
        copied_questions,
    )

    return copied_survey
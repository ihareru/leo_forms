from decimal import Decimal
from decimal import ROUND_HALF_UP

from django.db.models import Avg
from django.db.models import Count
from django.db.models import Q

from apps.surveys.models import Answer
from apps.surveys.models import SurveyQuestion


TWO_DECIMAL_PLACES = Decimal("0.01")


def round_score(value):
    """
    Округляет рассчитанное среднее значение
    до двух знаков после запятой.

    Примеры:
    4.975 -> 4.98
    4.994 -> 4.99
    4.995 -> 5.00
    """

    if value is None:
        return None

    return Decimal(value).quantize(
        TWO_DECIMAL_PLACES,  # noqa: F821
        rounding=ROUND_HALF_UP,
    )


def get_survey_results(survey):
    """
    Возвращает сводные результаты формы.

    Из расчётов исключаются ответы с is_excluded=True.
    """

    rating_questions = list(
        survey.questions.filter(
            is_active=True,
            question_type=SurveyQuestion.QuestionType.RATING,
        ).order_by(
            "order",
            "id",
        )
    )

    text_questions = list(
        survey.questions.filter(
            question_type=SurveyQuestion.QuestionType.TEXT,
        ).order_by(
            "order",
            "id",
        )
    )

    samples = list(
        survey.samples.order_by(
            "order",
            "id",
        )
    )

    result_rows = []

    for sample in samples:
        score_cells = []
        raw_score_values = []

        for question in rating_questions:
            average = (
                Answer.objects.filter(
                    sample=sample,
                    question=question,
                    submission__survey=survey,
                    submission__is_excluded=False,
                    numeric_value__isnull=False,
                )
                .aggregate(
                    average=Avg("numeric_value"),
                )
                .get("average")
            )

            if average is not None:
                raw_score_values.append(Decimal(average))

            score_cells.append(
                {
                    "question": question,
                    "average": round_score(average),
                }
            )

        overall_average = None

        if raw_score_values:
            overall_average = round_score(sum(raw_score_values) / len(raw_score_values))

        comments_queryset = Answer.objects.filter(
            sample=sample,
            submission__survey=survey,
            submission__is_excluded=False,
            question__question_type=(
                SurveyQuestion.QuestionType.TEXT
            ),
        ).exclude(
            text_value="",
        ).order_by(
            "submission__submitted_at",
            "id",
        )

        comments = list(
            comments_queryset.values_list(
                "text_value",
                flat=True,
            )
        )

        result_rows.append(
            {
                "sample": sample,
                "scores": score_cells,
                "overall_average": overall_average,
                "comments": comments,
            }
        )

    submissions_summary = survey.submissions.aggregate(
        total=Count("id"),
        included=Count(
            "id",
            filter=Q(is_excluded=False),
        ),
        excluded=Count(
            "id",
            filter=Q(is_excluded=True),
        ),
    )

    return {
        "rating_questions": rating_questions,
        "text_questions": text_questions,
        "rows": result_rows,
        "submissions_total": submissions_summary["total"],
        "submissions_included": submissions_summary["included"],
        "submissions_excluded": submissions_summary["excluded"],
    }
from apps.surveys.models import SurveyQuestion


DEFAULT_QUESTIONS = [
    {
        "title": "Внешний вид",
        "code": SurveyQuestion.StandardCode.APPEARANCE,
        "question_type": SurveyQuestion.QuestionType.RATING,
        "is_required": True,
        "order": 10,
        "minimum_value": "1.0",
        "maximum_value": "5.0",
        "decimal_places": 1,
    },
    {
        "title": "Цвет",
        "code": SurveyQuestion.StandardCode.COLOR,
        "question_type": SurveyQuestion.QuestionType.RATING,
        "is_required": True,
        "order": 20,
        "minimum_value": "1.0",
        "maximum_value": "5.0",
        "decimal_places": 1,
    },
    {
        "title": "Консистенция",
        "code": SurveyQuestion.StandardCode.CONSISTENCY,
        "question_type": SurveyQuestion.QuestionType.RATING,
        "is_required": True,
        "order": 30,
        "minimum_value": "1.0",
        "maximum_value": "5.0",
        "decimal_places": 1,
    },
    {
        "title": "Запах",
        "code": SurveyQuestion.StandardCode.SMELL,
        "question_type": SurveyQuestion.QuestionType.RATING,
        "is_required": True,
        "order": 40,
        "minimum_value": "1.0",
        "maximum_value": "5.0",
        "decimal_places": 1,
    },
    {
        "title": "Вкус",
        "code": SurveyQuestion.StandardCode.TASTE,
        "question_type": SurveyQuestion.QuestionType.RATING,
        "is_required": True,
        "order": 50,
        "minimum_value": "1.0",
        "maximum_value": "5.0",
        "decimal_places": 1,
    },
    {
        "title": "Комментарии к балловым оценкам",
        "code": SurveyQuestion.StandardCode.COMMENT,
        "question_type": SurveyQuestion.QuestionType.TEXT,
        "is_required": False,
        "order": 60,
        "minimum_value": None,
        "maximum_value": None,
        "decimal_places": 0,
    },
]


def create_default_questions(survey):
    """
    Создаёт стандартные вопросы для новой формы.

    ignore_conflicts позволяет безопасно вызвать функцию повторно.
    """

    questions = [
        SurveyQuestion(
            survey=survey,
            **question_data,
        )
        for question_data in DEFAULT_QUESTIONS
    ]

    SurveyQuestion.objects.bulk_create(
        questions,
        ignore_conflicts=True,
    )
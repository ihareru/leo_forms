from django.shortcuts import get_object_or_404

from apps.surveys.models import Survey


def get_surveys_available_to_user(user):
    """
    Возвращает формы, доступные пользователю.

    Администратор видит все формы.
    Обычный пользователь видит только свои формы.
    """

    queryset = Survey.objects.select_related("owner")

    if user.is_portal_admin:
        return queryset

    return queryset.filter(owner=user)


def get_survey_available_to_user(user, survey_id):
    """
    Возвращает форму, если пользователь имеет к ней доступ.

    При отсутствии доступа возвращается HTTP 404.
    """

    queryset = get_surveys_available_to_user(user)

    return get_object_or_404(
        queryset,
        pk=survey_id,
    )
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.db.models import Max
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import SurveyForm
from .forms import SurveySampleForm
from .models import Survey
from .models import SurveySample
from .services.access import get_survey_available_to_user
from .services.access import get_surveys_available_to_user


@login_required
def survey_list(request):
    """
    Список доступных пользователю форм.
    """

    surveys = (
        get_surveys_available_to_user(request.user)
        .annotate(
            samples_total=Count(
                "samples",
                distinct=True,
            ),
        )
        .order_by("-created_at")
    )

    context = {
        "surveys": surveys,
    }

    return render(
        request,
        "surveys/survey_list.html",
        context,
    )


@login_required
def survey_create(request):
    """
    Создание новой формы.
    """

    if request.method == "POST":
        form = SurveyForm(request.POST)

        if form.is_valid():
            survey = form.save(commit=False)
            survey.owner = request.user
            survey.save()

            messages.success(
                request,
                "Форма создана. Теперь добавьте образцы.",
            )

            return redirect(
                "surveys:survey_edit",
                survey_id=survey.pk,
            )
    else:
        form = SurveyForm()

    context = {
        "form": form,
        "page_title": "Создание формы",
        "submit_text": "Создать форму",
    }

    return render(
        request,
        "surveys/survey_form.html",
        context,
    )


@login_required
def survey_edit(request, survey_id):
    """
    Редактирование основной информации формы.

    Редактирование разрешено в любом статусе.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    if request.method == "POST":
        form = SurveyForm(
            request.POST,
            instance=survey,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Изменения формы сохранены.",
            )

            return redirect(
                "surveys:survey_edit",
                survey_id=survey.pk,
            )
    else:
        form = SurveyForm(instance=survey)

    samples = survey.samples.order_by(
        "order",
        "id",
    )

    questions = survey.questions.order_by(
        "order",
        "id",
    )

    context = {
        "survey": survey,
        "form": form,
        "samples": samples,
        "questions": questions,
    }

    return render(
        request,
        "surveys/survey_edit.html",
        context,
    )


@login_required
def sample_create(request, survey_id):
    """
    Добавление образца к форме.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    if request.method == "POST":
        form = SurveySampleForm(request.POST)

        if form.is_valid():
            sample = form.save(commit=False)
            sample.survey = survey

            maximum_order = (
                survey.samples.aggregate(
                    maximum=Max("order"),
                )["maximum"]
                or 0
            )

            sample.order = maximum_order + 10
            sample.save()

            messages.success(
                request,
                "Образец добавлен.",
            )

            return redirect(
                "surveys:survey_edit",
                survey_id=survey.pk,
            )
    else:
        form = SurveySampleForm()

    context = {
        "survey": survey,
        "form": form,
        "page_title": "Добавление образца",
        "submit_text": "Добавить образец",
    }

    return render(
        request,
        "surveys/sample_form.html",
        context,
    )


@login_required
def sample_edit(request, survey_id, sample_id):
    """
    Редактирование образца.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    sample = survey.samples.filter(
        pk=sample_id,
    ).first()

    if sample is None:
        from django.http import Http404

        raise Http404("Образец не найден.")

    if request.method == "POST":
        form = SurveySampleForm(
            request.POST,
            instance=sample,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Изменения образца сохранены.",
            )

            return redirect(
                "surveys:survey_edit",
                survey_id=survey.pk,
            )
    else:
        form = SurveySampleForm(instance=sample)

    context = {
        "survey": survey,
        "sample": sample,
        "form": form,
        "page_title": "Редактирование образца",
        "submit_text": "Сохранить изменения",
    }

    return render(
        request,
        "surveys/sample_form.html",
        context,
    )


@login_required
def sample_delete(request, survey_id, sample_id):
    """
    Удаление образца.

    На текущем этапе ответов ещё нет, поэтому образец
    можно удалять физически.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    sample = survey.samples.filter(
        pk=sample_id,
    ).first()

    if sample is None:
        from django.http import Http404

        raise Http404("Образец не найден.")

    if request.method == "POST":
        sample_name = sample.name
        sample.delete()

        messages.success(
            request,
            f'Образец «{sample_name}» удалён.',
        )

        return redirect(
            "surveys:survey_edit",
            survey_id=survey.pk,
        )

    context = {
        "survey": survey,
        "sample": sample,
    }

    return render(
        request,
        "surveys/sample_confirm_delete.html",
        context,
    )


@login_required
@require_POST
def sample_move_up(request, survey_id, sample_id):
    """
    Перемещение образца на одну позицию вверх.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    sample = survey.samples.filter(
        pk=sample_id,
    ).first()

    if sample is None:
        from django.http import Http404

        raise Http404("Образец не найден.")

    previous_sample = (
        survey.samples
        .filter(order__lt=sample.order)
        .order_by("-order", "-id")
        .first()
    )

    if previous_sample is not None:
        swap_sample_order(
            survey=survey,
            first_sample=sample,
            second_sample=previous_sample,
        )

    return redirect(
        "surveys:survey_edit",
        survey_id=survey.pk,
    )


@login_required
@require_POST
def sample_move_down(request, survey_id, sample_id):
    """
    Перемещение образца на одну позицию вниз.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    sample = survey.samples.filter(
        pk=sample_id,
    ).first()

    if sample is None:
        from django.http import Http404

        raise Http404("Образец не найден.")

    next_sample = (
        survey.samples
        .filter(order__gt=sample.order)
        .order_by("order", "id")
        .first()
    )

    if next_sample is not None:
        swap_sample_order(
            survey=survey,
            first_sample=sample,
            second_sample=next_sample,
        )

    return redirect(
        "surveys:survey_edit",
        survey_id=survey.pk,
    )


def swap_sample_order(
    survey,
    first_sample,
    second_sample,
):
    """
    Безопасно меняет порядок двух образцов.

    Временное значение нужно из-за ограничения уникальности
    сочетания survey + order.
    """

    first_order = first_sample.order
    second_order = second_sample.order

    maximum_order = (
        survey.samples.aggregate(
            maximum=Max("order"),
        )["maximum"]
        or 0
    )

    temporary_order = maximum_order + 1000

    with transaction.atomic():
        first_sample.order = temporary_order
        first_sample.save(
            update_fields=[
                "order",
                "updated_at",
            ]
        )

        second_sample.order = first_order
        second_sample.save(
            update_fields=[
                "order",
                "updated_at",
            ]
        )

        first_sample.order = second_order
        first_sample.save(
            update_fields=[
                "order",
                "updated_at",
            ]
        )


@login_required
@require_POST
def survey_publish(request, survey_id):
    """
    Публикация формы.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    try:
        survey.publish()
    except ValidationError as error:
        messages.error(
            request,
            " ".join(error.messages),
        )
    else:
        messages.success(
            request,
            "Форма опубликована.",
        )

    return redirect(
        "surveys:survey_edit",
        survey_id=survey.pk,
    )


@login_required
@require_POST
def survey_close(request, survey_id):
    """
    Закрытие сбора ответов.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    try:
        survey.close()
    except ValidationError as error:
        messages.error(
            request,
            " ".join(error.messages),
        )
    else:
        messages.success(
            request,
            "Сбор ответов закрыт.",
        )

    return redirect(
        "surveys:survey_edit",
        survey_id=survey.pk,
    )


@login_required
@require_POST
def survey_archive(request, survey_id):
    """
    Перевод формы в архив.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    survey.archive()

    messages.success(
        request,
        "Форма перемещена в архив.",
    )

    return redirect(
        "surveys:survey_list",
    )
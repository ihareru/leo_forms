from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Max
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import Http404, HttpResponse
from django.urls import reverse
from .forms import SurveyForm, SurveySampleForm, PublicSurveyForm
from .models import Survey, SurveySample, Submission
from .services.access import (
    get_survey_available_to_user,
    get_surveys_available_to_user
)
from .services.submissions import create_submission_from_form
from .services.excel_reports import build_survey_excel_report
from .services.qr_codes import generate_qr_code_png
from .services.results import get_survey_results


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
            submissions_total=Count(
                "submissions",
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

        if sample.answers.exists():
            sample.is_active = False
            sample.save(
                update_fields=[
                    "is_active",
                    "updated_at",
                ]
            )

            messages.warning(
                request,
                (
                    f"Образец «{sample_name}» содержит ответы "
                    f"и поэтому был скрыт, а не удалён."
                ),
            )
        else:
            sample.delete()

            messages.success(
                request,
                f"Образец «{sample_name}» удалён.",
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

def public_survey(request, public_id):
    """
    Публичная страница заполнения формы.

    Авторизация участника не требуется.
    """

    survey = get_object_or_404(
        Survey.objects.prefetch_related(
            "samples",
            "questions",
        ),
        public_id=public_id,
    )

    if survey.status == Survey.Status.DRAFT:
        raise Http404("Форма не опубликована.")

    if survey.status in {
        Survey.Status.CLOSED,
        Survey.Status.ARCHIVED,
    }:
        if not survey.samples.filter(is_active=True).exists():
            return render(
                request,
                "surveys/public_survey_closed.html",
                {
                    "survey": survey,
                },
            )

        return render(
            request,
            "surveys/public_survey_closed.html",
            {
                "survey": survey,
            },
        )

    session_key = (
        f"survey_{survey.public_id}_submitted"
    )

    already_submitted = request.session.get(
        session_key,
        False,
    )

    if (
        already_submitted
        and not survey.allow_multiple_submissions
    ):
        return render(
            request,
            "surveys/public_survey_already_submitted.html",
            {
                "survey": survey,
            },
        )

    if request.method == "POST":
        form = PublicSurveyForm(
            request.POST,
            survey=survey,
        )

        if form.is_valid():
            submission = create_submission_from_form(
                survey=survey,
                form=form,
                request=request,
            )

            request.session[session_key] = True
            request.session.modified = True

            return redirect(
                "public_survey_success",
                public_id=survey.public_id,
                submission_id=submission.public_id,
            )
    else:
        form = PublicSurveyForm(
            survey=survey,
        )

    context = {
        "survey": survey,
        "form": form,
        "sample_blocks": form.get_sample_blocks(),
    }

    return render(
        request,
        "surveys/public_survey.html",
        context,
    )


def public_survey_success(
    request,
    public_id,
    submission_id,
):
    """
    Страница успешной отправки формы.
    """

    survey = get_object_or_404(
        Survey,
        public_id=public_id,
    )

    submission = get_object_or_404(
        survey.submissions,
        public_id=submission_id,
    )

    return render(
        request,
        "surveys/public_survey_success.html",
        {
            "survey": survey,
            "submission": submission,
        },
    )

@login_required
def survey_qr_code(request, survey_id):
    """
    Возвращает QR-код публичной ссылки в формате PNG.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    public_path = reverse(
        "public_survey",
        args=[
            survey.public_id,
        ],
    )

    public_url = request.build_absolute_uri(
        public_path,
    )

    image_data = generate_qr_code_png(
        public_url,
    )

    response = HttpResponse(
        image_data,
        content_type="image/png",
    )

    response["Content-Disposition"] = (
        f'inline; filename="survey-{survey.pk}-qr.png"'
    )

    return response

@login_required
def survey_qr_code_download(
    request,
    survey_id,
):
    """
    Скачивает QR-код в формате PNG.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    public_path = reverse(
        "public_survey",
        args=[
            survey.public_id,
        ],
    )

    public_url = request.build_absolute_uri(
        public_path,
    )

    image_data = generate_qr_code_png(
        public_url,
    )

    response = HttpResponse(
        image_data,
        content_type="image/png",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="survey-{survey.pk}-qr.png"'
    )

    return response

@login_required
def survey_qr_print(request, survey_id):
    """
    Страница печати QR-кода и публичной ссылки.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    public_path = reverse(
        "public_survey",
        args=[
            survey.public_id,
        ],
    )

    public_url = request.build_absolute_uri(
        public_path,
    )

    context = {
        "survey": survey,
        "public_url": public_url,
    }

    return render(
        request,
        "surveys/survey_qr_print.html",
        context,
    )

@login_required
def survey_results(request, survey_id):
    """
    Сводные результаты формы.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    results = get_survey_results(survey)

    submissions = (
        survey.submissions
        .order_by(
            "-submitted_at",
            "-id",
        )
    )

    context = {
        "survey": survey,
        "results": results,
        "submissions": submissions,
    }

    return render(
        request,
        "surveys/survey_results.html",
        context,
    )

@login_required
def submission_detail(
    request,
    survey_id,
    submission_id,
):
    """
    Показывает индивидуальный ответ участника.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    submission = get_object_or_404(
        survey.submissions.prefetch_related(
            "answers",
            "answers__sample",
            "answers__question",
        ),
        pk=submission_id,
    )

    samples = list(
        survey.samples.order_by(
            "order",
            "id",
        )
    )

    questions = list(
        survey.questions.order_by(
            "order",
            "id",
        )
    )

    answer_map = {
        (
            answer.sample_id,
            answer.question_id,
        ): answer
        for answer in submission.answers.all()
    }

    sample_blocks = []

    for sample in samples:
        answer_rows = []

        for question in questions:
            answer_rows.append(
                {
                    "question": question,
                    "answer": answer_map.get(
                        (
                            sample.pk,
                            question.pk,
                        )
                    ),
                }
            )

        sample_blocks.append(
            {
                "sample": sample,
                "answers": answer_rows,
            }
        )

    context = {
        "survey": survey,
        "submission": submission,
        "sample_blocks": sample_blocks,
    }

    return render(
        request,
        "surveys/submission_detail.html",
        context,
    )

@login_required
@require_POST
def submission_exclude(
    request,
    survey_id,
    submission_id,
):
    """
    Исключает ответ участника из средних расчётов.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    submission = get_object_or_404(
        survey.submissions,
        pk=submission_id,
    )

    reason = request.POST.get(
        "exclusion_reason",
        "",
    ).strip()

    submission.is_excluded = True
    submission.exclusion_reason = reason

    submission.save(
        update_fields=[
            "is_excluded",
            "exclusion_reason",
        ]
    )

    messages.warning(
        request,
        (
            f'Ответ участника «{submission.full_name}» '
            f"исключён из расчётов."
        ),
    )

    return redirect(
        "surveys:submission_detail",
        survey_id=survey.pk,
        submission_id=submission.pk,
    )

@login_required
@require_POST
def submission_include(
    request,
    survey_id,
    submission_id,
):
    """
    Возвращает ранее исключённый ответ в расчёты.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    submission = get_object_or_404(
        survey.submissions,
        pk=submission_id,
    )

    submission.is_excluded = False
    submission.exclusion_reason = ""

    submission.save(
        update_fields=[
            "is_excluded",
            "exclusion_reason",
        ]
    )

    messages.success(
        request,
        (
            f'Ответ участника «{submission.full_name}» '
            f"возвращён в расчёты."
        ),
    )

    return redirect(
        "surveys:submission_detail",
        survey_id=survey.pk,
        submission_id=submission.pk,
    )

@login_required
def survey_excel_export(request, survey_id):
    """
    Формирует полный Excel-отчёт.
    """

    survey = get_survey_available_to_user(
        request.user,
        survey_id,
    )

    report_data = build_survey_excel_report(
        survey,
    )

    filename = (
        f"survey-{survey.pk}-results.xlsx"
    )

    response = HttpResponse(
        report_data,
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    return response
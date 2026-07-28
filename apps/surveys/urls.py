from django.urls import path

from . import views


app_name = "surveys"


urlpatterns = [
    path(
        "",
        views.survey_list,
        name="survey_list",
    ),
    path(
        "create/",
        views.survey_create,
        name="survey_create",
    ),
    path(
        "<int:survey_id>/edit/",
        views.survey_edit,
        name="survey_edit",
    ),
    path(
        "<int:survey_id>/publish/",
        views.survey_publish,
        name="survey_publish",
    ),
    path(
        "<int:survey_id>/close/",
        views.survey_close,
        name="survey_close",
    ),
    path(
        "<int:survey_id>/archive/",
        views.survey_archive,
        name="survey_archive",
    ),
    path(
        "<int:survey_id>/samples/create/",
        views.sample_create,
        name="sample_create",
    ),
    path(
        (
            "<int:survey_id>/samples/"
            "<int:sample_id>/edit/"
        ),
        views.sample_edit,
        name="sample_edit",
    ),
    path(
        (
            "<int:survey_id>/samples/"
            "<int:sample_id>/delete/"
        ),
        views.sample_delete,
        name="sample_delete",
    ),
    path(
        (
            "<int:survey_id>/samples/"
            "<int:sample_id>/move-up/"
        ),
        views.sample_move_up,
        name="sample_move_up",
    ),
    path(
        (
            "<int:survey_id>/samples/"
            "<int:sample_id>/move-down/"
        ),
        views.sample_move_down,
        name="sample_move_down",
    ),
]
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.surveys import views as survey_views


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "f/<uuid:public_id>/",
        survey_views.public_survey,
        name="public_survey",
    ),
    path(
        (
            "f/<uuid:public_id>/"
            "success/<uuid:submission_id>/"
        ),
        survey_views.public_survey_success,
        name="public_survey_success",
    ),
    path(
        "forms/",
        include("apps.surveys.urls"),
    ),
    path(
        "",
        include("apps.accounts.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )


admin.site.site_header = "Леовит формы"
admin.site.site_title = "Леовит формы"
admin.site.index_title = "Администрирование"
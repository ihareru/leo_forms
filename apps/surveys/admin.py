from django.contrib import admin

from .models import Survey
from .models import SurveyQuestion
from .models import SurveySample


class SurveySampleInline(admin.TabularInline):
    model = SurveySample
    extra = 0

    fields = (
        "name",
        "description",
        "order",
        "is_active",
    )

    ordering = (
        "order",
        "id",
    )


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 0

    fields = (
        "title",
        "code",
        "question_type",
        "is_required",
        "order",
        "is_active",
    )

    readonly_fields = (
        "code",
    )

    ordering = (
        "order",
        "id",
    )


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "status",
        "sample_count",
        "question_count",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "allow_multiple_submissions",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
    )

    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
        "published_at",
        "closed_at",
    )

    autocomplete_fields = (
        "owner",
    )

    ordering = (
        "-created_at",
    )

    inlines = (
        SurveySampleInline,
        SurveyQuestionInline,
    )

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "owner",
                    "title",
                    "description",
                    "status",
                )
            },
        ),
        (
            "Параметры заполнения",
            {
                "fields": (
                    "allow_multiple_submissions",
                    "public_id",
                )
            },
        ),
        (
            "Служебная информация",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "created_at",
                    "updated_at",
                    "published_at",
                    "closed_at",
                ),
            },
        ),
    )

    @admin.display(
        description="Образцов",
    )
    def sample_count(self, obj):
        return obj.samples.count()

    @admin.display(
        description="Вопросов",
    )
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(SurveySample)
class SurveySampleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "survey",
        "order",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "survey__title",
    )

    autocomplete_fields = (
        "survey",
    )

    ordering = (
        "survey",
        "order",
        "id",
    )


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "survey",
        "question_type",
        "is_required",
        "order",
        "is_active",
    )

    list_filter = (
        "question_type",
        "is_required",
        "is_active",
    )

    search_fields = (
        "title",
        "survey__title",
    )

    autocomplete_fields = (
        "survey",
    )

    ordering = (
        "survey",
        "order",
        "id",
    )
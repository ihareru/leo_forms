from django.contrib import admin
from .models import (
    Answer,
    Submission,
    Survey,
    SurveyQuestion,
    SurveySample
)



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

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    can_delete = False

    fields = (
        "sample",
        "question",
        "numeric_value",
        "text_value",
    )

    readonly_fields = fields

    ordering = (
        "sample__order",
        "question__order",
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "position",
        "survey",
        "submitted_at",
        "is_excluded",
    )

    list_filter = (
        "survey",
        "is_excluded",
        "submitted_at",
    )

    search_fields = (
        "full_name",
        "position",
        "survey__title",
    )

    readonly_fields = (
        "public_id",
        "survey",
        "full_name",
        "position",
        "submitted_at",
        "ip_address",
        "user_agent",
    )

    ordering = (
        "-submitted_at",
    )

    inlines = (
        AnswerInline,
    )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "sample",
        "question",
        "numeric_value",
        "short_text_value",
    )

    list_filter = (
        "question",
        "sample__survey",
    )

    search_fields = (
        "submission__full_name",
        "sample__name",
        "question__title",
        "text_value",
    )

    readonly_fields = (
        "submission",
        "sample",
        "question",
        "numeric_value",
        "text_value",
        "created_at",
    )

    @admin.display(
        description="Текстовый ответ",
    )
    def short_text_value(self, obj):
        if not obj.text_value:
            return "—"

        if len(obj.text_value) <= 80:
            return obj.text_value

        return f"{obj.text_value[:80]}…"
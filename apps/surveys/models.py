import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Survey(models.Model):
    """
    Форма или опрос, созданный пользователем портала.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        PUBLISHED = "PUBLISHED", "Опубликована"
        CLOSED = "CLOSED", "Сбор ответов закрыт"
        ARCHIVED = "ARCHIVED", "Архивная"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Создатель",
        related_name="surveys",
        on_delete=models.PROTECT,
    )

    title = models.CharField(
        verbose_name="Название формы",
        max_length=255,
    )

    description = models.TextField(
        verbose_name="Описание",
        blank=True,
    )

    status = models.CharField(
        verbose_name="Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    public_id = models.UUIDField(
        verbose_name="Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    allow_multiple_submissions = models.BooleanField(
        verbose_name="Разрешать повторное заполнение",
        default=False,
    )

    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Дата изменения",
        auto_now=True,
    )

    published_at = models.DateTimeField(
        verbose_name="Дата публикации",
        null=True,
        blank=True,
    )

    closed_at = models.DateTimeField(
        verbose_name="Дата закрытия",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Форма"
        verbose_name_plural = "Формы"
        ordering = [
            "-created_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "owner",
                    "status",
                ],
                name="survey_owner_status_idx",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def is_draft(self) -> bool:
        return self.status == self.Status.DRAFT

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    @property
    def is_closed(self) -> bool:
        return self.status == self.Status.CLOSED

    @property
    def accepts_responses(self) -> bool:
        return self.status == self.Status.PUBLISHED

    def publish(self):
        """
        Публикует форму.

        Пока форма не содержит образцов, публикация запрещена.
        """

        if not self.samples.filter(is_active=True).exists():
            raise ValidationError(
                "Нельзя опубликовать форму без образцов."
            )

        self.status = self.Status.PUBLISHED

        if self.published_at is None:
            self.published_at = timezone.now()

        self.closed_at = None

        self.save(
            update_fields=[
                "status",
                "published_at",
                "closed_at",
                "updated_at",
            ]
        )

    def close(self):
        """
        Закрывает форму для новых ответов.
        """

        if self.status != self.Status.PUBLISHED:
            raise ValidationError(
                "Закрыть можно только опубликованную форму."
            )

        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "closed_at",
                "updated_at",
            ]
        )

    def archive(self):
        """
        Переводит форму в архив.
        """

        self.status = self.Status.ARCHIVED

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


class SurveySample(models.Model):
    """
    Образец продукции внутри формы.
    """

    survey = models.ForeignKey(
        Survey,
        verbose_name="Форма",
        related_name="samples",
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        verbose_name="Название образца",
        max_length=255,
    )

    description = models.TextField(
        verbose_name="Характеристика образца",
        blank=True,
    )

    order = models.PositiveIntegerField(
        verbose_name="Порядок",
        default=0,
    )

    is_active = models.BooleanField(
        verbose_name="Активный",
        default=True,
    )

    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Дата изменения",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Образец"
        verbose_name_plural = "Образцы"
        ordering = [
            "order",
            "id",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "survey",
                    "order",
                ],
                name="unique_sample_order_per_survey",
            ),
        ]

    def __str__(self):
        return f"{self.survey.title}: {self.name}"


class SurveyQuestion(models.Model):
    """
    Вопрос или критерий оценки.

    Вопрос относится ко всей форме и показывается для каждого
    активного образца этой формы.
    """

    class QuestionType(models.TextChoices):
        RATING = "RATING", "Балловая оценка"
        TEXT = "TEXT", "Текстовый комментарий"

    class StandardCode(models.TextChoices):
        APPEARANCE = "APPEARANCE", "Внешний вид"
        COLOR = "COLOR", "Цвет"
        CONSISTENCY = "CONSISTENCY", "Консистенция"
        SMELL = "SMELL", "Запах"
        TASTE = "TASTE", "Вкус"
        COMMENT = "COMMENT", "Комментарии к балловым оценкам"

    survey = models.ForeignKey(
        Survey,
        verbose_name="Форма",
        related_name="questions",
        on_delete=models.CASCADE,
    )

    title = models.CharField(
        verbose_name="Название вопроса",
        max_length=255,
    )

    code = models.CharField(
        verbose_name="Системный код",
        max_length=30,
        choices=StandardCode.choices,
        blank=True,
    )

    question_type = models.CharField(
        verbose_name="Тип вопроса",
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.RATING,
    )

    is_required = models.BooleanField(
        verbose_name="Обязательный",
        default=True,
    )

    order = models.PositiveIntegerField(
        verbose_name="Порядок",
        default=0,
    )

    minimum_value = models.DecimalField(
        verbose_name="Минимальная оценка",
        max_digits=2,
        decimal_places=1,
        default="1.0",
        null=True,
        blank=True,
    )

    maximum_value = models.DecimalField(
        verbose_name="Максимальная оценка",
        max_digits=2,
        decimal_places=1,
        default="5.0",
        null=True,
        blank=True,
    )

    decimal_places = models.PositiveSmallIntegerField(
        verbose_name="Количество знаков после запятой",
        default=1,
    )

    is_active = models.BooleanField(
        verbose_name="Активный",
        default=True,
    )

    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Дата изменения",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = [
            "order",
            "id",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "survey",
                    "order",
                ],
                name="unique_question_order_per_survey",
            ),
            models.UniqueConstraint(
                fields=[
                    "survey",
                    "code",
                ],
                condition=~models.Q(code=""),
                name="unique_question_code_per_survey",
            ),
        ]

    def __str__(self):
        return f"{self.survey.title}: {self.title}"

    def clean(self):
        super().clean()

        if self.question_type == self.QuestionType.RATING:
            if self.minimum_value is None:
                raise ValidationError(
                    {
                        "minimum_value": (
                            "Для баллового вопроса необходимо "
                            "указать минимальную оценку."
                        )
                    }
                )

            if self.maximum_value is None:
                raise ValidationError(
                    {
                        "maximum_value": (
                            "Для баллового вопроса необходимо "
                            "указать максимальную оценку."
                        )
                    }
                )

            if self.minimum_value >= self.maximum_value:
                raise ValidationError(
                    {
                        "maximum_value": (
                            "Максимальная оценка должна быть "
                            "больше минимальной."
                        )
                    }
                )

        if self.question_type == self.QuestionType.TEXT:
            self.minimum_value = None
            self.maximum_value = None
            self.decimal_places = 0
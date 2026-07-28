import uuid
from pathlib import Path
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

        Если форма была опубликована, дата завершения сбора
        фиксируется автоматически.
        """

        self.status = self.Status.ARCHIVED

        if self.closed_at is None:
            self.closed_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "closed_at",
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


class Submission(models.Model):
    """
    Заполненная участником форма.

    Участник может быть неавторизованным, поэтому его ФИО
    и должность сохраняются непосредственно в отправке.
    """

    survey = models.ForeignKey(
        Survey,
        verbose_name="Форма",
        related_name="submissions",
        on_delete=models.PROTECT,
    )

    public_id = models.UUIDField(
        verbose_name="Идентификатор ответа",
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    full_name = models.CharField(
        verbose_name="ФИО",
        max_length=255,
    )

    position = models.CharField(
        verbose_name="Должность",
        max_length=255,
    )

    submitted_at = models.DateTimeField(
        verbose_name="Дата заполнения",
        auto_now_add=True,
        db_index=True,
    )

    is_excluded = models.BooleanField(
        verbose_name="Исключён из расчётов",
        default=False,
        db_index=True,
    )

    exclusion_reason = models.CharField(
        verbose_name="Причина исключения",
        max_length=500,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        verbose_name="IP-адрес",
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        verbose_name="Браузер",
        blank=True,
    )

    class Meta:
        verbose_name = "Ответ участника"
        verbose_name_plural = "Ответы участников"
        ordering = [
            "-submitted_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "survey",
                    "is_excluded",
                ],
                name="submission_survey_excl_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.full_name}: "
            f"{self.survey.title} "
            f"({self.submitted_at:%d.%m.%Y %H:%M})"
        )


class Answer(models.Model):
    """
    Отдельный ответ на вопрос по конкретному образцу.
    """

    submission = models.ForeignKey(
        Submission,
        verbose_name="Заполнение",
        related_name="answers",
        on_delete=models.CASCADE,
    )

    sample = models.ForeignKey(
        SurveySample,
        verbose_name="Образец",
        related_name="answers",
        on_delete=models.PROTECT,
    )

    question = models.ForeignKey(
        SurveyQuestion,
        verbose_name="Вопрос",
        related_name="answers",
        on_delete=models.PROTECT,
    )

    numeric_value = models.DecimalField(
        verbose_name="Числовая оценка",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )

    text_value = models.TextField(
        verbose_name="Текстовый ответ",
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        ordering = [
            "sample__order",
            "question__order",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "submission",
                    "sample",
                    "question",
                ],
                name="unique_answer_per_sample_question",
            ),
        ]
        indexes = [
            models.Index(
                fields=[
                    "sample",
                    "question",
                ],
                name="answer_sample_question_idx",
            ),
        ]

    def __str__(self):
        value = (
            self.numeric_value
            if self.numeric_value is not None
            else self.text_value
        )

        return (
            f"{self.submission.full_name}: "
            f"{self.sample.name} — "
            f"{self.question.title}: {value}"
        )

    def clean(self):
        super().clean()

        if self.sample.survey_id != self.submission.survey_id:
            raise ValidationError(
                "Образец относится к другой форме."
            )

        if self.question.survey_id != self.submission.survey_id:
            raise ValidationError(
                "Вопрос относится к другой форме."
            )

        if (
            self.question.question_type
            == SurveyQuestion.QuestionType.RATING
        ):
            if self.numeric_value is None:
                raise ValidationError(
                    {
                        "numeric_value": (
                            "Для баллового вопроса "
                            "необходимо указать оценку."
                        )
                    }
                )

            if (
                self.question.minimum_value is not None
                and self.numeric_value
                < self.question.minimum_value
            ):
                raise ValidationError(
                    {
                        "numeric_value": (
                            "Оценка меньше допустимого значения."
                        )
                    }
                )

            if (
                self.question.maximum_value is not None
                and self.numeric_value
                > self.question.maximum_value
            ):
                raise ValidationError(
                    {
                        "numeric_value": (
                            "Оценка больше допустимого значения."
                        )
                    }
                )

            self.text_value = ""

        if (
            self.question.question_type
            == SurveyQuestion.QuestionType.TEXT
        ):
            self.numeric_value = None

            
def protocol_upload_to(instance, filename):
    """
    Путь хранения сформированного протокола.

    Пример:
    protocols/survey_15/protocol_304_v1.docx
    """

    extension = Path(filename).suffix or ".docx"

    return (
        f"protocols/survey_{instance.survey_id}/"
        f"protocol_{instance.protocol_number}_"
        f"v{instance.version}{extension}"
    )


class SurveyProtocol(models.Model):
    """
    Реквизиты протокола конкретной формы.

    Заполняются после завершения сбора ответов.
    """

    survey = models.OneToOneField(
        Survey,
        verbose_name="Форма",
        related_name="protocol",
        on_delete=models.CASCADE,
    )

    document_code = models.CharField(
        verbose_name="Код документа",
        max_length=100,
        default="КК-Ф-020",
        blank=True,
    )

    protocol_number = models.CharField(
        verbose_name="Номер протокола",
        max_length=50,
        blank=True,
    )

    protocol_date = models.DateField(
        verbose_name="Дата протокола",
        null=True,
        blank=True,
    )

    responsible_employee = models.CharField(
        verbose_name=(
            "Сотрудник отдела разработки продуктов"
        ),
        max_length=255,
        blank=True,
    )

    tasting_goal = models.TextField(
        verbose_name="Цель дегустации",
        blank=True,
    )

    room_conditions = models.TextField(
        verbose_name="Условия в помещении",
        blank=True,
        default=(
            "Температура воздуха в помещении: "
            "+18 – +25 °С, относительная влажность "
            "воздуха – менее 75%."
        ),
    )

    product_conditions = models.TextField(
        verbose_name="Температура и условия продуктов",
        blank=True,
    )

    conclusion = models.TextField(
        verbose_name="Заключение",
        blank=True,
    )

    signer_position = models.CharField(
        verbose_name="Должность подписанта",
        max_length=255,
        blank=True,
        default="Нач. ОРП",
    )

    signer_name = models.CharField(
        verbose_name="ФИО подписанта",
        max_length=255,
        blank=True,
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
        verbose_name = "Реквизиты протокола"
        verbose_name_plural = "Реквизиты протоколов"

    def __str__(self):
        number = self.protocol_number or "без номера"

        return (
            f"Протокол {number}: "
            f"{self.survey.title}"
        )

    @property
    def is_complete(self) -> bool:
        """
        Проверка обязательных данных перед формированием DOCX.
        """

        return all(
            [
                self.protocol_number,
                self.protocol_date,
                self.responsible_employee,
                self.tasting_goal,
                self.conclusion,
                self.signer_position,
                self.signer_name,
            ]
        )


class GeneratedProtocol(models.Model):
    """
    Сформированная версия протокола DOCX.

    Каждое повторное формирование создаёт новую версию.
    """

    survey = models.ForeignKey(
        Survey,
        verbose_name="Форма",
        related_name="generated_protocols",
        on_delete=models.CASCADE,
    )

    protocol_number = models.CharField(
        verbose_name="Номер протокола",
        max_length=50,
    )

    version = models.PositiveIntegerField(
        verbose_name="Версия",
    )

    file = models.FileField(
        verbose_name="Файл DOCX",
        upload_to=protocol_upload_to,
    )

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Сформировал",
        related_name="generated_protocols",
        on_delete=models.PROTECT,
    )

    generated_at = models.DateTimeField(
        verbose_name="Дата формирования",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Сформированный протокол"
        verbose_name_plural = "Сформированные протоколы"
        ordering = [
            "-version",
            "-generated_at",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "survey",
                    "version",
                ],
                name="unique_protocol_version_per_survey",
            ),
        ]

    def __str__(self):
        return (
            f"Протокол №{self.protocol_number}, "
            f"версия {self.version}"
        )
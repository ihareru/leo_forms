from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Survey
from .services.questions import create_default_questions


@receiver(post_save, sender=Survey)
def create_survey_default_questions(
    sender,
    instance,
    created,
    **kwargs,
):
    """
    После создания формы добавляет стандартные вопросы.
    """

    if created:
        create_default_questions(instance)
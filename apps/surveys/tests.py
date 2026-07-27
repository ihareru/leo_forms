from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .forms import RatingDecimalField
from .models import Survey
from .models import SurveyQuestion
from .models import SurveySample


User = get_user_model()


class SurveyModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator",
            password="StrongPassword123!",
        )

    def test_new_survey_is_draft(self):
        survey = Survey.objects.create(
            owner=self.user,
            title="Тестовая форма",
        )

        self.assertEqual(
            survey.status,
            Survey.Status.DRAFT,
        )

        self.assertFalse(
            survey.accepts_responses,
        )

    def test_default_questions_created(self):
        survey = Survey.objects.create(
            owner=self.user,
            title="Тестовая форма",
        )

        self.assertEqual(
            survey.questions.count(),
            6,
        )

        question_codes = set(
            survey.questions.values_list(
                "code",
                flat=True,
            )
        )

        expected_codes = {
            SurveyQuestion.StandardCode.APPEARANCE,
            SurveyQuestion.StandardCode.COLOR,
            SurveyQuestion.StandardCode.CONSISTENCY,
            SurveyQuestion.StandardCode.SMELL,
            SurveyQuestion.StandardCode.TASTE,
            SurveyQuestion.StandardCode.COMMENT,
        }

        self.assertEqual(
            question_codes,
            expected_codes,
        )

    def test_public_id_is_unique(self):
        survey_1 = Survey.objects.create(
            owner=self.user,
            title="Форма №1",
        )

        survey_2 = Survey.objects.create(
            owner=self.user,
            title="Форма №2",
        )

        self.assertNotEqual(
            survey_1.public_id,
            survey_2.public_id,
        )

    def test_cannot_publish_survey_without_samples(self):
        survey = Survey.objects.create(
            owner=self.user,
            title="Форма без образцов",
        )

        with self.assertRaises(ValidationError):
            survey.publish()

    def test_survey_can_be_published_with_sample(self):
        survey = Survey.objects.create(
            owner=self.user,
            title="Форма с образцом",
        )

        SurveySample.objects.create(
            survey=survey,
            name="Образец №1",
            order=10,
        )

        survey.publish()
        survey.refresh_from_db()

        self.assertEqual(
            survey.status,
            Survey.Status.PUBLISHED,
        )

        self.assertTrue(
            survey.accepts_responses,
        )

        self.assertIsNotNone(
            survey.published_at,
        )

    def test_published_survey_can_be_closed(self):
        survey = Survey.objects.create(
            owner=self.user,
            title="Форма с образцом",
        )

        SurveySample.objects.create(
            survey=survey,
            name="Образец №1",
            order=10,
        )

        survey.publish()
        survey.close()
        survey.refresh_from_db()

        self.assertEqual(
            survey.status,
            Survey.Status.CLOSED,
        )

        self.assertFalse(
            survey.accepts_responses,
        )

        self.assertIsNotNone(
            survey.closed_at,
        )

    def test_draft_survey_cannot_be_closed(self):
        survey = Survey.objects.create(
            owner=self.user,
            title="Черновик",
        )

        with self.assertRaises(ValidationError):
            survey.close()


class RatingDecimalFieldTests(TestCase):
    def setUp(self):
        self.field = RatingDecimalField()

    def test_accepts_decimal_with_dot(self):
        value = self.field.clean("3.5")

        self.assertEqual(
            value,
            Decimal("3.5"),
        )

    def test_accepts_decimal_with_comma(self):
        value = self.field.clean("3,5")

        self.assertEqual(
            value,
            Decimal("3.5"),
        )

    def test_accepts_integer(self):
        value = self.field.clean("5")

        self.assertEqual(
            value,
            Decimal("5"),
        )

    def test_rejects_value_below_minimum(self):
        with self.assertRaises(ValidationError):
            self.field.clean("0,9")

    def test_rejects_value_above_maximum(self):
        with self.assertRaises(ValidationError):
            self.field.clean("5,1")

    def test_rejects_non_numeric_value(self):
        with self.assertRaises(ValidationError):
            self.field.clean("пять")
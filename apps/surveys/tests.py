from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .forms import RatingDecimalField, PublicSurveyForm
from .models import (
    Survey,
    SurveyQuestion,
    SurveySample,
    Answer,
    Submission,
)
from .services.results import get_survey_results


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


class PublicSurveyFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator_public",
            password="StrongPassword123!",
        )

        self.survey = Survey.objects.create(
            owner=self.user,
            title="Публичная форма",
        )

        self.sample = SurveySample.objects.create(
            survey=self.survey,
            name="Образец №1",
            order=10,
        )

    def get_valid_form_data(self):
        data = {
            "full_name": "Иванов Иван Иванович",
            "position": "Инженер-технолог",
        }

        for question in self.survey.questions.all():
            field_name = (
                PublicSurveyForm.get_answer_field_name(
                    sample_id=self.sample.pk,
                    question_id=question.pk,
                )
            )

            if (
                question.question_type
                == SurveyQuestion.QuestionType.RATING
            ):
                data[field_name] = "4,5"
            else:
                data[field_name] = "Хороший образец"

        return data

    def test_public_form_accepts_comma_scores(self):
        form = PublicSurveyForm(
            data=self.get_valid_form_data(),
            survey=self.survey,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        rating_question = self.survey.questions.filter(
            question_type=(
                SurveyQuestion.QuestionType.RATING
            ),
        ).first()

        field_name = form.get_answer_field_name(
            sample_id=self.sample.pk,
            question_id=rating_question.pk,
        )

        self.assertEqual(
            form.cleaned_data[field_name],
            Decimal("4.5"),
        )

    def test_public_form_rejects_score_above_five(self):
        data = self.get_valid_form_data()

        rating_question = self.survey.questions.filter(
            question_type=(
                SurveyQuestion.QuestionType.RATING
            ),
        ).first()

        field_name = (
            PublicSurveyForm.get_answer_field_name(
                sample_id=self.sample.pk,
                question_id=rating_question.pk,
            )
        )

        data[field_name] = "5,1"

        form = PublicSurveyForm(
            data=data,
            survey=self.survey,
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            field_name,
            form.errors,
        )


class PublicSurveyViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="public_owner",
            password="StrongPassword123!",
        )

        self.survey = Survey.objects.create(
            owner=self.user,
            title="Дегустация",
        )

        self.sample = SurveySample.objects.create(
            survey=self.survey,
            name="Образец №1",
            order=10,
        )

    def get_public_url(self):
        return reverse(
            "public_survey",
            args=[
                self.survey.public_id,
            ],
        )

    def get_valid_submission_data(self):
        data = {
            "full_name": "Петров Пётр Петрович",
            "position": "Технолог",
        }

        for question in self.survey.questions.all():
            field_name = (
                PublicSurveyForm.get_answer_field_name(
                    sample_id=self.sample.pk,
                    question_id=question.pk,
                )
            )

            if (
                question.question_type
                == SurveyQuestion.QuestionType.RATING
            ):
                data[field_name] = "3,5"
            else:
                data[field_name] = (
                    "Комментарий участника"
                )

        return data

    def test_draft_survey_is_not_public(self):
        response = self.client.get(
            self.get_public_url(),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_published_survey_is_public(self):
        self.survey.publish()

        response = self.client.get(
            self.get_public_url(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            self.survey.title,
        )

        self.assertContains(
            response,
            self.sample.name,
        )

    def test_closed_survey_does_not_accept_answers(self):
        self.survey.publish()
        self.survey.close()

        response = self.client.get(
            self.get_public_url(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Сбор ответов завершён",
        )

    def test_submission_is_saved(self):
        self.survey.publish()

        response = self.client.post(
            self.get_public_url(),
            self.get_valid_submission_data(),
        )

        self.assertEqual(
            Submission.objects.count(),
            1,
        )

        submission = Submission.objects.get()

        self.assertEqual(
            submission.full_name,
            "Петров Пётр Петрович",
        )

        self.assertEqual(
            submission.position,
            "Технолог",
        )

        expected_answer_count = (
            self.survey.questions.count()
            * self.survey.samples.filter(
                is_active=True,
            ).count()
        )

        self.assertEqual(
            submission.answers.count(),
            expected_answer_count,
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_comma_score_saved_as_decimal(self):
        self.survey.publish()

        self.client.post(
            self.get_public_url(),
            self.get_valid_submission_data(),
        )

        answer = Answer.objects.filter(
            question__question_type=(
                SurveyQuestion.QuestionType.RATING
            ),
        ).first()

        self.assertEqual(
            answer.numeric_value,
            Decimal("3.5"),
        )

    def test_comment_is_linked_to_participant(self):
        self.survey.publish()

        self.client.post(
            self.get_public_url(),
            self.get_valid_submission_data(),
        )

        comment_answer = Answer.objects.get(
            question__question_type=(
                SurveyQuestion.QuestionType.TEXT
            ),
        )

        self.assertEqual(
            comment_answer.text_value,
            "Комментарий участника",
        )

        self.assertEqual(
            comment_answer.submission.full_name,
            "Петров Пётр Петрович",
        )

    def test_second_submission_blocked_in_same_session(self):
        self.survey.publish()

        data = self.get_valid_submission_data()

        self.client.post(
            self.get_public_url(),
            data,
        )

        response = self.client.post(
            self.get_public_url(),
            data,
        )

        self.assertEqual(
            Submission.objects.count(),
            1,
        )

        self.assertContains(
            response,
            "Ответ уже отправлен",
        )

    def test_multiple_submissions_can_be_allowed(self):
        self.survey.allow_multiple_submissions = True
        self.survey.save(
            update_fields=[
                "allow_multiple_submissions",
                "updated_at",
            ]
        )

        self.survey.publish()

        data = self.get_valid_submission_data()

        self.client.post(
            self.get_public_url(),
            data,
        )

        self.client.post(
            self.get_public_url(),
            data,
        )

        self.assertEqual(
            Submission.objects.count(),
            2,
        )

    def test_inactive_sample_is_not_shown(self):
        self.sample.is_active = False
        self.sample.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        active_sample = SurveySample.objects.create(
            survey=self.survey,
            name="Активный образец",
            order=20,
        )

        self.survey.publish()

        response = self.client.get(
            self.get_public_url(),
        )

        self.assertNotContains(
            response,
            self.sample.name,
        )

        self.assertContains(
            response,
            active_sample.name,
        )


class SurveyResultsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="results_owner",
            password="StrongPassword123!",
        )

        self.survey = Survey.objects.create(
            owner=self.user,
            title="Результаты дегустации",
        )

        self.sample = SurveySample.objects.create(
            survey=self.survey,
            name="Образец №1",
            order=10,
        )

        self.rating_question = (
            self.survey.questions.filter(
                question_type=(
                    SurveyQuestion.QuestionType.RATING
                ),
            )
            .order_by(
                "order",
            )
            .first()
        )

        self.comment_question = (
            self.survey.questions.filter(
                question_type=(
                    SurveyQuestion.QuestionType.TEXT
                ),
            )
            .first()
        )

    def create_submission(
        self,
        *,
        full_name,
        score,
        comment="",
        is_excluded=False,
    ):
        submission = Submission.objects.create(
            survey=self.survey,
            full_name=full_name,
            position="Технолог",
            is_excluded=is_excluded,
        )

        Answer.objects.create(
            submission=submission,
            sample=self.sample,
            question=self.rating_question,
            numeric_value=score,
        )

        Answer.objects.create(
            submission=submission,
            sample=self.sample,
            question=self.comment_question,
            text_value=comment,
        )

        return submission

    def test_average_score_is_calculated(self):
        self.create_submission(
            full_name="Участник №1",
            score=Decimal("4.0"),
        )

        self.create_submission(
            full_name="Участник №2",
            score=Decimal("5.0"),
        )

        results = get_survey_results(
            self.survey,
        )

        rating_score = results["rows"][0]["scores"][0]

        self.assertEqual(
            rating_score["average"],
            Decimal("4.5"),
        )

    def test_excluded_submission_is_not_in_average(self):
        self.create_submission(
            full_name="Участник №1",
            score=Decimal("5.0"),
        )

        self.create_submission(
            full_name="Ошибочный участник",
            score=Decimal("1.0"),
            is_excluded=True,
        )

        results = get_survey_results(
            self.survey,
        )

        rating_score = results["rows"][0]["scores"][0]

        self.assertEqual(
            rating_score["average"],
            Decimal("5.0"),
        )

        self.assertEqual(
            results["submissions_total"],
            2,
        )

        self.assertEqual(
            results["submissions_included"],
            1,
        )

        self.assertEqual(
            results["submissions_excluded"],
            1,
        )

    def test_comments_are_anonymous_in_results(self):
        self.create_submission(
            full_name="Иванов Иван Иванович",
            score=Decimal("4.0"),
            comment="Недостаточно выраженный вкус",
        )

        results = get_survey_results(
            self.survey,
        )

        comments = results["rows"][0]["comments"]

        self.assertEqual(
            comments,
            [
                "Недостаточно выраженный вкус",
            ],
        )

        self.assertNotIn(
            "Иванов Иван Иванович",
            comments,
        )

class SurveyReportViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="report_owner",
            password="StrongPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="report_other",
            password="StrongPassword123!",
        )

        self.survey = Survey.objects.create(
            owner=self.user,
            title="Форма для отчётов",
        )

        self.sample = SurveySample.objects.create(
            survey=self.survey,
            name="Образец №1",
            order=10,
        )

    def test_owner_can_open_results(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "surveys:survey_results",
                args=[
                    self.survey.pk,
                ],
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Результаты",
        )

    def test_other_user_cannot_open_results(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "surveys:survey_results",
                args=[
                    self.survey.pk,
                ],
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_qr_code_is_png(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "surveys:survey_qr_code",
                args=[
                    self.survey.pk,
                ],
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "image/png",
        )

        self.assertTrue(
            response.content.startswith(
                b"\x89PNG",
            )
        )

    def test_excel_export_returns_xlsx(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "surveys:survey_excel_export",
                args=[
                    self.survey.pk,
                ],
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        self.assertTrue(
            response.content.startswith(
                b"PK",
            )
        )

class SubmissionManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="submission_owner",
            password="StrongPassword123!",
        )

        self.survey = Survey.objects.create(
            owner=self.user,
            title="Управление ответами",
        )

        self.submission = Submission.objects.create(
            survey=self.survey,
            full_name="Участник",
            position="Технолог",
        )

    def test_submission_can_be_excluded(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "surveys:submission_exclude",
                args=[
                    self.survey.pk,
                    self.submission.pk,
                ],
            ),
            {
                "exclusion_reason": (
                    "Ответ отправлен ошибочно"
                ),
            },
        )

        self.submission.refresh_from_db()

        self.assertTrue(
            self.submission.is_excluded,
        )

        self.assertEqual(
            self.submission.exclusion_reason,
            "Ответ отправлен ошибочно",
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_submission_can_be_returned_to_results(self):
        self.submission.is_excluded = True
        self.submission.exclusion_reason = "Ошибка"
        self.submission.save()

        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "surveys:submission_include",
                args=[
                    self.survey.pk,
                    self.submission.pk,
                ],
            ),
        )

        self.submission.refresh_from_db()

        self.assertFalse(
            self.submission.is_excluded,
        )

        self.assertEqual(
            self.submission.exclusion_reason,
            "",
        )


from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from apps.surveys.models import Survey, SurveySample


User = get_user_model()


class UserModelTests(TestCase):
    def test_default_role_is_user(self):
        user = User.objects.create_user(
            username="creator",
            password="StrongPassword123!",
        )

        self.assertEqual(
            user.role,
            User.Role.USER,
        )

    def test_superuser_role_is_admin(self):
        user = User.objects.create_superuser(
            username="admin",
            password="StrongPassword123!",
        )

        self.assertEqual(
            user.role,
            User.Role.ADMIN,
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_full_name_falls_back_to_username(self):
        user = User.objects.create_user(
            username="creator",
            password="StrongPassword123!",
        )

        self.assertEqual(
            user.get_full_name(),
            "creator",
        )


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator",
            password="StrongPassword123!",
        )

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(
            reverse("accounts:dashboard"),
        )

        expected_url = (
            reverse("accounts:login")
            + "?next="
            + reverse("accounts:dashboard")
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_user_can_login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "creator",
                "password": "StrongPassword123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:dashboard"),
        )

    def test_dashboard_available_after_login(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:dashboard"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Личный кабинет",
        )

class SurveyViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator",
            password="StrongPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="other",
            password="StrongPassword123!",
        )

        self.admin = User.objects.create_superuser(
            username="admin",
            password="StrongPassword123!",
        )

        self.survey = Survey.objects.create(
            owner=self.user,
            title="Форма пользователя",
        )

        self.other_survey = Survey.objects.create(
            owner=self.other_user,
            title="Чужая форма",
        )

    def test_anonymous_user_cannot_open_survey_list(self):
        response = self.client.get(
            reverse("surveys:survey_list"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_user_sees_only_own_surveys(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("surveys:survey_list"),
        )

        self.assertContains(
            response,
            self.survey.title,
        )

        self.assertNotContains(
            response,
            self.other_survey.title,
        )

    def test_admin_sees_all_surveys(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("surveys:survey_list"),
        )

        self.assertContains(
            response,
            self.survey.title,
        )

        self.assertContains(
            response,
            self.other_survey.title,
        )

    def test_user_cannot_open_other_users_survey(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "surveys:survey_edit",
                args=[
                    self.other_survey.pk,
                ],
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_admin_can_open_other_users_survey(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "surveys:survey_edit",
                args=[
                    self.other_survey.pk,
                ],
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_created_survey_belongs_to_current_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("surveys:survey_create"),
            {
                "title": "Новая форма",
                "description": "Описание",
                "allow_multiple_submissions": False,
            },
        )

        created_survey = Survey.objects.get(
            title="Новая форма",
        )

        self.assertEqual(
            created_survey.owner,
            self.user,
        )

        self.assertRedirects(
            response,
            reverse(
                "surveys:survey_edit",
                args=[
                    created_survey.pk,
                ],
            ),
        )

    def test_user_can_add_sample(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "surveys:sample_create",
                args=[
                    self.survey.pk,
                ],
            ),
            {
                "name": "Образец №1",
                "description": "Описание образца",
                "is_active": True,
            },
        )

        sample = self.survey.samples.get()

        self.assertEqual(
            sample.name,
            "Образец №1",
        )

        self.assertEqual(
            sample.order,
            10,
        )

        self.assertRedirects(
            response,
            reverse(
                "surveys:survey_edit",
                args=[
                    self.survey.pk,
                ],
            ),
        )

    def test_second_sample_gets_next_order(self):
        SurveySample.objects.create(
            survey=self.survey,
            name="Образец №1",
            order=10,
        )

        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "surveys:sample_create",
                args=[
                    self.survey.pk,
                ],
            ),
            {
                "name": "Образец №2",
                "description": "",
                "is_active": True,
            },
        )

        second_sample = self.survey.samples.get(
            name="Образец №2",
        )

        self.assertEqual(
            second_sample.order,
            20,
        )

    def test_user_cannot_add_sample_to_other_users_survey(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "surveys:sample_create",
                args=[
                    self.other_survey.pk,
                ],
            ),
            {
                "name": "Чужой образец",
                "description": "",
                "is_active": True,
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertFalse(
            self.other_survey.samples.filter(
                name="Чужой образец",
            ).exists()
        )

    def test_publish_view_publishes_survey(self):
        SurveySample.objects.create(
            survey=self.survey,
            name="Образец №1",
            order=10,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "surveys:survey_publish",
                args=[
                    self.survey.pk,
                ],
            ),
        )

        self.survey.refresh_from_db()

        self.assertEqual(
            self.survey.status,
            Survey.Status.PUBLISHED,
        )

        self.assertRedirects(
            response,
            reverse(
                "surveys:survey_edit",
                args=[
                    self.survey.pk,
                ],
            ),
        )

    def test_publish_view_rejects_survey_without_samples(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "surveys:survey_publish",
                args=[
                    self.survey.pk,
                ],
            ),
        )

        self.survey.refresh_from_db()

        self.assertEqual(
            self.survey.status,
            Survey.Status.DRAFT,
        )

    def test_close_view_closes_published_survey(self):
        SurveySample.objects.create(
            survey=self.survey,
            name="Образец №1",
            order=10,
        )

        self.survey.publish()

        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "surveys:survey_close",
                args=[
                    self.survey.pk,
                ],
            ),
        )

        self.survey.refresh_from_db()

        self.assertEqual(
            self.survey.status,
            Survey.Status.CLOSED,
        )

    def test_samples_can_be_reordered(self):
        first_sample = SurveySample.objects.create(
            survey=self.survey,
            name="Образец №1",
            order=10,
        )

        second_sample = SurveySample.objects.create(
            survey=self.survey,
            name="Образец №2",
            order=20,
        )

        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "surveys:sample_move_up",
                args=[
                    self.survey.pk,
                    second_sample.pk,
                ],
            ),
        )

        first_sample.refresh_from_db()
        second_sample.refresh_from_db()

        self.assertEqual(
            second_sample.order,
            10,
        )

        self.assertEqual(
            first_sample.order,
            20,
        )
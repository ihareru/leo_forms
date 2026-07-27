from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
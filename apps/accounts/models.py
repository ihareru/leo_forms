from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Администратор"
        USER = "USER", "Пользователь"

    role = models.CharField(
        verbose_name="Роль",
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )

    position = models.CharField(
        verbose_name="Должность",
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
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = [
            "last_name",
            "first_name",
            "username",
        ]

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_staff = True

        super().save(*args, **kwargs)

    @property
    def is_portal_admin(self) -> bool:
        return (
            self.role == self.Role.ADMIN
            or self.is_superuser
        )

    def get_full_name(self):
        full_name = super().get_full_name().strip()

        if full_name:
            return full_name

        return self.username

    def __str__(self):
        return self.get_full_name()
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Содержит данные о пользователях."""

    ROLE_CHOICES = (
        ('User', 'Пользователь'),
        ('Admin', 'Администратор'),
    )

    first_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        verbose_name='Электронная почта',
    )
    role = models.CharField(
        max_length=5,
        choices=ROLE_CHOICES,
        default='User',
        verbose_name='Роль',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return self.role == 'Admin' or self.is_superuser or self.is_staff

    def __str__(self):
        return f'{self.username}'


class Subscription(models.Model):
    """Содержит информацию о подписках на авторов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.author}'

from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_username

USER = 'user'
ADMIN = 'admin'
USER_TYPE = [
    (USER, USER),
    (ADMIN, ADMIN),
]


class User(AbstractUser):
    """ Модель Пользователя. """
    username = models.CharField(
        max_length=150,
        validators=(validate_username,),
        unique=True,
        blank=False,
        null=False
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        null=False,
    )
    first_name = models.CharField(
        'имя',
        max_length=150,
        blank=False,
    )
    last_name = models.CharField(
        'фамилия',
        max_length=150,
        blank=False,
    )

    role = models.CharField(
        'роль',
        max_length=10,
        choices=USER_TYPE,
        default=USER,
        blank=True,
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_user(self):
        return self.role == USER

    @property
    def is_admin(self):
        return self.role == ADMIN

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.username

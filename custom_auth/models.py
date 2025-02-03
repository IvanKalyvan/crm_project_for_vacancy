import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.utils import timezone

from .celery_tasks import send_confirmation_email as send_confirmation_email_celery


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('email_verified', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        user.send_confirmation_email()
        return user


class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    confirmation_token = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reset_password_token = models.CharField(max_length=64, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def send_confirmation_email(self, request):

        if not self.confirmation_token:
            self.confirmation_token = get_random_string(length=64)
            self.save()

        confirmation_link = request.build_absolute_uri(
            reverse('auth:confirm_email', args=[str(self.uid), self.confirmation_token])
        )

        send_confirmation_email_celery([self.email], 'Activate your account', f'Here is the link to activate your account: {confirmation_link}')

    def activate_account(self):

        self.is_active = True
        self.email_verified = True
        self.confirmation_token = None
        self.save(update_fields=['is_active', 'email_verified', 'confirmation_token'])
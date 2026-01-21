import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model according to API Contract 3NF schema.
    Maps to 'users' table in the database.
    """
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        INSTRUCTOR = 'instructor', 'Instructor'
        ADMIN = 'admin', 'Admin'

    # Primary identifier
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        verbose_name='User ID'
    )

    # Authentication fields
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True
    )
    password = models.CharField(
        max_length=255
    )

    # Role and status
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    email_verified = models.BooleanField(
        default=False
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # For Django admin

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(role__in=['student', 'instructor', 'admin']),
                name='valid_user_role'
            ),
        ]

    def __str__(self):
        return self.email

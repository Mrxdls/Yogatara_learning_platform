import uuid
from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """
    User Profile model - stores extended user information (1:1 with User).
    Maps to 'user_profiles' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # Personal information
    full_name = models.CharField(max_length=100, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.CharField(max_length=500, blank=True)
    bio = models.TextField(blank=True)

    # Contact information
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    website = models.CharField(max_length=255, blank=True)

    # Educational background
    education = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.email}"


class UserSettings(models.Model):
    """
    User Settings model - stores user preferences and settings (1:1 with User).
    Maps to 'user_settings' table in the database.
    """
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]

    PROFILE_VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('connections', 'Connections Only'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings'
    )

    # Notification settings
    email_course_updates = models.BooleanField(default=True)
    email_assignments = models.BooleanField(default=True)
    email_announcements = models.BooleanField(default=True)
    email_weekly_digest = models.BooleanField(default=False)
    push_course_updates = models.BooleanField(default=True)
    push_assignments = models.BooleanField(default=True)
    push_announcements = models.BooleanField(default=True)

    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=PROFILE_VISIBILITY_CHOICES,
        default='public'
    )
    show_enrolled_courses = models.BooleanField(default=True)
    show_progress = models.BooleanField(default=True)

    # Preference settings
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light'
    )
    language = models.CharField(max_length=10, default='en')
    autoplay_videos = models.BooleanField(default=True)
    default_playback_speed = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.00
    )
    captions_enabled = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_settings'
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"Settings of {self.user.email}"


class UserSocial(models.Model):
    """
    User Social Links model - stores social media links (1:1 with User).
    Maps to 'user_social' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='social'
    )

    # Social media usernames
    facebook = models.CharField(max_length=100, blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.CharField(max_length=100, blank=True)
    github = models.CharField(max_length=100, blank=True)
    instagram = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_social'
        verbose_name = 'User Social Links'
        verbose_name_plural = 'User Social Links'

    def __str__(self):
        return f"Social links of {self.user.email}"


class UserSkill(models.Model):
    """
    User Skills model - stores user skills and proficiency levels (1:N with User).
    Maps to 'user_skills' table in the database.
    """
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skills'
    )

    # Skill information
    name = models.CharField(max_length=100)
    proficiency = models.CharField(
        max_length=20,
        choices=PROFICIENCY_CHOICES,
        default='beginner'
    )

    # Timestamps
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_skills'
        verbose_name = 'User Skill'
        verbose_name_plural = 'User Skills'
        unique_together = ['user', 'name']
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.proficiency})"

import uuid
from django.db import models
from django.conf import settings


class Enrollment(models.Model):
    """
    Enrollment model - tracks user enrollments in courses.
    Maps to 'enrollments' table in the database.
    """
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        FREE = 'free', 'Free'
        PAID = 'paid', 'Paid'
        REFUNDED = 'refunded', 'Refunded'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    # Enrollment details
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.FREE
    )
    certificate_issued = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'enrollments'
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = ['user', 'course']
        ordering = ['-enrollment_date']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['active', 'completed', 'cancelled']),
                name='valid_enrollment_status'
            ),
            models.CheckConstraint(
                check=models.Q(payment_status__in=['free', 'paid', 'refunded']),
                name='valid_payment_status'
            ),
            models.CheckConstraint(
                check=models.Q(progress_percentage__gte=0) & models.Q(progress_percentage__lte=100),
                name='valid_progress_percentage'
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"


class VideoProgress(models.Model):
    """
    Video Progress model - tracks user progress on video lectures.
    Maps to 'video_progress' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='video_progress'
    )
    lecture = models.ForeignKey(
        'courses.Lecture',
        on_delete=models.CASCADE,
        related_name='video_progress'
    )
    
    # Progress tracking
    watched_seconds = models.IntegerField(default=0)
    total_seconds = models.IntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    
    # Timestamps
    last_watched_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'video_progress'
        verbose_name = 'Video Progress'
        verbose_name_plural = 'Video Progress'
        unique_together = ['enrollment', 'lecture']
        ordering = ['-last_watched_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(watched_seconds__gte=0),
                name='valid_watched_seconds'
            ),
            models.CheckConstraint(
                check=models.Q(completion_percentage__gte=0) & models.Q(completion_percentage__lte=100),
                name='valid_completion_percentage'
            ),
        ]

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.lecture.title} ({self.completion_percentage}%)"


class Bookmark(models.Model):
    """
    Bookmark model - allows users to bookmark specific points in videos or lectures.
    Maps to 'bookmarks' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    lecture = models.ForeignKey(
        'courses.Lecture',
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    
    # Bookmark details
    title = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)
    timestamp_seconds = models.IntegerField(default=0)  # For video bookmarks
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookmarks'
        verbose_name = 'Bookmark'
        verbose_name_plural = 'Bookmarks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.lecture.title} @ {self.timestamp_seconds}s"


class Note(models.Model):
    """
    Note model - allows users to take notes during lectures.
    Maps to 'notes' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    lecture = models.ForeignKey(
        'courses.Lecture',
        on_delete=models.CASCADE,
        related_name='notes'
    )
    
    # Note details
    content = models.TextField()
    timestamp_seconds = models.IntegerField(null=True, blank=True)  # Optional timestamp for video notes
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notes'
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by {self.enrollment.user.email} on {self.lecture.title}"

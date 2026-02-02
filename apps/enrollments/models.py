import uuid
from django.db import models
from django.conf import settings


from django.utils import timezone
import uuid
from django.db import models
from django.conf import settings


class Enrollment(models.Model):
    class PaymentStatus(models.TextChoices):
        FREE = 'free', 'Free'
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        REFUNDED = 'refunded', 'Refunded'
        EXPIRED = 'expired', 'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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

    # ---------- PRICING SNAPSHOT (IMMUTABLE) ----------
    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)

    coupon = models.ForeignKey(
        'courses.Coupon',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # ---------- PAYMENT / ACCESS ----------
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    is_active = models.BooleanField(default=False)

    # ---------- EXPIRY WINDOW ----------
    expires_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)

    # ---------- PROGRESS ----------
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    is_completed = models.BooleanField(default=False)
    certificate_issued = models.BooleanField(default=False)

    # ---------- TIMESTAMPS ----------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'enrollments'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(progress_percentage__gte=0) &
                          models.Q(progress_percentage__lte=100),
                name='valid_progress_percentage'
            ),
            models.CheckConstraint(
                condition=models.Q(payment_status__in=['free', 'pending', 'paid', 'refunded', 'expired']),
                name='valid_enrollment_payment_status'
            ),
            models.UniqueConstraint(
                fields=['user', 'course'],
                name='unique_user_course_enrollment'
            ),
        ]

    def mark_expired(self):
        self.is_expired = True
        self.payment_status = self.PaymentStatus.EXPIRED
        self.is_active = False
        self.save(update_fields=['is_expired', 'payment_status', 'is_active'])

    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.payment_status})"

    def calculate_progress_percentage(self):
        """
        Calculate overall course progress as average of lecture completion percentages.
        Includes all lectures in the course, even if no progress record exists (defaults to 0%).
        """
        # Get all published lectures in the course
        from apps.courses.models import Lecture
        lectures = Lecture.objects.filter(
            section__course=self.course,
            is_published=True
        ).select_related('section')

        total_lectures = lectures.count()
        if total_lectures == 0:
            self.progress_percentage = 0.00
            self.save(update_fields=['progress_percentage'])
            return self.progress_percentage

        total_percentage = 0.0
        for lecture in lectures:
            # Get progress for this lecture, or assume 0%
            progress = self.lecture_progress.filter(lecture=lecture).first()
            completion = progress.completion_percentage if progress else 0.00
            total_percentage += completion

        self.progress_percentage = round(total_percentage / total_lectures, 2)
        self.save(update_fields=['progress_percentage'])
        return self.progress_percentage


class LectureProgress(models.Model):
    """
    Lecture Progress model - tracks user progress on video lectures.
    Maps to 'lecture_progress' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='lecture_progress'
    )
    lecture = models.ForeignKey(
        'courses.Lecture',
        on_delete=models.CASCADE,
        related_name='lecture_progress'
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
        db_table = 'lecture_progress'
        verbose_name = 'Lecture Progress'
        verbose_name_plural = 'Lecture Progress'
        unique_together = ['enrollment', 'lecture']
        ordering = ['-last_watched_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(watched_seconds__gte=0),
                name='valid_watched_seconds'
            ),
            models.CheckConstraint(
                condition=models.Q(completion_percentage__gte=0) & models.Q(completion_percentage__lte=100),
                name='valid_completion_percentage'
            ),
        ]

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.lecture.title} ({self.completion_percentage}%)"


class Bookmark(models.Model):
    """
    Bookmark model - allows users to bookmark specific points in lectures.
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
    timestamp_seconds = models.IntegerField(default=0)  # For lecture bookmarks

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


# add payment models
class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = 'created', 'Created'
        AUTHORIZED = 'authorized', 'Authorized'
        CAPTURED = 'captured', 'Captured'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='INR')

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED
    )

    payment_gateway = models.CharField(max_length=20, default='razorpay')
    gateway_response = models.JSONField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['razorpay_payment_id']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=['created', 'authorized', 'captured', 'failed', 'refunded']),
                name='valid_payment_status'
            ),
        ]

    def mark_authorized(self, payment_id, signature):
        self.razorpay_payment_id = payment_id
        self.razorpay_signature = signature
        self.status = self.Status.AUTHORIZED
        self.save()

    def mark_captured(self):
        self.status = self.Status.CAPTURED
        self.save()

        enrollment = self.enrollment
        if not enrollment.is_expired:
            enrollment.payment_status = Enrollment.PaymentStatus.PAID
            enrollment.is_active = True
            enrollment.save()

    def mark_failed(self, reason=""):
        self.status = self.Status.FAILED
        self.failure_reason = reason
        self.save()

    def __str__(self):
        return f"{self.razorpay_order_id} ({self.status})"

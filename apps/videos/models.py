import uuid
from django.db import models


class VideoContent(models.Model):
    """
    Video Content model - stores video-specific content for lectures (1:1 with Lecture).
    Maps to 'video_content' table in the database.
    """
    VIDEO_PROVIDER_CHOICES = [
        ('youtube', 'YouTube'),
        ('vimeo', 'Vimeo'),
        ('aws', 'AWS'),
        ('custom', 'Custom'),
    ]

    video_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    lecture = models.OneToOneField(
        'courses.Lecture',
        on_delete=models.CASCADE,
        related_name='video_content'
    )
    
    # Video information
    video_url = models.CharField(max_length=500)
    video_provider = models.CharField(
        max_length=20,
        choices=VIDEO_PROVIDER_CHOICES,
        default='custom'
    )
    video_quality = models.JSONField(default=dict, blank=True)  # {1080p: 'url', 720p: 'url', 480p: 'url'}
    thumbnail_url = models.CharField(max_length=500, blank=True)
    captions_url = models.CharField(max_length=500, blank=True)
    
    # Metadata
    duration_seconds = models.IntegerField(null=True, blank=True)
    file_size_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'video_content'
        verbose_name = 'Video Content'
        verbose_name_plural = 'Video Content'

    def __str__(self):
        return f"Video for {self.lecture.title}"


class PDFContent(models.Model):
    """
    PDF Content model - stores PDF-specific content for lectures (1:1 with Lecture).
    Maps to 'pdf_content' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    lecture = models.OneToOneField(
        'courses.Lecture',
        on_delete=models.CASCADE,
        related_name='pdf_content'
    )
    
    # PDF information
    pdf_url = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_size_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    total_pages = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pdf_content'
        verbose_name = 'PDF Content'
        verbose_name_plural = 'PDF Content'

    def __str__(self):
        return f"PDF for {self.lecture.title}"


class LectureResource(models.Model):
    """
    Lecture Resources model - stores downloadable resources for lectures (1:N with Lecture).
    Maps to 'lecture_resources' table in the database.
    """
    RESOURCE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('document', 'Document'),
        ('code', 'Code'),
        ('other', 'Other'),
    ]

    resource_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    lecture = models.ForeignKey(
        'courses.Lecture',
        on_delete=models.CASCADE,
        related_name='resources'
    )
    
    # Resource information
    title = models.CharField(max_length=255)
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        default='other'
    )
    file_url = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_size_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lecture_resources'
        verbose_name = 'Lecture Resource'
        verbose_name_plural = 'Lecture Resources'
        ordering = ['lecture', 'created_at']

    def __str__(self):
        return f"{self.title} - {self.lecture.title}"

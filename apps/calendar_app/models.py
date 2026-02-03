import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class CalendarEvent(models.Model):
    """
    Calendar Event model - stores events for courses and classes.
    Maps to 'calendar_events' table in the database.
    """
    
    EVENT_TYPE_CHOICES = [
        ('class', 'Class Session'),
        ('workshop', 'Workshop'),
        ('webinar', 'Webinar'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
        ('deadline', 'Deadline'),
        ('holiday', 'Holiday'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Event information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='class'
    )
    
    # Time information
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Location/Meeting information
    location = models.CharField(max_length=255, blank=True)
    meeting_link = models.URLField(blank=True, help_text="Video conference or meeting link")
    
    # Relationships
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_events_created'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_events'
    )
    
    # Capacity and attendance
    max_capacity = models.IntegerField(null=True, blank=True, help_text="Maximum participants allowed")
    current_attendees = models.IntegerField(default=0)
    
    # Event status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    is_public = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False)
    
    # Additional fields
    materials_url = models.URLField(blank=True, help_text="Link to course materials or resources")
    recording_url = models.URLField(blank=True, help_text="Link to event recording")
    notes = models.TextField(blank=True)
    
    # Reminders
    send_reminder = models.BooleanField(default=True)
    reminder_before_hours = models.IntegerField(default=24, help_text="Hours before event to send reminder")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='calendar_events_created_by'
    )
    
    class Meta:
        db_table = 'calendar_events'
        verbose_name = 'Calendar Event'
        verbose_name_plural = 'Calendar Events'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['start_time', 'status']),
            models.Index(fields=['instructor', 'start_time']),
            models.Index(fields=['course', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def is_happening_now(self):
        """Check if event is currently happening."""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    def is_upcoming(self):
        """Check if event is upcoming."""
        return self.start_time > timezone.now()
    
    def is_past(self):
        """Check if event is in the past."""
        return self.end_time < timezone.now()
    
    def duration_minutes(self):
        """Get duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)


class EventAttendee(models.Model):
    """
    Event Attendee model - tracks user attendance for calendar events.
    Maps to 'event_attendees' table in the database.
    """
    
    ATTENDANCE_STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('attended', 'Attended'),
        ('absent', 'Absent'),
        ('cancelled', 'Cancelled'),
        ('waitlisted', 'Waitlisted'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    event = models.ForeignKey(
        CalendarEvent,
        on_delete=models.CASCADE,
        related_name='attendees'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_event_attendances'
    )
    
    # Attendance tracking
    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='registered'
    )
    attended_at = models.DateTimeField(null=True, blank=True)
    
    # Ratings and feedback
    rating = models.IntegerField(null=True, blank=True, help_text="Rating out of 5")
    feedback = models.TextField(blank=True)
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'event_attendees'
        verbose_name = 'Event Attendee'
        verbose_name_plural = 'Event Attendees'
        unique_together = ('event', 'user')
        ordering = ['-registered_at']
        indexes = [
            models.Index(fields=['event', 'attendance_status']),
            models.Index(fields=['user', 'attendance_status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.event.title}"

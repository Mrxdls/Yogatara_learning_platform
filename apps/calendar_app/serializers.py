from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import CalendarEvent, EventAttendee
from apps.courses.models import Course

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information serializer for nested representation"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']
        read_only_fields = ['id', 'email', 'full_name']


class EventAttendeeSerializer(serializers.ModelSerializer):
    """Serializer for event attendee - tracks attendance and feedback"""
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = EventAttendee
        fields = [
            'id', 
            'event',
            'user', 
            'user_id',
            'attendance_status', 
            'attended_at',
            'rating', 
            'feedback',
            'registered_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'event', 'registered_at', 'updated_at', 'attended_at']
        extra_kwargs = {
            'attendance_status': {'required': False},
            'rating': {'required': False},
            'feedback': {'required': False},
        }
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class CalendarEventListSerializer(serializers.ModelSerializer):
    """Serializer for listing calendar events - lightweight representation"""
    instructor = UserBasicSerializer(read_only=True)
    instructor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='instructor',
        write_only=True,
        required=False
    )
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    attendee_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    event_status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    event_type_display = serializers.CharField(
        source='get_event_type_display',
        read_only=True
    )
    
    class Meta:
        model = CalendarEvent
        fields = [
            'id',
            'title',
            'event_type',
            'event_type_display',
            'start_time',
            'end_time',
            'timezone',
            'location',
            'meeting_link',
            'instructor',
            'instructor_id',
            'course_title',
            'status',
            'event_status_display',
            'is_public',
            'attendee_count',
            'max_capacity',
            'is_full',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'attendee_count', 'is_full', 'created_at', 'updated_at']
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_attendee_count(self, obj):
        """Get total number of attendees (registered + attended)"""
        return obj.attendees.filter(
            attendance_status__in=['registered', 'attended']
        ).count()
    
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_full(self, obj):
        """Check if event is at max capacity"""
        if obj.max_capacity is None:
            return False
        return obj.current_attendees >= obj.max_capacity


class CalendarEventDetailSerializer(serializers.ModelSerializer):
    """Serializer for calendar event details - comprehensive representation"""
    instructor = UserBasicSerializer(read_only=True)
    instructor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='instructor',
        write_only=True,
        required=False
    )
    created_by = UserBasicSerializer(read_only=True)
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='created_by',
        write_only=True,
        required=False
    )
    
    course_id = serializers.CharField(
        source='course.id',
        read_only=True,
        allow_null=True
    )
    course = serializers.SerializerMethodField(read_only=True)
    
    # Nested attendees
    attendees = EventAttendeeSerializer(many=True, read_only=True)
    attendee_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    
    # Event status helpers
    event_status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    event_type_display = serializers.CharField(
        source='get_event_type_display',
        read_only=True
    )
    is_happening_now = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = CalendarEvent
        fields = [
            'id',
            # Basic information
            'title',
            'description',
            'event_type',
            'event_type_display',
            # Time information
            'start_time',
            'end_time',
            'timezone',
            'duration_minutes',
            # Location
            'location',
            'meeting_link',
            # Relationships
            'instructor',
            'instructor_id',
            'created_by',
            'created_by_id',
            'course',
            'course_id',
            # Capacity
            'max_capacity',
            'current_attendees',
            'attendee_count',
            'is_full',
            # Status
            'status',
            'event_status_display',
            'is_public',
            'is_recurring',
            'is_happening_now',
            'is_upcoming',
            'is_past',
            # Additional resources
            'materials_url',
            'recording_url',
            'notes',
            # Reminders
            'send_reminder',
            'reminder_before_hours',
            # Attendees
            'attendees',
            # Timestamps
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 
            'current_attendees',
            'attendee_count',
            'is_full',
            'attendees',
            'is_happening_now',
            'is_upcoming',
            'is_past',
            'duration_minutes',
            'created_at',
            'updated_at'
        ]
        extra_kwargs = {
            'description': {'required': False},
            'location': {'required': False},
            'meeting_link': {'required': False},
            'max_capacity': {'required': False},
            'is_public': {'required': False},
            'is_recurring': {'required': False},
            'materials_url': {'required': False},
            'recording_url': {'required': False},
            'notes': {'required': False},
            'send_reminder': {'required': False},
            'course_id': {'required': False},
            'instructor_id': {'required': False},
        }
    
    def validate_start_time(self, value):
        """Validate start_time is in the future"""
        from django.utils import timezone
        # Allow past events for updates, only validate for creates
        if not self.instance:
            if value < timezone.now():
                raise serializers.ValidationError(
                    "Start time must be in the future."
                )
        return value
    
    def validate(self, data):
        """Validate end_time is after start_time"""
        start_time = data.get('start_time') or self.instance.start_time
        end_time = data.get('end_time') or self.instance.end_time
        
        if end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })
        return data
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_course(self, obj):
        """Lazy load course information"""
        if obj.course:
            return {
                'id': str(obj.course.id),
                'title': obj.course.title,
                'slug': obj.course.slug,
            }
        return None
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_attendee_count(self, obj):
        """Get total number of registered attendees"""
        return obj.attendees.filter(
            attendance_status__in=['registered', 'attended']
        ).count()
    
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_full(self, obj):
        """Check if event is at max capacity"""
        if obj.max_capacity is None:
            return False
        return obj.current_attendees >= obj.max_capacity
    
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_happening_now(self, obj):
        """Check if event is happening now"""
        return obj.is_happening_now()
    
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_upcoming(self, obj):
        """Check if event is upcoming"""
        return obj.is_upcoming()
    
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_past(self, obj):
        """Check if event is in the past"""
        return obj.is_past()
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_duration_minutes(self, obj):
        """Get event duration in minutes"""
        return obj.duration_minutes()


class CalendarEventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating calendar events"""
    instructor_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='instructor',
        required=False
    )
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CalendarEvent
        fields = [
            'title',
            'description',
            'event_type',
            'start_time',
            'end_time',
            'timezone',
            'location',
            'meeting_link',
            'instructor_id',
            'course_id',
            'max_capacity',
            'status',
            'is_public',
            'is_recurring',
            'materials_url',
            'recording_url',
            'notes',
            'send_reminder',
            'reminder_before_hours',
        ]
        extra_kwargs = {
            'title': {'required': True},
            'start_time': {'required': True},
            'end_time': {'required': True},
            'description': {'required': False},
            'location': {'required': False},
            'meeting_link': {'required': False},
            'max_capacity': {'required': False},
            'is_public': {'required': False},
            'is_recurring': {'required': False},
            'materials_url': {'required': False},
            'recording_url': {'required': False},
            'notes': {'required': False},
            'send_reminder': {'required': False},
        }
    
    def validate_start_time(self, value):
        """Validate start_time"""
        from django.utils import timezone
        if not self.instance and value < timezone.now():
            raise serializers.ValidationError(
                "Start time must be in the future."
            )
        return value
    
    def validate(self, data):
        """Validate end_time is after start_time"""
        start_time = data.get('start_time') or (self.instance.start_time if self.instance else None)
        end_time = data.get('end_time') or (self.instance.end_time if self.instance else None)
        
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })
        return data
    
    def create(self, validated_data):
        """Create a new calendar event"""
        # Set created_by and instructor if not provided
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data.setdefault('created_by', request.user)
            validated_data.setdefault('instructor', request.user)
        
        return super().create(validated_data)


class EventAttendeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for registering users to events"""
    class Meta:
        model = EventAttendee
        fields = ['user_id', 'attendance_status']
        extra_kwargs = {
            'user_id': {'required': True},
            'attendance_status': {'required': False},
        }
    
    def create(self, validated_data):
        """Create attendee record"""
        event_id = self.context.get('event_id')
        validated_data['event_id'] = event_id
        return super().create(validated_data)

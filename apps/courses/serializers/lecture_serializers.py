from rest_framework import serializers
from django.utils.text import slugify
from django.db import models

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from core.cdn_helper import BunnyService
from ..models import Course, Category, CoursePricing, Section, Lecture
import secrets
import string
from apps.enrollments.serializers.lecture_progress_serializers import LectureProgressSerializer



class LectureCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        write_only=True,
        required=True,
        help_text="Lecture video file"
    )

    class Meta:
        model = Lecture
        fields = [
            'title',
            'description',
            'content_type',
            'order_index',
            'is_published',
            'file',
        ]
        extra_kwargs = {
            'content_type': {'default': 'video'},
            'is_published': {'default': True},
            'order_index': {'required': False, 'allow_null': True},
        }
    
    # Override to explicitly set binary format
    def get_fields(self):
        fields = super().get_fields()
        # Make sure file field has binary format in schema
        if 'file' in fields:
            fields['file'].style = {'base_template': 'file.html'}
        return fields

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value

    def validate_order_index(self, value):
        if value and value < 1:
            raise serializers.ValidationError("Order must be a positive integer.")
        return value

    def validate_file(self, value):
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 2GB.")

        if not value.name.lower().endswith(('.mp4', '.mov', '.avi')):
            raise serializers.ValidationError("Invalid video format.")

        return value
    
    def save(self, **kwargs):
        # Always auto-assign order_index for new lectures
        section = kwargs.get('section')
        if section and not self.instance:  # Only for creating new instances
            # Get the max order_index for this section and add 1
            max_order = Lecture.objects.filter(section=section).aggregate(
                max_order=models.Max('order_index')
            )['max_order']
            self.validated_data['order_index'] = (max_order or 0) + 1
        
        return super().save(**kwargs)
    
    def create(self, validated_data):
        # Remove 'file' from validated_data as it's not a model field
        # The file is handled separately in the view
        validated_data.pop('file', None)
        return super().create(validated_data)

class LectureReadSerializer(serializers.ModelSerializer):
    streaming_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Lecture
        fields = [
            'id',
            'section',
            'title',
            'description',
            'content_type',
            'content_url',
            'streaming_url',
            'order_index',
            'is_published',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'section', 'created_at', 'updated_at', 'content_url', 'streaming_url']
    
    def get_streaming_url(self, obj):
        """Generate streaming URL from content_url"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        if not obj.content_url:
            return None
        url = BunnyService.get_streaming_link(video_id=obj.content_url)
        return url
   
class LectureDetailSerializer(serializers.ModelSerializer):
    """Serializer for lecture details - conditionally includes streaming URL only in detail views"""
    
    streaming_url = serializers.SerializerMethodField()
    section_title = serializers.CharField(source='section.title', read_only=True)
    lecture_progress = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = [
            'id', 'section', 'section_title', 'title', 'description',
            'content_type', 'streaming_url', 'content_url',
            'order_index', 'is_published', 'lecture_progress',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'section', 'section_title', 'streaming_url', 'content_url', 'content_type',
            'lecture_progress', 'created_at', 'updated_at'
        ]

    def get_fields(self):
        """Exclude streaming_url field in list views for better performance"""
        fields = super().get_fields()
        request = self.context.get('request')
        
        # Remove streaming_url from list views
        if request and getattr(request, 'resolver_match', None):
            view = self.context.get('view')
            if view and getattr(view, 'action', None) == 'list':
                fields.pop('streaming_url', None)
        
        return fields
    
    def get_lecture_progress(self, obj):
        """Get lecture progress for the requesting user"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        enrollment = obj.section.course.enrollments.filter(
            user=request.user,
            is_active=True
        ).first()
        
        
        if not enrollment:
            return None
        
        progress = enrollment.lecture_progress.filter(lecture=obj).first()
        if not progress:
            # create 0% progress in lecture progress
            serializer = LectureProgressSerializer(data={
                'lecture': obj.id,
                'watched_seconds': 0,
                'total_seconds': 0
            }, context={'enrollment': enrollment})
            if serializer.is_valid():
                progress = serializer.save(enrollment=enrollment)
            else:
                raise serializers.ValidationError("Could not create lecture progress.")
        return {
            'watched_seconds': progress.watched_seconds,
            'progress_percentage': progress.progress_percentage,
            'last_watched_at': progress.last_watched_at
        }

    def get_streaming_url(self, obj):
        # Check if request context is available and user is authenticated
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None  # or return a message like "Authentication required"
        url = BunnyService.get_streaming_link(video_id=obj.content_url)
        print(f"[LectureDetailSerializer] Streaming URL for lecture {obj.id}: {url}")
        return url
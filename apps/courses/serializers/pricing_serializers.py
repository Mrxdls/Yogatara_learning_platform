from rest_framework import serializers
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from core.cdn_helper import BunnyService
from ..models import Course, Category, CoursePricing, Section, Lecture
import secrets
import string

class CoursePricingSerializer(serializers.ModelSerializer):
    """Serializer for Course Pricing"""
    # Nested course representation for reading (lazy loaded)
    course = serializers.SerializerMethodField()
    course_id = serializers.UUIDField(write_only=True, required=True, source='course')

    class Meta:
        model = CoursePricing
        fields = [
            'id', 'course', 'course_id', 'price', 'sale_price', 'currency', 'is_free',
            'sale_start_date', 'sale_end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'course', 'created_at', 'updated_at']
        extra_kwargs = {
            'price': {'required': True},
            'sale_price': {'required': False},
            'sale_start_date': {'required': False},
            'sale_end_date': {'required': False},
            'currency': {'required': False},
            'is_free': {'required': False},
        }

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_course(self, obj):
        """Lazy load CourseSerializer to avoid circular imports"""
        from .course_serializers import CourseListSerializer
        
        if obj.course:
            return CourseListSerializer(obj.course).data
        return None

    def validate_course_id(self, value):
        """Validate that course exists"""
        try:
            course = Course.objects.get(id=value)
            return course
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course does not exist.")

    def validate(self, data):
        is_free = data.get('is_free', False)
        price = data.get('price')
        sale_price = data.get('sale_price')

        if is_free:
            # Free courses always have price = 0 and no sale price
            data['price'] = 0
            if sale_price is not None:
                data['sale_price'] = None  # Remove sale price for free courses
        else:
            # Paid courses validations
            if price is None or price <= 0:
                raise serializers.ValidationError("Paid courses must have a positive price.")
            if sale_price is not None and sale_price >= price:
                raise serializers.ValidationError("Sale price must be less than the regular price.")
        
        return data

    def validate_price(self, value):
        """Validate price is non-negative"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def create(self, validated_data):
        """Create pricing for course"""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update pricing for course"""
        return super().update(instance, validated_data)




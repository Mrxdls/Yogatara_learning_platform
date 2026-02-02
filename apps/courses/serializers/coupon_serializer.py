from rest_framework import serializers
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from core.cdn_helper import BunnyService
from ..models import Coupon, CouponCourse, Course
from apps.authentication.models import User
import secrets
import string

    
class CouponSerializer(serializers.ModelSerializer):
    """Serializer for Course Coupons"""
    coupon_courses = serializers.SerializerMethodField()
    is_for_all_users = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value', 'max_uses',
            'current_uses', 'valid_from', 'valid_to', 'is_active',
            'coupon_courses', 'is_for_all_users', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_uses', 'created_at', 'updated_at']
        extra_kwargs = {
            'code': {'required': False},  # Can be auto-generated
            'discount_type': {'required': True},
            'discount_value': {'required': True},
            'max_uses': {'required': False},
            'valid_from': {'required': False},
            'valid_to': {'required': False},
            'is_active': {'required': False},
        }

    def validate_code(self, value):
        """Validate coupon code or auto-generate if not provided"""
        if value:
            # If code provided, validate it
            if len(value) < 5:
                raise serializers.ValidationError("Coupon code must be at least 5 characters long.")
            
            # Check uniqueness (exclude current instance during updates)
            query = Coupon.objects.filter(code__iexact=value)
            if self.instance:
                query = query.exclude(id=self.instance.id)
            
            if query.exists():
                raise serializers.ValidationError("Coupon code already exists.")
            
            value = value.strip().upper()
        else:
            # Auto-generate if not provided: YOGA + 5 random alphanumeric
            while True:
                random_suffix = ''.join(
                    secrets.choice(string.ascii_uppercase + string.digits) 
                    for _ in range(5)
                )
                code = 'YOGA' + random_suffix
                if not Coupon.objects.filter(code=code).exists():
                    value = code
                    break
        
        return value
    
    def validate_discount_value(self, value):
        """Validate discount value based on discount type"""
        discount_type = self.initial_data.get('discount_type')
        
        # For percentage: 0 < value <= 100
        if discount_type == 'percent':
            if value <= 0 or value > 100:
                raise serializers.ValidationError(
                    "For percentage discount, value must be between 0 and 100."
                )
        # For fixed amount: value > 0
        else:
            if value <= 0:
                raise serializers.ValidationError("Discount value must be positive.")
        
        return value

    def validate(self, data):
        """Validate coupon dates if provided"""
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')
        
        # Both dates provided - ensure valid_from < valid_to
        if valid_from and valid_to and valid_from >= valid_to:
            raise serializers.ValidationError(
                "valid_from must be before valid_to."
            )
        
        return data

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_coupon_courses(self, obj):
        """Get courses associated with this coupon"""
        try:
            coupon_courses = CouponCourse.objects.filter(coupon=obj)
            courses = [cc.course for cc in coupon_courses]
            
            # Return course data as dicts, not IDs
            return [
                {
                    'id': str(course.id),
                    'title': course.title,
                    'code': course.course_code,
                    'slug': course.slug,
                }
                for course in courses
            ]
        except Exception as e:
            print(f"Error in get_coupon_courses: {e}")
            return []
    
    @extend_schema_field(serializers.BooleanField())
    def get_is_for_all_users(self, obj):
        """Check if coupon is available to all users"""
        return obj.is_for_all_users()
    def create(self, validated_data):
        """Create coupon"""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update coupon"""
        return super().update(instance, validated_data)


class CouponCourseSerializer(serializers.ModelSerializer):
    """Serializer for associating Coupons with Courses"""
    class Meta:
        model = CouponCourse
        fields = ['id', 'coupon_id', 'course_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'coupon_id': {'required': True},
            'course_id': {'required': True},
        }

    def validate_coupon_id(self, value):
        """Validate that coupon exists"""
        try:
            Coupon.objects.get(id=value)
            return value
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Coupon does not exist.")

    def validate_course_id(self, value):
        """Validate that course exists"""
        try:
            Course.objects.get(id=value)
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course does not exist.")



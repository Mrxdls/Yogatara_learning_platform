from rest_framework import serializers
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from core.cdn_helper import BunnyService
from ..models import Course, Category, CoursePricing, Section, Lecture
import secrets
import string



class CourseSerializer(serializers.ModelSerializer):
    """Serializer for course CRUD operations - create, read, update, delete"""

    # Nested category representation for reading (lazy loaded)
    category = serializers.SerializerMethodField()
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='category',
        write_only=True,
        required=False
    )

    # Read-only fields
    slug = serializers.SlugField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # Custom field for created_by (instructor info)
    created_by = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = Course
        fields = [
            # Basic info
            'id', 'course_code', 'title', 'slug',
            'short_description', 'description',

            # Course properties
            'level', 'language', 'status',

            # Relationships
            'category', 'category_id', 'created_by',

            # Media
            'thumbnail_url', 'promo_video_url',

            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'course_code', 'slug',
                           'created_at', 'updated_at']
        extra_kwargs = {
            # Make some fields optional for creation
            'course_code': {'required': False},
            'short_description': {'required': False},
            'description': {'required': False},
            'level': {'required': False},
            'language': {'required': False},
            'status': {'required': False},
            'thumbnail_url': {'required': False},
            'promo_video_url': {'required': False},
        }

    def validate_course_code(self, value):
        """Validate course code uniqueness"""
        if self.instance and Course.objects.filter(course_code=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Course code must be unique.")
        elif not self.instance and Course.objects.filter(course_code=value).exists():
            raise serializers.ValidationError("Course code must be unique.")
        return value

    def validate_title(self, value):
        """Validate title uniqueness and length"""
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")

        # Check title uniqueness (case-insensitive)
        if self.instance and Course.objects.filter(title__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A course with this title already exists.")
        elif not self.instance and Course.objects.filter(title__iexact=value).exists():
            raise serializers.ValidationError("A course with this title already exists.")

        return value

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_category(self, obj):
        """Lazy load CategorySerializer to avoid circular imports"""
        from .category_serializers import CategorySerializer
        
        if obj.category:
            return CategorySerializer(obj.category).data
        return None

    # def validate_category_id(self, value):
    #     """Validate that category exists and is active"""
    #     try:
    #         category = Category.objects.get(id=value, is_active=True)
    #         return category
    #     except Category.DoesNotExist:
    #         raise serializers.ValidationError("Invalid or inactive category.")

    def create(self, validated_data):
        """Create course with auto-generated fields and defaults"""

        # Set defaults for creation
        defaults = {
            'language': validated_data.get('language', 'English'),
            'status': validated_data.get('status', 'draft'),
        }

        # Generate random alphanumeric course code (8 characters)
        if not validated_data.get('course_code'):
            characters = string.ascii_uppercase + string.digits
            while True:
                course_code = ''.join(secrets.choice(characters) for _ in range(8))
                if not Course.objects.filter(course_code=course_code).exists():
                    break
            defaults['course_code'] = course_code

        # Generate unique slug from title
        base_slug = slugify(validated_data['title'])
        slug = base_slug
        counter = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        defaults['slug'] = slug

        # Set created_by from request user
        request = self.context.get('request')
        if request and request.user:
            defaults['created_by'] = request.user

        # Merge defaults with validated data
        validated_data.update(defaults)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update course with slug regeneration if title changed"""
        if 'title' in validated_data and validated_data['title'] != instance.title:
            base_slug = slugify(validated_data['title'])
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(id=instance.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            validated_data['slug'] = slug

        return super().update(instance, validated_data)








class CourseDetailSerializer(serializers.ModelSerializer):
    """Read-only serializer for course details - no validation needed"""

    # Nested category representation (lazy loaded)
    category = serializers.SerializerMethodField()

    # Nested pricing representation (lazy loaded)
    pricing = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    # Read-only fields
    slug = serializers.SlugField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True)
    enrollment = serializers.SerializerMethodField(read_only=True)

    # Custom field for created_by (instructor info)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = Course
        fields = [
            # Basic info
            'id', 'course_code', 'title', 'slug',
            'short_description', 'description',

            # Course properties
            'level', 'language', 'status',

            # Relationships
            'category', 'created_by_name',

            # Pricing
            'pricing',

            # Media
            'thumbnail_url', 'promo_video_url',

            # Timestamps
            'created_at', 'updated_at', 'published_at', 'enrollment'
        ]
        read_only_fields = ['id', 'course_code', 'title', 'slug',
                           'short_description', 'description', 'level',
                           'language', 'status', 'category', 'created_by_name',
                           'thumbnail_url', 'promo_video_url', 'created_at',
                           'updated_at', 'published_at', 'pricing', 'enrollment']

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_category(self, obj):
        """Lazy load CategorySerializer"""
        from .category_serializers import CategorySerializer
        
        if obj.category:
            return CategorySerializer(obj.category).data
        return None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_pricing(self, obj):
        """Lazy load CoursePricingSerializer"""
        from .pricing_serializers import CoursePricingSerializer
        
        if hasattr(obj, 'pricing'):
            return CoursePricingSerializer(obj.pricing).data
        return None

    def get_is_enrolled(self, obj):
        """Check if the requesting user is enrolled in the course"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(user=request.user,is_active=True).exists()
        return False
    
    def get_enrollment(self, obj):
        """Get enrollment details for the requesting user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            enrollment = obj.enrollments.filter(user=request.user,is_active=True).first()
            if enrollment:
                from apps.enrollments.serializers.enrollment_serializers import EnrollmentDetailSerializer
                return EnrollmentDetailSerializer(enrollment).data
        return None

class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for course listings"""

    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    pricing = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'course_code', 'title', 'slug',
            'short_description', 'level', 'status',
            'category_name', 'created_by_name',
            'pricing', 'thumbnail_url', 'created_at', 'published_at'
        ]

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_pricing(self, obj):
        """Lazy load CoursePricingSerializer safely"""
        try:
            from .pricing_serializers import CoursePricingSerializer
            
            pricing = getattr(obj, 'pricing', None)
            if pricing:
                return {
                    'price': pricing.price,
                    'sale_price': pricing.sale_price,
                    'currency': pricing.currency,
                    'is_free': pricing.is_free
                }
            return None
        except Exception:
            return None




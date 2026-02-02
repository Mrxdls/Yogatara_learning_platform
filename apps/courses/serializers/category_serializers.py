from rest_framework import serializers
from django.utils.text import slugify
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from core.cdn_helper import BunnyService
from ..models import Course, Category, CoursePricing, Section, Lecture
import secrets
import string



class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Course Category"""

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'is_active', 'display_order'
        ]
        read_only_fields = ['id', 'slug']
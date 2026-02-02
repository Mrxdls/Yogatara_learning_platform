from rest_framework import serializers
from ..models import Course, Section


class SectionSerializer(serializers.ModelSerializer):
    """Serializer for Course Sections"""

    # Write-only field for creating/updating with course_id
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course'
    )

    class Meta:
        model = Section
        fields = [
            'id', 'course_id', 'title', 'description', 'order_index',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'course_id']
        extra_kwargs = {
            'title': {'required': True, 'max_length': 255},
            'description': {'required': False, 'allow_blank': True},
            'order_index': {'required': True},
        }

    def validate_title(self, value):
        """Validate title length"""
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value

    def validate_order_index(self, value):
        """Validate order is positive"""
        if value < 1:
            raise serializers.ValidationError("Order must be a positive integer.")
        return value

    def create(self, validated_data):
        """Create course section"""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update course section"""
        return super().update(instance, validated_data)



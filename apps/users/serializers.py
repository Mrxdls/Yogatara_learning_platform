from rest_framework import serializers
from .models import UserProfile, UserSettings, UserSocial, UserSkill


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (extended user information)"""
    class Meta:
        model = UserProfile
        fields = [
            'id', 
            'user',
            'full_name', 
            'display_name', 
            'avatar_url', 
            'bio', 
            'phone', 
            'location', 
            'timezone', 
            'website', 
            'education', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user settings (preferences and configuration)"""
    class Meta:
        model = UserSettings
        fields = [
            'id',
            'user',
            'email_course_updates',
            'email_assignments',
            'email_announcements',
            'email_weekly_digest',
            'push_course_updates',
            'push_assignments',
            'push_announcements',
            'profile_visibility',
            'show_enrolled_courses',
            'show_progress',
            'theme',
            'language',
            'autoplay_videos',
            'default_playback_speed',
            'captions_enabled',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSocialSerializer(serializers.ModelSerializer):
    """Serializer for user social media links"""
    class Meta:
        model = UserSocial
        fields = [
            'id',
            'user',
            'facebook',
            'twitter',
            'linkedin',
            'github',
            'instagram',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSkillSerializer(serializers.ModelSerializer):
    """Serializer for user skills"""
    class Meta:
        model = UserSkill
        fields = [
            'id',
            'user',
            'name',
            'proficiency',
            'added_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'added_at', 'updated_at']

    def validate_name(self, value):
        """Validate skill name is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Skill name cannot be empty.")
        return value.strip()


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user profile with related data"""
    settings = UserSettingsSerializer(read_only=True)
    social = UserSocialSerializer(read_only=True)
    skills = UserSkillSerializer(read_only=True, many=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user',
            'full_name',
            'display_name',
            'avatar_url',
            'bio',
            'phone',
            'location',
            'timezone',
            'website',
            'education',
            'settings',
            'social',
            'skills',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
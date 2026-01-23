from rest_framework import serializers
from .models import UserProfile, UserSettings, UserSocial, UserSkill


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (extended user information)"""
    class Meta:
        model = UserProfile
        fields = [
            'id', 
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

    full_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    avatar_url = serializers.CharField(required=False, allow_blank=True, max_length=500)
    bio = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    location = serializers.CharField(required=False, allow_blank=True, max_length=100)
    timezone = serializers.CharField(required=False, max_length=50)
    website = serializers.CharField(required=False, allow_blank=True, max_length=255)
    education = serializers.CharField(required=False, allow_blank=True)



class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user settings (preferences and configuration)"""
    class Meta:
        model = UserSettings
        fields = [
            'id',
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

    email_course_updates = serializers.BooleanField(required=False)
    email_assignments = serializers.BooleanField(required=False)
    email_announcements = serializers.BooleanField(required=False)
    email_weekly_digest = serializers.BooleanField(required=False)
    push_course_updates = serializers.BooleanField(required=False)
    push_assignments = serializers.BooleanField(required=False)
    push_announcements = serializers.BooleanField(required=False)
    profile_visibility = serializers.ChoiceField(
        choices=UserSettings.PROFILE_VISIBILITY_CHOICES,
        required=False
    )
    show_enrolled_courses = serializers.BooleanField(required=False)
    show_progress = serializers.BooleanField(required=False)
    theme = serializers.ChoiceField(
        choices=UserSettings.THEME_CHOICES,
        required=False
    )
    language = serializers.CharField(required=False, max_length=10)
    autoplay_videos = serializers.BooleanField(required=False)
    default_playback_speed = serializers.DecimalField(required=False, max_digits=3, decimal_places=2)
    captions_enabled = serializers.BooleanField(required=False)


class UserSocialSerializer(serializers.ModelSerializer):
    """Serializer for user social media links"""
    class Meta:
        model = UserSocial
        fields = [
            'id',
            'facebook',
            'twitter',
            'linkedin',
            'github',
            'instagram',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    facebook = serializers.URLField(required=False, allow_blank=True)
    twitter = serializers.URLField(required=False, allow_blank=True)
    linkedin = serializers.URLField(required=False, allow_blank=True)
    github = serializers.URLField(required=False, allow_blank=True)
    instagram = serializers.URLField(required=False, allow_blank=True)



class UserSkillSerializer(serializers.ModelSerializer):
    """Serializer for user skills"""
    class Meta:
        model = UserSkill
        fields = [
            'id',
            'name',
            'proficiency',
            'added_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'added_at', 'updated_at']

    proficiency = serializers.ChoiceField(
        choices=UserSkill.PROFICIENCY_CHOICES,
        required=False
    )
    name = serializers.CharField(max_length=100)
    

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


class UserProfilePictureSerializer(serializers.ModelSerializer):
    """Serializer for uploading user profile picture"""
    file = serializers.FileField(write_only=True, required=True)
    
    class Meta:
        model = UserProfile
        fields = ['avatar_url', 'file']
        read_only_fields = ['avatar_url']

    def validate_file(self, value):
        """Validate file size and type"""
        if value.size > 5 * 1024 * 1024:  # 5MB limit
            raise serializers.ValidationError("File size must not exceed 5MB")
        
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only image files are allowed (JPEG, PNG, GIF, WebP)")
        
        return value
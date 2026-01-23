from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from apps.users.models import UserProfile, UserSettings, UserSocial
from apps.users.serializers import (
    UserProfileSerializer,
    UserSettingsSerializer,
    UserSocialSerializer,
    UserSkillSerializer
)


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for general use"""
    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'is_active', 'email_verified', 'created_at']
        read_only_fields = ['id', 'created_at', 'email_verified']


class UserMeSerializer(serializers.ModelSerializer):
    """Serializer for current user details with all related data"""
    profile = UserProfileSerializer(read_only=True)
    settings = UserSettingsSerializer(read_only=True)
    social = UserSocialSerializer(read_only=True)
    skills = UserSkillSerializer(read_only=True, many=True)
    
    class Meta:
        model = User
        fields = [
            'id', 
            'email', 
            'role', 
            'is_active', 
            'email_verified', 
            'created_at', 
            'updated_at', 
            'last_login_at',
            'profile',
            'settings',
            'social',
            'skills'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at', 'last_login_at', 'email_verified']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    
    Password Requirements:
    - Minimum 8 characters
    - Cannot be too similar to email or other user attributes
    - Cannot be a common/weak password (e.g., '123456', 'password', 'admin')
    - Cannot be entirely numeric
    - Examples of strong passwords: 'SecurePass123!', 'MyPassword@2024'
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters, not entirely numeric, and not a common password"
    )
    full_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Full name for user profile (optional)"
    )
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        default=User.Role.STUDENT,
        help_text="User role: 'student', 'instructor', or 'admin'"
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'role']

    def create(self, validated_data):
        # Extract full_name (not a User model field)
        full_name = validated_data.pop('full_name', '')
        # validated_data['password'] = set_password(validated_data['password'])
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', User.Role.STUDENT)
        )
        
        # Create user profile with full_name
        UserProfile.objects.create(
            user=user,
            full_name=full_name
        )
        
        # Create user settings with defaults
        UserSettings.objects.create(user=user)
        
        # Create user social links (empty initially)
        UserSocial.objects.create(user=user)
        
        return user
    

# Alias for backward compatibility
SignupSerializer = RegisterSerializer


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    
    Example Request:
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    
    Example Response:
    {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "role": "student",
            "is_active": true,
            "email_verified": false,
            "created_at": "2024-01-21T10:30:00Z"
        }
    }
    """
    email = serializers.EmailField(required=True, help_text="User email address")
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="User password"
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization'
            )


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change
    
    Password Requirements:
    - Minimum 8 characters
    - Cannot be too similar to email or other user attributes
    - Cannot be a common/weak password (e.g., '123456', 'password', 'admin')
    - Cannot be entirely numeric
    
    Example Request:
    {
        "old_password": "CurrentPassword123!",
        "new_password": "NewSecurePass456!"
    }
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Current password"
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="New password (must be at least 8 characters, not entirely numeric, and not a common password)"
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError(
                "No active user found with this email address."
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset
    
    Password Requirements:
    - Minimum 8 characters
    - Cannot be too similar to email or other user attributes
    - Cannot be a common/weak password (e.g., '123456', 'password', 'admin')
    - Cannot be entirely numeric
    
    Example Request:
    {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "uid": "550e8400-e29b-41d4-a716-446655440000",
        "new_password": "NewSecurePass456!"
    }
    """
    token = serializers.CharField(required=True, help_text="Password reset token")
    uid = serializers.CharField(required=True, help_text="User ID")
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="New password (must be at least 8 characters, not entirely numeric, and not a common password)"
    )




class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True, help_text="The refresh token")

    def validate_refresh(self, value):
        try:
            RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Invalid or expired refresh token")
        return value


class RefreshTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="New access token")
    refresh = serializers.CharField(help_text="Renewed refresh token")


class LogoutSerializer(serializers.Serializer):
    # No request body needed - tokens come from headers
    pass


class SendVerificationEmailSerializer(serializers.Serializer):
    """Serializer for sending verification email"""
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(
        choices=[('email_verification', 'Email Verification'), ('password_reset', 'Password Reset')],
        required=True
    )



from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "password")

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            email=attrs["email"],
            password=attrs["password"]
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("User account disabled")

        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        }


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


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "created_at")

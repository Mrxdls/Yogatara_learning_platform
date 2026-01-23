from datetime import datetime
from time import time
import jwt
import tempfile
import os
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.core.mail import send_mail
from django.utils import timezone

from Learning_hub import settings
from apps.authentication.models import User
from core.bg_task import upload_avatar_task, delete_file_by_cdn_url_task


from .serializers import (
    UserProfilePictureSerializer,
    UserProfileSerializer,
    UserSettingsSerializer,
    UserSkillSerializer,
    UserSocialSerializer,
)

class UserProfileView(APIView):
    """Retrieve or update user profile."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer}
    )
    # def get(self, request):
    #     profile = request.user.profile
    #     serializer = UserProfileSerializer(profile)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    )
    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserSettingsView(APIView):
    """Retrieve or update user settings."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserSettingsSerializer}
    )
    def get(self, request):
        settings = request.user.settings
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserSettingsSerializer,
        responses={200: UserSettingsSerializer}
    )
    def put(self, request):
        settings = request.user.settings
        serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserSkillsView(APIView):
    """Retrieve or update user skills."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserSkillSerializer(many=True)}
    )
    def get(self, request):
        skills = request.user.skills.all()
        serializer = UserSkillSerializer(skills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserSkillSerializer(many=True),
        responses={200: UserSkillSerializer(many=True)}
    )
    def put(self, request):
        skills = request.user.skills.all()
        serializer = UserSkillSerializer(skills, data=request.data, many=True, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserSocialView(APIView):
    """Retrieve or update user social links."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserSocialSerializer}
    )
    def get(self, request):
        social = request.user.social
        serializer = UserSocialSerializer(social)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserSocialSerializer,
        responses={200: UserSocialSerializer}
    )
    def put(self, request):
        social = request.user.social
        serializer = UserSocialSerializer(social, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserProfilePictureView(APIView):
    """Retrieve or update user profile picture."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfilePictureSerializer}
    )
    def get(self, request):
        """Get user profile picture."""
        profile = request.user.profile
        serializer = UserProfilePictureSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request={'multipart/form-data': {'type': 'object', 'properties': {'file': {'type': 'string', 'format': 'binary'}}}},
        responses={200: UserProfilePictureSerializer},
        description="Upload a new profile picture"
    )
    def put(self, request):
        """Update user profile picture (ASYNC upload)."""

        profile = request.user.profile

        profile_pic = request.data.get('file')
        if not profile_pic:
            return Response({"error": "No file provided"}, status=400)

        # Save to temp file
        import tempfile, os

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in profile_pic.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        remote_path = f"uploads/avatars/user_{request.user.id}_{profile_pic.name}"

        # Enqueue background job
        upload_avatar_task.delay(request.user.id, temp_path, remote_path)

        # Respond immediately
        return Response(
            {"message": "Profile picture upload started. It will update shortly."},
            status=202
        )
    def delete(self, request):
        """Delete user profile picture."""
        profile = request.user.profile
        if not profile.avatar_url:
            return Response({"error": "No profile picture to delete"}, status=400)

        try:
            # Enqueue deletion task
            delete_file_by_cdn_url_task.delay(profile.avatar_url)
        except Exception as e:
            print(f"[Profile Picture] Error queueing delete task: {e}")
            # Don't fail the deletion if queueing fails, log and continue

        # Clear avatar URL
        profile.avatar_url = ""
        profile.save(update_fields=["avatar_url"])

        return Response({"message": "Profile picture deletion started."}, status=202)
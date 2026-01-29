from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from django.db.models import Q
from django.shortcuts import get_object_or_404
import traceback
import tempfile
import os

from ..models import Course, Category, CoursePricing, Section, Lecture
from ..serializers import (
    CourseListSerializer,
    CategorySerializer,
    CourseSerializer,
    CoursePricingSerializer,
    LectureDetailSerializer,
    LectureCreateSerializer,
    LectureReadSerializer,
)
from core.bg_task import delete_video_task, upload_video_task
from core.cdn_helper import BunnyService


class CourseViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for managing courses.
    Supports:
    - POST /courses/ - Create course (superuser only)
    - GET /courses/ - List all courses
    - GET /courses/{id}/ - Get single course
    - PUT/PATCH /courses/{id}/ - Update course (superuser only)
    - DELETE /courses/{id}/ - Delete course (superuser only)
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseSerializer

    @extend_schema(
        tags=['Courses'],
        operation_id='courses_create',
        description="Create a new course (superuser only)",
    )
    def create(self, request, *args, **kwargs):
        """Create a new course (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can create courses.")
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=['Courses'],
        operation_id='courses_list',
        description="List all courses",
    )
    def list(self, request, *args, **kwargs):
        """Fetch all courses and return using serializer"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['Courses'],
        operation_id='courses_retrieve',
        description="Get a course by id, slug, or uuid",
        parameters=[
            OpenApiParameter(
                name='slug',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                required=False,
                description='Course slug'
            ),
            OpenApiParameter(
                name='uuid',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.UUID,
                required=False,
                description='Course UUID'
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        """Get a course by id, slug, or uuid"""
        # Support lookup by slug or uuid
        pk = self.kwargs.get(self.lookup_field)
        slug = request.query_params.get('slug')
        uuid = request.query_params.get('uuid')

        if slug:
            try:
                course = Course.objects.get(slug=slug)
                self.kwargs[self.lookup_field] = course.id
            except Course.DoesNotExist:
                return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        elif uuid:
            try:
                course = Course.objects.get(id=uuid)
                self.kwargs[self.lookup_field] = course.id
            except Course.DoesNotExist:
                return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=['Courses'],
        operation_id='courses_update',
        description="Update an existing course (superuser only)",
    )
    def update(self, request, *args, **kwargs):
        """Update an existing course (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update courses.")
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=['Courses'],
        operation_id='courses_partial_update',
        description="Partially update an existing course (superuser only)",
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a course (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update courses.")
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=['Courses'],
        operation_id='courses_destroy',
        description="Delete an existing course (superuser only)",
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an existing course (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can delete courses.")
        return super().destroy(request, *args, **kwargs)



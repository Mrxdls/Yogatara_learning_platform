
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
from ..models import Section
from core.bg_task import delete_video_task, upload_video_task
from core.cdn_helper import BunnyService
from ..serializers import SectionSerializer

class SectionViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for managing sections within a course.
    Supports:
    - POST /sections/ - Create section (requires course_id in request data)
    - GET /sections/ - List all sections (filterable by course_id query param)
    - GET /sections/{id}/ - Get single section
    - PUT/PATCH /sections/{id}/ - Update section
    - DELETE /sections/{id}/ - Delete section
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter sections by course_id if provided"""
        queryset = Section.objects.all()
        course_id = self.request.query_params.get('course_id') or self.kwargs.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    @extend_schema(
        tags=['Sections'],
        operation_id='sections_create',
        description="Create a new section in a course (superuser only)",
    )
    def create(self, request, *args, **kwargs):
        """Create a new section in a course"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can create sections.")
        
        course_id = self.kwargs.get('course_id') or request.data.get('course_id')
        
        if course_id is None:
            return Response(
                {"detail": "Course ID is required to create a section."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course_id=course_id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Sections'],
        operation_id='sections_list',
        parameters=[
            OpenApiParameter(
                name='course_id',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.UUID,
                required=False,
                description='Filter sections by Course ID'
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """Get all sections for a course"""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['Sections'], operation_id='sections_retrieve')
    def retrieve(self, request, *args, **kwargs):
        """Get a section by id"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=['Sections'],
        operation_id='sections_update',
        description="Update an existing section (superuser only)",
    )
    def update(self, request, *args, **kwargs):
        """Update an existing section (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update sections.")
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=['Sections'],
        operation_id='sections_partial_update',
        description="Partially update an existing section (superuser only)",
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a section (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update sections.")
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=['Sections'],
        operation_id='sections_destroy',
        description="Delete an existing section (superuser only)",
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an existing section (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can delete sections.")
        return super().destroy(request, *args, **kwargs)


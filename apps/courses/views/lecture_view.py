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
import logging

logger = logging.getLogger(__name__)

from apps.enrollments.models import Enrollment


from ..models import Course, Category, CoursePricing, Section, Lecture
from ..serializers import (
    LectureDetailSerializer,
    LectureCreateSerializer,
)
from core.bg_task import delete_video_task, upload_video_task
from core.cdn_helper import BunnyService
from ..models import Lecture

class LectureViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for handling all lecture operations.
    Supports:
    - POST /lectures/ - Create lecture (multipart/form-data with file upload)
    - GET /lectures/ - List all lectures (filterable by section_id query param)
    - GET /lectures/{id}/ - Get single lecture
    - PUT/PATCH /lectures/{id}/ - Update lecture (application/json only)
    - DELETE /lectures/{id}/ - Delete lecture
    """
    queryset = Lecture.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return LectureCreateSerializer
        return LectureDetailSerializer

    def get_queryset(self):
        """Filter lectures by section_id if provided"""
        queryset = Lecture.objects.all()
        section_id = self.request.query_params.get('section_id') or self.kwargs.get('section_id')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        return queryset

    # def get_parsers(self):
    #     """Use multipart parser only for create action, JSON for others"""
    #     if self.action == 'create':
    #         return [MultiPartParser(), FormParser()]
    #     return super().get_parsers()

    @extend_schema(
        tags=['Lectures'],
        operation_id='lectures_create',
        description="Create a new lecture in a section (superuser only). Requires multipart/form-data with file upload.",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Video file to upload'
                    },
                    'section_id': {
                        'type': 'string',
                        'format': 'uuid',
                        'description': 'Section ID (UUID) to which the lecture belongs'
                    },
                    'title': {
                        'type': 'string',
                        'maxLength': 255,
                        'description': 'Lecture title'
                    },
                    'description': {
                        'type': 'string',
                        'description': 'Lecture description'
                    },
                    'content_type': {
                        'type': 'string',
                        'enum': ['video'],
                        'default': 'video',
                        'description': 'Content type'
                    },
                    'order_index': {
                        'type': 'integer',
                        'minimum': 1,
                        'description': 'Display order (must be unique within section)'
                    },
                    'is_published': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'Published status'
                    }
                },
                'required': ['file', 'section_id', 'title', 'order_index']
            }
        },
        responses={
            201: LectureDetailSerializer,
            400: {'description': 'Bad request - missing required fields or invalid section_id'},
            403: {'description': 'Forbidden - requires superuser authentication'},
        },
    )
    def create(self, request, section_id=None, *args, **kwargs):
        """Create a new lecture with file upload"""
        import uuid as uuid_module
        temp_path = None
        try:
            if not request.user.is_superuser:
                raise PermissionDenied("Only superusers can create lectures.")

            # Get section_id from kwargs or request data
            section_id = section_id or self.kwargs.get('section_id') or request.data.get('section_id')
            
            if section_id is None:
                return Response(
                    {"detail": "Section ID is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate section_id is a valid UUID
            try:
                if isinstance(section_id, str):
                    uuid_module.UUID(section_id)
            except ValueError:
                return Response(
                    {"detail": "Invalid section_id format. Must be a valid UUID."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            content_file = request.FILES.get('file')
            if not content_file:
                return Response(
                    {"detail": "Lecture content file is required."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in content_file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            section = get_object_or_404(Section, id=section_id)

            lecture = serializer.save(
                section=section,
                content_url=''  # will be updated by background task
            )

            upload_video_task.delay(
                lecture_id=lecture.id,
                local_path=temp_path,
                title=lecture.title
            )

            return Response(
                LectureDetailSerializer(lecture, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            # Clean up temp file on error
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Log and return full traceback for debugging
            error_traceback = traceback.format_exc()
            logger.error(f"Error in POST lecture endpoint: {error_traceback}")
            return Response(
                {
                    "detail": "Internal server error",
                    "error": str(e),
                    "traceback": error_traceback
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['Lectures'],
        operation_id='lectures_list',
        parameters=[
            OpenApiParameter(
                name='section_id',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.UUID,
                required=False,
                description='Filter lectures by Section ID'
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """List lectures with optional section filtering"""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['Lectures'], operation_id='lectures_retrieve')
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single lecture"""
        
        enrollment_exists = Enrollment.objects.filter(
            user=request.user,
            course__sections__lectures__id=kwargs['pk'],
            is_active=True
        ).exists()
        if not enrollment_exists and not request.user.is_superuser:
            raise PermissionDenied("You must be enrolled in the course to access this lecture.")
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=['Lectures'],
        operation_id='lectures_update',
        description="Update an existing lecture (superuser only). Sends JSON data only (no file upload). Use POST to upload files.",
    )
    def update(self, request, *args, **kwargs):
        """Update an existing lecture (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update lectures.")
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=['Lectures'],
        operation_id='lectures_partial_update',
        description="Partially update a lecture (superuser only). Sends JSON data only (no file upload). Use POST to upload files.",
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a lecture (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update lectures.")
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=['Lectures'], operation_id='lectures_destroy')
    def destroy(self, request, *args, **kwargs):
        """Delete an existing lecture (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can delete lectures.")
        
        lecture = self.get_object()
        delete_video_task.delay(lecture.content_url)
        return super().destroy(request, *args, **kwargs)
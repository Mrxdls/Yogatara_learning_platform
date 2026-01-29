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

from ..models import Category
from ..serializers import CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for managing categories.
    Supports:
    - POST /categories/ - Create category (superuser only)
    - GET /categories/ - List all categories
    - GET /categories/{id}/ - Get single category
    - PUT/PATCH /categories/{id}/ - Update category (superuser only)
    - DELETE /categories/{id}/ - Delete category (superuser only)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=['Categories'],
        operation_id='categories_create',
        description="Create a new category (superuser only)",
    )
    def create(self, request, *args, **kwargs):
        """Create a new category (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can create categories.")
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=['Categories'],
        operation_id='categories_list',
        description="List all categories",
    )
    def list(self, request, *args, **kwargs):
        """Fetch all categories"""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['Categories'], operation_id='categories_retrieve')
    def retrieve(self, request, *args, **kwargs):
        """Get a single category"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=['Categories'],
        operation_id='categories_update',
        description="Update an existing category (superuser only)",
    )
    def update(self, request, *args, **kwargs):
        """Update an existing category (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update categories.")
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=['Categories'],
        operation_id='categories_partial_update',
        description="Partially update an existing category (superuser only)",
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a category (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update categories.")
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=['Categories'],
        operation_id='categories_destroy',
        description="Delete an existing category (superuser only)",
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an existing category (superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can delete categories.")
        return super().destroy(request, *args, **kwargs)

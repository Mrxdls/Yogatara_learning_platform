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

from ..models import CoursePricing
from ..serializers import CoursePricingSerializer


class CoursePricingCreateView(APIView):
    """
    API view for creating course pricing.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        description="Create pricing for a course (superuser only)",
        request=CoursePricingSerializer,
        responses={201: CoursePricingSerializer},
    )
    def post(self, request):
        """Create pricing for a course"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can create course pricing.")

        serializer = CoursePricingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class CoursePricingDetailView(APIView):
    """
    API view for get, update, delete course pricing by course_id.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        description="Get pricing for a course",
        responses={200: CoursePricingSerializer},
    )
    def get(self, request, course_id):
        """Get pricing for a course"""
        try:
            pricing = CoursePricing.objects.get(course_id=course_id)
            serializer = CoursePricingSerializer(pricing)
            return Response(serializer.data, status=200)
        except CoursePricing.DoesNotExist:
            return Response({"detail": "Pricing not found for this course."}, status=404)

    @extend_schema(
        tags=['Course Pricing'],        description="Update course pricing (superuser only)",
        request=CoursePricingSerializer,
        responses={200: CoursePricingSerializer},
    )
    def put(self, request, course_id):
        """Update pricing for a course"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update course pricing.")

        try:
            pricing = CoursePricing.objects.get(course_id=course_id)
        except CoursePricing.DoesNotExist:
            return Response({"detail": "Pricing not found for this course."}, status=404)

        serializer = CoursePricingSerializer(pricing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)

    @extend_schema(
        description="Delete pricing for a course (superuser only)",
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}},
    )
    def delete(self, request, course_id):
        """Delete pricing for a course"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can delete course pricing.")

        try:
            pricing = CoursePricing.objects.get(course_id=course_id)
        except CoursePricing.DoesNotExist:
            return Response({"detail": "Pricing not found for this course."}, status=404)

        pricing.delete()
        return Response({"detail": "Pricing deleted successfully."}, status=200)


class CoursePricingViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for managing course pricing.
    Supports:
    - POST /pricing/ - Create pricing (superuser only)
    - GET /pricing/ - List all pricing
    - GET /pricing/{id}/ - Get single pricing
    - PUT/PATCH /pricing/{id}/ - Update pricing (superuser only)
    - DELETE /pricing/{id}/ - Delete pricing (superuser only)
    """
    queryset = CoursePricing.objects.all()
    serializer_class = CoursePricingSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter pricing by course_id if provided"""
        queryset = CoursePricing.objects.all()
        course_id = self.request.query_params.get('course_id') or self.kwargs.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    @extend_schema(
        tags=['Course Pricing'],
        operation_id='pricing_create',
        description="Create pricing for a course (superuser only)",
    )
    def create(self, request, *args, **kwargs):
        """Create pricing for a course"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can create course pricing.")
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=['Course Pricing'],
        operation_id='pricing_list',
        parameters=[
            OpenApiParameter(
                name='course_id',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.UUID,
                required=False,
                description='Filter pricing by Course ID'
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """List all pricing"""
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['Course Pricing'], operation_id='pricing_retrieve')
    def retrieve(self, request, *args, **kwargs):
        """Get pricing for a course"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=['Course Pricing'],
        operation_id='pricing_update',
        description="Update course pricing (superuser only)",
    )
    def update(self, request, *args, **kwargs):
        """Update pricing for a course"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update course pricing.")
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=['Course Pricing'],
        operation_id='pricing_partial_update',
        description="Partially update course pricing (superuser only)",
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update pricing for a course"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update course pricing.")
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=['Course Pricing'],
        operation_id='pricing_destroy',
        description="Delete pricing for a course (superuser only)",
    )
    def destroy(self, request, *args, **kwargs):
        """Delete pricing for a course"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can delete course pricing.")
        return super().destroy(request, *args, **kwargs)







from rest_framework import mixins
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

from ..models import Coupon

from ..serializers import CouponSerializer, CouponCourseSerializer

class CouponViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet for managing coupons.
    Supports:
    - POST /coupons/ - Create coupon (superuser only)
    - GET /coupons/ - List all coupons
    - GET /coupons/{id}/ - Get single coupon
    - PUT/PATCH /coupons/{id}/ - Update coupon (superuser only)
    - DELETE /coupons/{id}/ - Delete coupon (superuser only)
    """
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @extend_schema(
        tags=['Coupons'],
        operation_id='coupons_create',
        description="Create a new coupon (superuser only)",
    )
    def create(self, request, *args, **kwargs):
        """Create a new coupon (superuser only)"""
        try:
            if not request.user.is_superuser:
                raise PermissionDenied("Only superusers can create coupons.")
            return super().create(request, *args, **kwargs)
        except PermissionDenied:
            raise
        except Exception as e:
            print(f"Error in coupon create: {str(e)}")
            traceback.print_exc()
            return Response(
                {"error": "Failed to create coupon", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['Coupons'],
        operation_id='coupons_list',
        description="List all coupons",
    )
    def list(self, request, *args, **kwargs):
        """Fetch all coupons"""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            print(f"Error in coupon list: {str(e)}")
            traceback.print_exc()
            return Response(
                {"error": "Failed to fetch coupons", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(tags=['Coupons'], operation_id='coupons_retrieve')
    def retrieve(self, request, *args, **kwargs):
        """Get a single coupon"""
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            print(f"Error in coupon retrieve: {str(e)}")
            traceback.print_exc()
            return Response(
                {"error": "Failed to fetch coupon", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['Coupons'],
        operation_id='coupons_update',
        description="Update an existing coupon (superuser only)",
    )
    def update(self, request, *args, **kwargs):
        """Update an existing coupon (superuser only)"""
        try:
            if not request.user.is_superuser:
                raise PermissionDenied("Only superusers can update coupons.")
            # only active coupons can be updated
            coupon = self.get_object()
            if not coupon.is_active:
                return Response(
                    {"error": "Only active coupons can be updated."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return super().update(request, *args, **kwargs)
        except PermissionDenied:
            raise
        except Exception as e:
            print(f"Error in coupon update: {str(e)}")
            traceback.print_exc()
            return Response(
                {"error": "Failed to update coupon", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['Coupons'],
        operation_id='coupons_delete',
        description="Delete an existing coupon (superuser only)",
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an existing coupon (superuser only)"""
        try:
            if not request.user.is_superuser:
                raise PermissionDenied("Only superusers can delete coupons.")
            coupon = self.get_object()
            coupon.is_active = False
            coupon.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied:
            raise
        except Exception as e:
            print(f"Error in coupon delete: {str(e)}")
            traceback.print_exc()
            return Response(
                {"error": "Failed to delete coupon", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
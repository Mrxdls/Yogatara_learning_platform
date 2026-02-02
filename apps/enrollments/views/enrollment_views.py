from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from ..serializers import (
    EnrollmentInitSerializer,
    EnrollmentListSerializer,
    EnrollmentDetailSerializer,
)
from ..models import Enrollment


class EnrollmentInitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # get serializer function that decide which serializer use in which request 

    

    @extend_schema(
        tags=['Enrollments'],
        request=EnrollmentInitSerializer,
        responses={
            201: {
                'description': 'Enrollment initialized successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'course_id': 'uuid-string',
                            'coupon_code': 'DISCOUNT50'}}}}})
    def post(self, request):
        serializer = EnrollmentInitSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        enrollment = serializer.save()

        return Response(
            {
                "enrollment_id": enrollment.id,
                "base_amount": enrollment.base_amount,
                "discount_amount": enrollment.discount_amount,
                "gst_amount": enrollment.gst_amount,
                "final_amount": enrollment.final_amount,
                "expires_at": enrollment.expires_at,
                "payment_status": enrollment.payment_status,
            },
            status=status.HTTP_201_CREATED
        )

    def get(self, request, id=None):
        if id:
            # Detail view
            enrollment = Enrollment.objects.get(id=id, user=request.user)
            serializer = EnrollmentDetailSerializer(enrollment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Get user's enrollments
        enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
        serializer = EnrollmentListSerializer(enrollments, many=True)
        
        return Response(
            {
                "count": enrollments.count(),
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )
    

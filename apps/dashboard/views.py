from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import (
    StudentDashboardSerializer,
    AdminMetricsSerializer,
    AdminDashboardSerializer,
    AdminCourseMetricsSerializer,
    AdminUserMetricsSerializer,
    AdminEnrollmentMetricsSerializer,
)
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from django.contrib.auth import get_user_model

User = get_user_model()


class StudentDashboardView(APIView):
    """
    Student Dashboard API - returns learning statistics for authenticated user.
    Shows enrolled courses, completed courses, lectures watched, average quiz score, and learning hours.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Dashboard'],
        responses={200: StudentDashboardSerializer},
        description="Get student dashboard statistics including enrollments, progress, and average scores"
    )
    def get(self, request):
        """
        Get dashboard statistics for the authenticated student.
        Requires authentication.
        """
        serializer = StudentDashboardSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ========================= ADMIN DASHBOARD VIEWS =========================


class AdminMetricsView(APIView):
    """
    Admin Metrics API endpoint for platform-wide statistics.
    Returns key performance indicators and metrics for the entire platform.
    
    Metrics include:
    - User statistics (total, active, new)
    - Course statistics (published, draft, archived)
    - Enrollment data (active, completed, pending)
    - Revenue metrics (total, this month, this week)
    - Engagement metrics (completion rate, rating, learning hours)
    - Assignment metrics (total, submissions, average score)
    - Content metrics (lectures, videos, sections)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Admin Dashboard'],
        responses={200: AdminMetricsSerializer},
        description="Get comprehensive platform metrics including user, course, and revenue statistics"
    )
    def get(self, request):
        """
        Get all platform metrics.
        Only accessible to admin users.
        """
        serializer = AdminMetricsSerializer()
        metrics = serializer.to_representation(None)
        return Response(metrics, status=status.HTTP_200_OK)


class AdminDashboardView(APIView):
    """
    Admin Dashboard API endpoint for comprehensive platform overview.
    Returns a complete dashboard with metrics, top performers, recent activity, and trends.
    
    Includes:
    - Platform metrics (26 KPIs)
    - Top 5 courses by enrollment
    - Top 5 users by learning hours
    - Recent 10 enrollments
    - 7-day revenue trend
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=['Admin Dashboard'],
        responses={200: AdminDashboardSerializer},
        description="Get comprehensive admin dashboard with metrics, top performers, and trends"
    )
    def get(self, request):
        """
        Get complete admin dashboard with all metrics and trends.
        Only accessible to admin users.
        """
        serializer = AdminDashboardSerializer()
        dashboard = serializer.to_representation(None)
        return Response(dashboard, status=status.HTTP_200_OK)


class AdminCourseMetricsView(APIView):
    """
    Admin Course Metrics API endpoint for course-level analytics.
    Returns detailed metrics for a specific course including enrollments,
    revenue, performance, and engagement data.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=['Admin Dashboard'],
        responses={200: AdminCourseMetricsSerializer},
        description="Get detailed metrics for a specific course including enrollments, revenue, and performance"
    )
    def get(self, request, course_id):
        """
        Get metrics for a specific course.
        Only accessible to admin users.
        
        Args:
            course_id: UUID of the course
        """
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminCourseMetricsSerializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserMetricsView(APIView):
    """
    Admin User Metrics API endpoint for user-level analytics.
    Returns detailed metrics for a specific user including enrollments,
    progress, assessments, and spending data.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=['Admin Dashboard'],
        responses={200: AdminUserMetricsSerializer},
        description="Get detailed metrics for a specific user including enrollments, progress, and spending"
    )
    def get(self, request, user_id):
        """
        Get metrics for a specific user.
        Only accessible to admin users.
        
        Args:
            user_id: UUID of the user
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminUserMetricsSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminEnrollmentMetricsView(APIView):
    """
    Admin Enrollment Metrics API endpoint for enrollment-level analytics.
    Returns detailed metrics for a specific enrollment including payment status,
    progress, engagement, and assignment data.
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=['Admin Dashboard'],
        responses={200: AdminEnrollmentMetricsSerializer},
        description="Get detailed metrics for a specific enrollment including payment and progress"
    )
    def get(self, request, enrollment_id):
        """
        Get metrics for a specific enrollment.
        Only accessible to admin users.
        
        Args:
            enrollment_id: UUID of the enrollment
        """
        try:
            enrollment = Enrollment.objects.select_related(
                'user', 'course'
            ).get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminEnrollmentMetricsSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_200_OK)

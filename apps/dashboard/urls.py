from django.urls import path
from .views import (
    StudentDashboardView,
    AdminMetricsView,
    AdminDashboardView,
    AdminCourseMetricsView,
    AdminUserMetricsView,
    AdminEnrollmentMetricsView,
)

urlpatterns = [
    # Student Dashboard
    path('student/', StudentDashboardView.as_view(), name='student_dashboard'),
    
    # Admin Dashboard
    path('admin/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/metrics/', AdminMetricsView.as_view(), name='admin_metrics'),
    path('admin/course/<uuid:course_id>/metrics/', AdminCourseMetricsView.as_view(), name='admin_course_metrics'),
    path('admin/user/<uuid:user_id>/metrics/', AdminUserMetricsView.as_view(), name='admin_user_metrics'),
    path('admin/enrollment/<uuid:enrollment_id>/metrics/', AdminEnrollmentMetricsView.as_view(), name='admin_enrollment_metrics'),
]

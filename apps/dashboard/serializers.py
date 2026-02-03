from rest_framework import serializers
from django.db.models import Count, Avg, Q, F, Sum, Max, Min, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

from apps.assignments.models import Assignment, Question, AssignmentSubmission, QuestionAttempt
from apps.enrollments.models import Enrollment, LectureProgress
from apps.courses.models import Lecture, Section, Course, Instructor
from apps.users.models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()


class CurrentLectureSerializer(serializers.Serializer):
    """Serializer for current lecture details"""
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    content_url = serializers.CharField()
    order_index = serializers.IntegerField()
    section_id = serializers.UUIDField()
    section_title = serializers.CharField()
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class CurrentSectionSerializer(serializers.Serializer):
    """Serializer for current section details"""
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    order_index = serializers.IntegerField()
    course_id = serializers.UUIDField()
    total_lectures = serializers.IntegerField()
    completed_lectures = serializers.IntegerField()


class SectionAssignmentSerializer(serializers.Serializer):
    """Serializer for assignment details in a section"""
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()
    assignment_type = serializers.CharField()
    max_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    is_published = serializers.BooleanField()
    user_submission_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    user_submission_status = serializers.CharField(allow_null=True)


class StudentDashboardSerializer(serializers.Serializer):
    """
    Serializer for student dashboard statistics.
    Calculates key metrics about a student's learning progress including
    enrollments, quiz scores, learning hours, and current learning context.
    """
    enrolled_courses = serializers.IntegerField(read_only=True)
    completed_courses = serializers.IntegerField(read_only=True)
    total_lectures_watched = serializers.IntegerField(read_only=True)
    average_quiz_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    learning_hours = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    current_lecture = CurrentLectureSerializer(read_only=True)
    current_section = CurrentSectionSerializer(read_only=True)
    current_section_assignment = SectionAssignmentSerializer(read_only=True, allow_null=True)

    def get_enrolled_courses(self, user):
        """Get count of enrolled courses for the user"""
        return Enrollment.objects.filter(
            user=user,
            is_active=True
        ).values('course').distinct().count()

    def get_completed_courses(self, user):
        """Get count of completed courses for the user"""
        return Enrollment.objects.filter(
            user=user,
            is_completed=True
        ).count()

    def get_total_lectures_watched(self, user):
        """Get count of lectures marked as completed by the user"""
        return LectureProgress.objects.filter(
            enrollment__user=user,
            is_completed=True
        ).count()

    def get_average_quiz_score(self, user):
        """Get average score of all assignment submissions for the user"""
        avg_score = AssignmentSubmission.objects.filter(
            enrollment__user=user,
            score__isnull=False
        ).aggregate(
            avg=Avg('score')
        )['avg']
        
        # Return 0.00 if no submissions, otherwise return the average
        return avg_score if avg_score is not None else 0.00

    def get_learning_hours(self, user):
        """
        Calculate total learning hours by summing lecture progress.
        Assumes learning_hours = (watched_seconds / 3600) per lecture
        """
        # Get all lecture progress for the user and sum watched_seconds
        total_seconds = LectureProgress.objects.filter(
            enrollment__user=user
        ).aggregate(
            total=Coalesce(Sum('watched_seconds'), 0)
        )['total']
        
        # Convert seconds to hours (rounded to 2 decimal places)
        learning_hours = round(total_seconds / 3600, 2)
        return learning_hours

    def get_current_lecture(self, user):
        """
        Get the most recently accessed lecture for the user.
        Returns detailed information about the current lecture.
        """
        try:
            # Get the most recently accessed lecture
            latest_progress = LectureProgress.objects.filter(
                enrollment__user=user
            ).select_related('lecture__section').order_by('-last_watched_at').first()
            
            if not latest_progress:
                return None
            
            lecture = latest_progress.lecture
            return {
                'id': lecture.id,
                'title': lecture.title,
                'description': lecture.description,
                'content_url': lecture.content_url,
                'order_index': lecture.order_index,
                'section_id': lecture.section.id,
                'section_title': lecture.section.title,
                'completion_percentage': latest_progress.completion_percentage,
            }
        except Exception:
            return None

    def get_current_section(self, user):
        """
        Get the section of the most recently accessed lecture.
        Returns count of total and completed lectures in this section.
        """
        try:
            # Get the most recently accessed lecture
            latest_progress = LectureProgress.objects.filter(
                enrollment__user=user
            ).select_related('lecture__section').order_by('-last_watched_at').first()
            
            if not latest_progress:
                return None
            
            section = latest_progress.lecture.section
            
            # Count total and completed lectures in this section
            total_lectures = Lecture.objects.filter(
                section=section,
                is_published=True
            ).count()
            
            completed_lectures = LectureProgress.objects.filter(
                enrollment__user=user,
                lecture__section=section,
                is_completed=True
            ).count()
            
            return {
                'id': section.id,
                'title': section.title,
                'description': section.description,
                'order_index': section.order_index,
                'course_id': section.course.id,
                'total_lectures': total_lectures,
                'completed_lectures': completed_lectures,
            }
        except Exception:
            return None

    def get_current_section_assignment(self, user):
        """
        Get the assignment associated with the current section.
        Returns assignment details and user's submission score if available.
        """
        try:
            # Get the most recently accessed lecture
            latest_progress = LectureProgress.objects.filter(
                enrollment__user=user
            ).select_related('lecture__section').order_by('-last_watched_at').first()
            
            if not latest_progress:
                return None
            
            section = latest_progress.lecture.section
            
            # Get the assignment for this section
            assignment = Assignment.objects.filter(section=section).first()
            
            if not assignment:
                return None
            
            # Get user's submission for this assignment
            enrollment = latest_progress.enrollment
            submission = AssignmentSubmission.objects.filter(
                enrollment=enrollment,
                assignment=assignment
            ).first()
            
            return {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'assignment_type': assignment.assignment_type,
                'max_score': assignment.max_score,
                'is_published': assignment.is_published,
                'user_submission_score': submission.score if submission else None,
                'user_submission_status': submission.status if submission else None,
            }
        except Exception:
            return None

    def to_representation(self, obj):
        """
        obj is the User instance
        Calculate all fields based on the user's data
        """
        user = obj
        return {
            'enrolled_courses': self.get_enrolled_courses(user),
            'completed_courses': self.get_completed_courses(user),
            'total_lectures_watched': self.get_total_lectures_watched(user),
            'average_quiz_score': self.get_average_quiz_score(user),
            'learning_hours': self.get_learning_hours(user),
            'current_lecture': self.get_current_lecture(user),
            'current_section': self.get_current_section(user),
            'current_section_assignment': self.get_current_section_assignment(user),
        }


# ========================= ADMIN PANEL SERIALIZERS =========================


class AdminMetricsSerializer(serializers.Serializer):
    """
    Core metrics serializer for admin dashboard.
    Provides platform-wide statistics and key performance indicators.
    """
    # User Metrics
    total_users = serializers.IntegerField(read_only=True)
    active_users = serializers.IntegerField(read_only=True)
    new_users_this_month = serializers.IntegerField(read_only=True)
    new_users_this_week = serializers.IntegerField(read_only=True)
    
    # Course Metrics
    total_courses = serializers.IntegerField(read_only=True)
    published_courses = serializers.IntegerField(read_only=True)
    draft_courses = serializers.IntegerField(read_only=True)
    archived_courses = serializers.IntegerField(read_only=True)
    
    # Enrollment Metrics
    total_enrollments = serializers.IntegerField(read_only=True)
    active_enrollments = serializers.IntegerField(read_only=True)
    completed_enrollments = serializers.IntegerField(read_only=True)
    pending_payments = serializers.IntegerField(read_only=True)
    
    # Revenue Metrics
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    revenue_this_month = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    revenue_this_week = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    # Engagement Metrics
    average_course_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    # average_course_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)  # TODO: Rating system not implemented yet
    average_learning_hours_per_user = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    
    # Assignment/Quiz Metrics
    total_assignments = serializers.IntegerField(read_only=True)
    total_submissions = serializers.IntegerField(read_only=True)
    average_assignment_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    # Content Metrics
    total_lectures = serializers.IntegerField(read_only=True)
    total_videos = serializers.IntegerField(read_only=True)
    total_sections = serializers.IntegerField(read_only=True)
    
    def get_total_users(self):
        """Get total number of users in the system"""
        return User.objects.count()
    
    def get_active_users(self):
        """Get users with at least one active enrollment"""
        return User.objects.filter(enrollments__is_active=True).distinct().count()
    
    def get_new_users_this_month(self):
        """Get users created in the current month"""
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return User.objects.filter(created_at__gte=month_start).count()
    
    def get_new_users_this_week(self):
        """Get users created in the current week"""
        week_start = timezone.now() - timedelta(days=7)
        return User.objects.filter(created_at__gte=week_start).count()
    
    def get_total_courses(self):
        """Get total number of courses"""
        return Course.objects.count()
    
    def get_published_courses(self):
        """Get count of published courses"""
        return Course.objects.filter(status='published').count()
    
    def get_draft_courses(self):
        """Get count of draft courses"""
        return Course.objects.filter(status='draft').count()
    
    def get_archived_courses(self):
        """Get count of archived courses"""
        return Course.objects.filter(status='archived').count()
    
    def get_total_enrollments(self):
        """Get total number of enrollments"""
        return Enrollment.objects.count()
    
    def get_active_enrollments(self):
        """Get number of active enrollments"""
        return Enrollment.objects.filter(is_active=True).count()
    
    def get_completed_enrollments(self):
        """Get number of completed enrollments"""
        return Enrollment.objects.filter(is_completed=True).count()
    
    def get_pending_payments(self):
        """Get enrollments with pending payment status"""
        return Enrollment.objects.filter(payment_status='pending').count()
    
    def get_total_revenue(self):
        """Get total revenue from all paid enrollments"""
        revenue = Enrollment.objects.filter(
            payment_status='paid'
        ).aggregate(
            total=Coalesce(Sum('final_amount', output_field=DecimalField()), 0, output_field=DecimalField())
        )['total']
        return revenue
    
    def get_revenue_this_month(self):
        """Get revenue for the current month"""
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue = Enrollment.objects.filter(
            payment_status='paid',
            created_at__gte=month_start
        ).aggregate(
            total=Coalesce(Sum('final_amount', output_field=DecimalField()), 0, output_field=DecimalField())
        )['total']
        return revenue
    
    def get_revenue_this_week(self):
        """Get revenue for the current week"""
        week_start = timezone.now() - timedelta(days=7)
        revenue = Enrollment.objects.filter(
            payment_status='paid',
            created_at__gte=week_start
        ).aggregate(
            total=Coalesce(Sum('final_amount', output_field=DecimalField()), 0, output_field=DecimalField())
        )['total']
        return revenue
    
    def get_average_course_completion_rate(self):
        """Get average completion rate across all courses"""
        rate = Course.objects.annotate(
            completion_rate=Coalesce(
                Avg('enrollments__progress_percentage'),
                0,
                output_field=DecimalField()
            )
        ).aggregate(
            avg_rate=Avg('completion_rate')
        )['avg_rate']
        return round(rate, 2) if rate else 0.00
    
    def get_average_course_rating(self):
        """Get average rating across all courses"""
        # TODO: Implement rating system
        # Course model doesn't have avg_rating field yet
        return 0.00
    
    def get_average_learning_hours_per_user(self):
        """Get average learning hours per active user"""
        total_hours = LectureProgress.objects.aggregate(
            total=Coalesce(Sum('watched_seconds'), 0)
        )['total']
        
        active_users = self.get_active_users()
        if active_users == 0:
            return 0.00
        
        avg_hours = (total_hours / 3600) / active_users
        return round(avg_hours, 2)
    
    def get_total_assignments(self):
        """Get total number of assignments"""
        return Assignment.objects.count()
    
    def get_total_submissions(self):
        """Get total number of assignment submissions"""
        return AssignmentSubmission.objects.count()
    
    def get_average_assignment_score(self):
        """Get average score across all assignment submissions"""
        avg_score = AssignmentSubmission.objects.filter(
            score__isnull=False
        ).aggregate(
            avg=Avg('score')
        )['avg']
        return round(avg_score, 2) if avg_score else 0.00
    
    def get_total_lectures(self):
        """Get total number of lectures"""
        return Lecture.objects.count()
    
    def get_total_videos(self):
        """Get total number of videos"""
        return Lecture.objects.filter(content_type='video').count()
    
    def get_total_sections(self):
        """Get total number of sections"""
        return Section.objects.count()
    
    def to_representation(self, obj):
        """
        Calculate all metrics and return as dictionary
        obj is not used but kept for consistency with DRF patterns
        """
        return {
            'total_users': self.get_total_users(),
            'active_users': self.get_active_users(),
            'new_users_this_month': self.get_new_users_this_month(),
            'new_users_this_week': self.get_new_users_this_week(),
            'total_courses': self.get_total_courses(),
            'published_courses': self.get_published_courses(),
            'draft_courses': self.get_draft_courses(),
            'archived_courses': self.get_archived_courses(),
            'total_enrollments': self.get_total_enrollments(),
            'active_enrollments': self.get_active_enrollments(),
            'completed_enrollments': self.get_completed_enrollments(),
            'pending_payments': self.get_pending_payments(),
            'total_revenue': self.get_total_revenue(),
            'revenue_this_month': self.get_revenue_this_month(),
            'revenue_this_week': self.get_revenue_this_week(),
            'average_course_completion_rate': self.get_average_course_completion_rate(),
            # 'average_course_rating': self.get_average_course_rating(),  # TODO: Rating system not implemented yet
            'average_learning_hours_per_user': self.get_average_learning_hours_per_user(),
            'total_assignments': self.get_total_assignments(),
            'total_submissions': self.get_total_submissions(),
            'average_assignment_score': self.get_average_assignment_score(),
            'total_lectures': self.get_total_lectures(),
            'total_videos': self.get_total_videos(),
            'total_sections': self.get_total_sections(),
        }


class AdminCourseMetricsSerializer(serializers.Serializer):
    """
    Detailed metrics for individual courses in admin panel.
    Calculates all metrics from Course instance.
    """
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    course_code = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    level = serializers.CharField(read_only=True)
    
    # Enrollment metrics
    total_enrollments = serializers.IntegerField(read_only=True)
    active_enrollments = serializers.IntegerField(read_only=True)
    completed_enrollments = serializers.IntegerField(read_only=True)
    
    # Revenue metrics
    total_course_revenue = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    # Performance metrics
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    # average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)  # TODO: Rating system not implemented yet
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    # Content metrics
    total_sections = serializers.IntegerField(read_only=True)
    total_lectures = serializers.IntegerField(read_only=True)
    total_assignments = serializers.IntegerField(read_only=True)
    
    # Engagement
    total_learning_hours = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    average_learning_hours_per_user = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    
    def to_representation(self, obj):
        """Calculate all metrics from course instance"""
        course = obj
        return {
            'id': course.id,
            'title': course.title,
            'course_code': course.course_code,
            'status': course.status,
            'level': course.level,
            'total_enrollments': course.enrollments.count(),
            'active_enrollments': course.enrollments.filter(is_active=True).count(),
            'completed_enrollments': course.enrollments.filter(is_completed=True).count(),
            'total_course_revenue': course.enrollments.filter(
                payment_status='paid'
            ).aggregate(total=Coalesce(Sum('final_amount', output_field=DecimalField()), 0, output_field=DecimalField()))['total'],
            'average_price': course.enrollments.filter(
                final_amount__gt=0
            ).aggregate(avg=Coalesce(Avg('final_amount'), 0, output_field=DecimalField()))['avg'],
            'completion_rate': course.enrollments.aggregate(
                rate=Avg('progress_percentage')
            )['rate'] or 0,
            # 'average_rating': getattr(course, 'avg_rating', 0.00),  # TODO: Rating system not implemented yet
            'average_score': 0,
            'total_sections': course.sections.count(),
            'total_lectures': sum(s.lectures.count() for s in course.sections.all()),
            'total_assignments': 0,
            'total_learning_hours': 0,
            'average_learning_hours_per_user': 0,
        }


class AdminUserMetricsSerializer(serializers.Serializer):
    """
    Detailed metrics for individual users in admin panel.
    Calculates all metrics from User instance.
    """
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    
    # Enrollment stats
    total_enrollments = serializers.IntegerField(read_only=True)
    completed_enrollments = serializers.IntegerField(read_only=True)
    active_enrollments = serializers.IntegerField(read_only=True)
    
    # Progress metrics
    average_completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_learning_hours = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_lectures_watched = serializers.IntegerField(read_only=True)
    
    # Assessment metrics
    average_quiz_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_submissions = serializers.IntegerField(read_only=True)
    
    # Account info
    join_date = serializers.DateTimeField(read_only=True)
    last_active = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    # Spending
    total_spent = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    def to_representation(self, obj):
        """Calculate all metrics from user instance"""
        user = obj
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'total_enrollments': user.enrollments.count(),
            'completed_enrollments': user.enrollments.filter(is_completed=True).count(),
            'active_enrollments': user.enrollments.filter(is_active=True).count(),
            'average_completion_rate': user.enrollments.aggregate(
                rate=Avg('progress_percentage')
            )['rate'] or 0,
            'total_learning_hours': 0,
            'total_lectures_watched': 0,
            'average_quiz_score': 0,
            'total_submissions': 0,
            'join_date': user.created_at,
            'last_active': user.last_login,
            'is_active': user.is_active,
            'total_spent': user.enrollments.filter(
                payment_status='paid'
            ).aggregate(total=Coalesce(Sum('final_amount', output_field=DecimalField()), 0, output_field=DecimalField()))['total'],
        }


class AdminEnrollmentMetricsSerializer(serializers.Serializer):
    """
    Detailed metrics for individual enrollments in admin panel.
    Calculates all metrics from Enrollment instance.
    """
    id = serializers.UUIDField(read_only=True)
    user_email = serializers.CharField(read_only=True)
    course_title = serializers.CharField(read_only=True)
    
    # Payment info
    base_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    final_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status = serializers.CharField(read_only=True)
    
    # Enrollment status
    is_active = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    # Engagement
    last_accessed_at = serializers.DateTimeField(read_only=True)
    lectures_watched = serializers.IntegerField(read_only=True)
    learning_hours = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    
    # Assignments
    assignments_submitted = serializers.IntegerField(read_only=True)
    average_assignment_score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    # Certificates
    certificate_issued = serializers.BooleanField(read_only=True)
    
    # Timeline
    enrolled_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    expires_at = serializers.DateTimeField(read_only=True, allow_null=True)
    
    def to_representation(self, obj):
        """Calculate all metrics from enrollment instance"""
        enrollment = obj
        return {
            'id': enrollment.id,
            'user_email': enrollment.user.email,
            'course_title': enrollment.course.title,
            'base_amount': enrollment.base_amount,
            'discount_amount': enrollment.discount_amount,
            'final_amount': enrollment.final_amount,
            'payment_status': enrollment.payment_status,
            'is_active': enrollment.is_active,
            'is_completed': enrollment.is_completed,
            'progress_percentage': enrollment.progress_percentage,
            'last_accessed_at': enrollment.last_accessed_at,
            'lectures_watched': 0,
            'learning_hours': 0,
            'assignments_submitted': 0,
            'average_assignment_score': 0,
            'certificate_issued': enrollment.certificate_issued,
            'enrolled_at': enrollment.created_at,
            'completed_at': enrollment.completion_date,
            'expires_at': enrollment.expires_at,
        }


class AdminDashboardSerializer(serializers.Serializer):
    """
    Main admin dashboard serializer combining all metrics.
    Provides a comprehensive overview of the platform.
    """
    metrics = AdminMetricsSerializer(read_only=True)
    top_courses = serializers.SerializerMethodField()
    top_users = serializers.SerializerMethodField()
    recent_enrollments = serializers.SerializerMethodField()
    revenue_trend = serializers.SerializerMethodField()
    
    def get_top_courses(self, obj):
        """Get top 5 courses by enrollment count"""
        top_courses = Course.objects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:5]
        
        return [{
            'id': course.id,
            'title': course.title,
            'enrollment_count': course.enrollment_count,
            'completion_rate': course.enrollments.aggregate(
                rate=Avg('progress_percentage')
            )['rate'] or 0,
            'revenue': course.enrollments.filter(
                payment_status='paid'
            ).aggregate(
                total=Coalesce(Sum('final_amount', output_field=DecimalField()), 0, output_field=DecimalField())
            )['total']
        } for course in top_courses]
    
    def get_top_users(self, obj):
        """Get top 5 users by learning hours"""
        top_users = User.objects.annotate(
            total_hours=Coalesce(
                Sum('enrollments__lectureprogress__watched_seconds', output_field=DecimalField()) / 3600,
                0,
                output_field=DecimalField()
            ),
            enrollments_count=Count('enrollments')
        ).order_by('-total_hours')[:5]
        
        return [{
            'id': user.id,
            'email': user.email,
            'learning_hours': round(user.total_hours, 2),
            'enrollments_count': user.enrollments_count,
            'completion_rate': user.enrollments.aggregate(
                rate=Avg('progress_percentage')
            )['rate'] or 0,
        } for user in top_users]
    
    def get_recent_enrollments(self, obj):
        """Get 10 most recent enrollments"""
        recent = Enrollment.objects.select_related(
            'user', 'course'
        ).order_by('-created_at')[:10]
        
        return [{
            'id': enrollment.id,
            'user_email': enrollment.user.email,
            'course_title': enrollment.course.title,
            'payment_status': enrollment.payment_status,
            'progress_percentage': enrollment.progress_percentage,
            'enrolled_at': enrollment.created_at,
        } for enrollment in recent]
    
    def get_revenue_trend(self, obj):
        """Get revenue trend for the last 7 days"""
        today = timezone.now().date()
        trend_data = []
        
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            day_start = timezone.make_aware(
                timezone.datetime.combine(date, timezone.datetime.min.time())
            )
            day_end = timezone.make_aware(
                timezone.datetime.combine(date, timezone.datetime.max.time())
            )
            
            revenue = Enrollment.objects.filter(
                payment_status='paid',
                created_at__gte=day_start,
                created_at__lte=day_end
            ).aggregate(
                total=Coalesce(Sum('final_amount', output_field=DecimalField()), 0, output_field=DecimalField())
            )['total']
            
            trend_data.append({
                'date': date.isoformat(),
                'revenue': float(revenue)
            })
        
        return trend_data
    
    def to_representation(self, obj):
        """Return comprehensive admin dashboard data"""
        return {
            'metrics': AdminMetricsSerializer().to_representation(None),
            'top_courses': self.get_top_courses(obj),
            'top_users': self.get_top_users(obj),
            'recent_enrollments': self.get_recent_enrollments(obj),
            'revenue_trend': self.get_revenue_trend(obj),
        }
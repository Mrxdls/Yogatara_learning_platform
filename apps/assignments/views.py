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

from apps.assignments.models import Assignment, Question, AssignmentSubmission, QuestionAttempt
from apps.enrollments.models import Enrollment
from apps.assignments.serializers import (
    AssignmentSerializer,
    QuestionAttemptSerializer,
    QuestionAttemptRequestSerializer,
    AssignmentQuestionSerializer,
    AssignmentSubmissionSerializer
)


class AssignmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Assignments'],
        request=AssignmentSerializer,
        responses={
            201: AssignmentSerializer,
            400: 'Bad Request'
        }
    )
    def post(self, request):
        """Create a new assignment (Superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can create assignments.")

        serializer = AssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()

        return Response(AssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class AssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Assignments'],
        responses={
            200: AssignmentSerializer,
            404: 'Not Found'
        }
    )
    def get(self, request, assignment_id):
        """Retrieve assignment details (Students must be enrolled)"""
        assignment = get_object_or_404(Assignment, id=assignment_id)

        # Check if the user is enrolled in the course
        enrollment_exists = Enrollment.objects.filter(
            user=request.user,
            course=assignment.section.course,
            is_active=True
        ).exists()

        if not enrollment_exists and not request.user.is_instructor:
            raise PermissionDenied("You must be enrolled in the course to access this assignment.")

        serializer = AssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Assignments'],
        request=AssignmentSerializer,
        responses={
            200: AssignmentSerializer,
            404: 'Not Found'
        }
    )
    def put(self, request, assignment_id):
        """Update an existing assignment (Superuser only)"""
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can update assignments.")

        assignment = get_object_or_404(Assignment, id=assignment_id)

        serializer = AssignmentSerializer(assignment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()

        return Response(AssignmentSerializer(assignment).data, status=status.HTTP_200_OK)


class QuestionAttemptCreateView(APIView):
    """Create a question attempt (POST only)"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Assignments'],
        request=QuestionAttemptRequestSerializer,
        responses={
            201: inline_serializer(
                name='QuestionAttemptResponse',
                fields={
                    'attempt': QuestionAttemptSerializer(),
                    'next_question': AssignmentQuestionSerializer(allow_null=True),
                    'is_last_question': serializers.BooleanField(),
                }
            ),
            400: 'Bad Request'
        }
    )
    def post(self, request):
        """Submit an answer attempt for a question and get the next question"""
        serializer = QuestionAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question = serializer.validated_data['question']
        assignment = question.assignment
        
        # Get or validate enrollment
        enrollment = get_object_or_404(
            Enrollment,
            user=request.user,
            course=assignment.section.course,
            is_active=True
        )
        
        # Save the attempt with enrollment
        question_attempt = serializer.save(enrollment=enrollment)
        
        # Get the next question in the assignment based on order_index
        next_question = Question.objects.filter(
            assignment=assignment,
            order_index__gt=question.order_index
        ).order_by('order_index').first()
        if next_question is None:
            # All questions attempted, create/update assignment submission
            assignment_submission = AssignmentSubmission.objects.filter(
                enrollment=enrollment,
                assignment=assignment
            ).first()
            
            if assignment_submission:
                # Update existing submission
                submission_serializer = AssignmentSubmissionSerializer(
                    assignment_submission,
                    data={'status': AssignmentSubmission.Status.SUBMITTED},
                    partial=True
                )
            else:
                # Create new submission
                submission_serializer = AssignmentSubmissionSerializer(
                    data={
                        'enrollment': enrollment.id,
                        'assignment': assignment.id,
                        'status': AssignmentSubmission.Status.SUBMITTED
                    }
                )
            
            submission_serializer.is_valid(raise_exception=True)
            assignment_submission = submission_serializer.save()
        response_data = {
            'attempt': QuestionAttemptSerializer(question_attempt).data,
            'next_question': AssignmentQuestionSerializer(next_question).data if next_question else None,
            'is_last_question': next_question is None,
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class AssignmentNextQuestionView(APIView):
    """Get the next unanswered question for an assignment"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Assignments'],
        responses={
            200: AssignmentQuestionSerializer,
            404: 'Not Found'
        }
    )
    def get(self, request, assignment_id):
        """Get first unanswered question for a specific assignment"""
        # check user enrollment
        enrollment = get_object_or_404(
            Enrollment,
            user=request.user,
            course__sections__assignment__id=assignment_id,
            is_active=True
        )
        
        # Get questions already attempted by this user
        attempted_question_ids = QuestionAttempt.objects.filter(
            enrollment=enrollment,
            question__assignment__id=assignment_id
        ).values_list('question_id', flat=True)
        
        # Get first unanswered question
        next_question = Question.objects.filter(
            assignment__id=assignment_id
        ).exclude(
            id__in=attempted_question_ids
        ).order_by('order_index').first()
        
        if next_question is None:
            return Response({'message': 'All questions have been attempted'}, status=status.HTTP_200_OK)
        
        serializer = AssignmentQuestionSerializer(next_question)
        return Response(serializer.data, status=status.HTTP_200_OK)

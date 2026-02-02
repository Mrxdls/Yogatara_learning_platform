# generate url parttern for assignments app
from django.urls import path
from apps.assignments.views import (
    AssignmentCreateView,
    AssignmentDetailView,
    QuestionAttemptCreateView,
    AssignmentNextQuestionView
)

urlpatterns = [
    path('', AssignmentCreateView.as_view(), name='assignments_create'),
    path('<uuid:assignment_id>/', AssignmentDetailView.as_view(), name='assignments_detail'),
    path('questions/attempt/', QuestionAttemptCreateView.as_view(), name='question_attempt_create'),
    path('<uuid:assignment_id>/next-question/', AssignmentNextQuestionView.as_view(), name='assignment_next_question'),
]
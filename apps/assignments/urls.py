# generate url parttern for assignments app
from django.urls import path
from apps.assignments.views import AssignmentView, QuestionAttemptView

urlpatterns = [
    path('', AssignmentView.as_view(), name='assignments_create'),
    path('<uuid:assignment_id>/', AssignmentView.as_view(), name='assignments_detail'),
    path('questions/attempt/', QuestionAttemptView.as_view(), name='question_attempt'),
]
import uuid
from django.db import models
from django.conf import settings


class Assignment(models.Model):
    """
    Assignment model - course assignments.
    Maps to 'assignments' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    # Assignment details
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    
    # Files and resources
    attachment_url = models.CharField(max_length=500, blank=True)
    
    # Grading
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00
    )
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=60.00
    )
    
    # Deadlines
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Settings
    is_published = models.BooleanField(default=True)
    order_index = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assignments'
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        ordering = ['course', 'order_index']
        constraints = [
            models.CheckConstraint(
                check=models.Q(max_score__gt=0),
                name='valid_assignment_max_score'
            ),
            models.CheckConstraint(
                check=models.Q(passing_score__gte=0) & models.Q(passing_score__lte=models.F('max_score')),
                name='valid_assignment_passing_score'
            ),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class AssignmentSubmission(models.Model):
    """
    Assignment Submission model - tracks student assignment submissions.
    Maps to 'assignment_submissions' table in the database.
    """
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'
        PENDING = 'pending', 'Pending'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    enrollment = models.ForeignKey(
        'enrollments.Enrollment',
        on_delete=models.CASCADE,
        related_name='assignment_submissions'
    )
    
    # Submission content
    content = models.TextField()
    attachment_url = models.CharField(max_length=500, blank=True)
    
    # Grading
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assignment_submissions'
        verbose_name = 'Assignment Submission'
        verbose_name_plural = 'Assignment Submissions'
        unique_together = ['assignment', 'enrollment']
        ordering = ['-submitted_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['submitted', 'graded', 'pending']),
                name='valid_submission_status'
            ),
            models.CheckConstraint(
                check=models.Q(score__isnull=True) | models.Q(score__gte=0),
                name='valid_submission_score'
            ),
        ]

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.assignment.title}"


class Quiz(models.Model):
    """
    Quiz model - quizzes associated with lectures or courses.
    Maps to 'quizzes' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    lecture = models.OneToOneField(
        'courses.Lecture',
        on_delete=models.CASCADE,
        related_name='quiz',
        null=True,
        blank=True
    )
    
    # Quiz details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    
    # Quiz settings
    time_limit_minutes = models.IntegerField(null=True, blank=True)
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.00
    )
    max_attempts = models.IntegerField(default=3)
    shuffle_questions = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quizzes'
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(time_limit_minutes__isnull=True) | models.Q(time_limit_minutes__gt=0),
                name='valid_quiz_time_limit'
            ),
            models.CheckConstraint(
                check=models.Q(passing_score__gte=0) & models.Q(passing_score__lte=100),
                name='valid_quiz_passing_score'
            ),
            models.CheckConstraint(
                check=models.Q(max_attempts__gt=0),
                name='valid_max_attempts'
            ),
        ]

    def __str__(self):
        return self.title


class Question(models.Model):
    """
    Question model - individual questions within a quiz.
    Maps to 'questions' table in the database.
    """
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple_choice', 'Multiple Choice'
        TRUE_FALSE = 'true_false', 'True/False'
        SHORT_ANSWER = 'short_answer', 'Short Answer'
        ESSAY = 'essay', 'Essay'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    
    # Question details
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE
    )
    
    # Options and answers (stored as JSON)
    options = models.JSONField(default=list, blank=True)  # ['Option A', 'Option B', 'Option C', 'Option D']
    correct_answer = models.JSONField(default=list, blank=True)  # Can be single or multiple correct answers
    
    # Points and order
    points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00
    )
    order_index = models.IntegerField(default=0)
    
    # Additional info
    explanation = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'questions'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['quiz', 'order_index']
        constraints = [
            models.CheckConstraint(
                check=models.Q(question_type__in=['multiple_choice', 'true_false', 'short_answer', 'essay']),
                name='valid_question_type'
            ),
            models.CheckConstraint(
                check=models.Q(points__gt=0),
                name='valid_question_points'
            ),
        ]

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order_index}"


class QuizAttempt(models.Model):
    """
    Quiz Attempt model - tracks student quiz attempts.
    Maps to 'quiz_attempts' table in the database.
    """
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    enrollment = models.ForeignKey(
        'enrollments.Enrollment',
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    
    # Attempt details
    attempt_number = models.IntegerField(default=1)
    answers = models.JSONField(default=dict, blank=True)  # {question_id: answer}
    
    # Scoring
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    total_points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    passed = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quiz_attempts'
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
        ordering = ['-started_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['in_progress', 'submitted', 'graded']),
                name='valid_attempt_status'
            ),
            models.CheckConstraint(
                check=models.Q(attempt_number__gt=0),
                name='valid_attempt_number'
            ),
            models.CheckConstraint(
                check=models.Q(score__isnull=True) | models.Q(score__gte=0),
                name='valid_attempt_score'
            ),
            models.CheckConstraint(
                check=models.Q(percentage__isnull=True) | (models.Q(percentage__gte=0) & models.Q(percentage__lte=100)),
                name='valid_attempt_percentage'
            ),
        ]

    def __str__(self):
        return f"{self.enrollment.user.email} - {self.quiz.title} (Attempt {self.attempt_number})"

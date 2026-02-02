import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator



class Assignment(models.Model):
    """
    Assignment model - assignments associated with sections (includes quizzes).
    Maps to 'assignments' table in the database.
    """
    class AssignmentType(models.TextChoices):
        QUIZ = 'quiz', 'Quiz'
        ASSIGNMENT = 'assignment', 'Assignment'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    section = models.OneToOneField(
        'courses.Section',
        on_delete=models.CASCADE,
        related_name='assignment',
        null=True,
        blank=True
    )
    
    # Assignment details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    assignment_type = models.CharField(
        max_length=20,
        choices=AssignmentType.choices,
        default=AssignmentType.QUIZ
    )
    
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
    
    # Quiz-specific settings (only used if assignment_type == 'quiz')
    time_limit_minutes = models.IntegerField(null=True, blank=True)
    max_attempts = models.IntegerField(default=3)
    shuffle_questions = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=True)
    
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
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(assignment_type__in=['quiz', 'assignment']),
                name='valid_assignment_type'
            ),
            models.CheckConstraint(
                check=models.Q(max_score__gt=0),
                name='valid_assignment_max_score'
            ),
            models.CheckConstraint(
                check=models.Q(passing_score__gte=0) & models.Q(passing_score__lte=models.F('max_score')),
                name='valid_assignment_passing_score'
            ),
            models.CheckConstraint(
                check=models.Q(time_limit_minutes__isnull=True) | models.Q(time_limit_minutes__gt=0),
                name='valid_assignment_time_limit'
            ),
            models.CheckConstraint(
                check=models.Q(max_attempts__gt=0),
                name='valid_max_attempts'
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.assignment_type})"


class Question(models.Model):
    """
    Question model - individual questions within an assignment (for quizzes).
    Maps to 'questions' table in the database.
    """
    class QuestionType(models.TextChoices):
        MCQ = 'mcq', 'Multiple Choice Question (Single Answer)'
        MSQ = 'msq', 'Multiple Select Question (Multiple Answers)'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='questions',
        null=True,
        blank=True
    )
    
    # Question details
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ
    )
    
    # Options and answers (stored as JSON)
    options = models.JSONField(default=dict, blank=True)  # {'A': 'Option A', 'B': 'Option B', 'C': 'Option C', 'D': 'Option D'}
    correct_answer = models.JSONField(default=list, blank=True)  # [{'key': 'A'}, {'key': 'B'}] - list of correct answer JSON objects
    
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
        ordering = ['assignment', 'order_index']
        constraints = [
            models.CheckConstraint(
                check=models.Q(question_type__in=['mcq', 'msq']),
                name='valid_question_type'
            ),
            models.CheckConstraint(
                check=models.Q(points__gt=0),
                name='valid_question_points'
            ),
        ]

    def __str__(self):
        return f"{self.assignment.title} - Q{self.order_index}"


class QuestionAttempt(models.Model):
    """
    Question Attempt model - tracks student attempts on individual questions (for quizzes).
    Maps to 'question_attempts' table in the database.
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
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    enrollment = models.ForeignKey(
        'enrollments.Enrollment',
        on_delete=models.CASCADE,
        related_name='question_attempts'
    )
    
    # Attempt details
    attempt_number = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    answer = models.JSONField(default=list, blank=True)  # Selected answer(s) for this question
    
    is_correct = models.BooleanField(default=False)
    
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
        db_table = 'question_attempts'
        verbose_name = 'Question Attempt'
        verbose_name_plural = 'Question Attempts'
        ordering = ['-started_at']
        unique_together = ['question', 'enrollment', 'attempt_number']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['in_progress', 'submitted', 'graded']),
                name='valid_question_attempt_status'
            ),
        ]

    def is_correct_answer(self):
        """Check if the provided answer is correct based on question type"""
        question_type = self.question.question_type
        
        if question_type == 'mcq':
            # Single correct answer
            correct_keys = [item.get('key') for item in self.question.correct_answer if isinstance(item, dict)]
            given_keys = [item.get('key') for item in self.answer if isinstance(item, dict)]
            return len(given_keys) == 1 and given_keys[0] in correct_keys
        
        elif question_type == 'msq':
            # Multiple correct answers
            correct_keys = [item.get('key') for item in self.question.correct_answer if isinstance(item, dict)]
            given_keys = [item.get('key') for item in self.answer if isinstance(item, dict)]
            return set(correct_keys) == set(given_keys)
        return False
    
    def __str__(self):
        return f"{self.enrollment.user.email} - {self.question.assignment.title} Q{self.question.order_index} (Attempt {self.attempt_number})"


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
        'Assignment',
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    enrollment = models.ForeignKey(
        'enrollments.Enrollment',
        on_delete=models.CASCADE,
        related_name='assignment_submissions'
    )
    
    # Submission content
    attachment_url = models.CharField(max_length=500, blank=True)
    
    # Grading
    score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    feedback = models.TextField(blank=True)
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
                name='valid_assignment_submission_status'
            ),
        ]


    # score calculate percentage through all attempt questions 
    # and update score field
    def calculate_score(self):
        total_points = 0
        earned_points = 0

        # Fetch all question attempts related to this assignment submission
        question_attempts = QuestionAttempt.objects.filter(
            enrollment=self.enrollment,
            question__assignment=self.assignment,
            status=QuestionAttempt.Status.GRADED
        )

        for attempt in question_attempts:
            total_points += attempt.question.points
            if attempt.is_correct:
                earned_points += attempt.question.points

        if total_points > 0:
            self.score = round((earned_points / total_points) * 100, 2)
        else:
            self.score = 0.00

        self.save() 
    def __str__(self):
        return f"{self.enrollment.user.email} - {self.assignment.title}"


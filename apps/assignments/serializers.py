from rest_framework import serializers

from apps.assignments.models import AssignmentSubmission, Question, QuestionAttempt, Assignment

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class AssignmentQuestionSerializer(serializers.ModelSerializer):
    """Serializer for question details (excludes correct_answer for students)"""
    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class QuestionAttemptRequestSerializer(serializers.Serializer):
    """Serializer for question attempt request body (what the client sends)"""
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    answer = serializers.JSONField()
    attempt_number = serializers.IntegerField(default=1, min_value=1)
    status = serializers.ChoiceField(
        choices=QuestionAttempt.Status.choices,
        default=QuestionAttempt.Status.IN_PROGRESS
    )


class QuestionAttemptSerializer(serializers.ModelSerializer):
    """Full serializer for question attempt responses"""
    is_correct = serializers.BooleanField(read_only=True)
    enrollment = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = QuestionAttempt
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'started_at', 'is_correct', 'enrollment')

    def validate(self, data):
        """Validate the answer based on question type"""
        question = data.get('question')
        answer = data.get('answer')

        if question.question_type == Question.QuestionType.MCQ:
            # For MCQ, answer should be a list with a single dict containing 'key'
            if not isinstance(answer, list) or len(answer) != 1:
                raise serializers.ValidationError("Answer must be a list with a single answer object for MCQ.")
            
            if not isinstance(answer[0], dict) or 'key' not in answer[0]:
                raise serializers.ValidationError("Answer must contain a 'key' field for MCQ.")
            
            if answer[0]['key'] not in question.options.keys():
                raise serializers.ValidationError("Invalid option key provided for MCQ.")
            

        elif question.question_type == Question.QuestionType.MSQ:
            # For MSQ, answer should be a list of dicts with 'key'
            if not isinstance(answer, list) or len(answer) < 1:
                raise serializers.ValidationError("Answer must be a list of answer objects for MSQ.")
            
            for ans in answer:
                if not isinstance(ans, dict) or 'key' not in ans:
                    raise serializers.ValidationError("Each answer must contain a 'key' field for MSQ.")
                if ans['key'] not in question.options.keys():
                    raise serializers.ValidationError(f"Invalid option key '{ans['key']}' provided for MSQ.")
        else:
            raise serializers.ValidationError("Unsupported question type.")

        return data
    
    def create(self, validated_data):
        """Create the question attempt and set is_correct"""
        instance = super().create(validated_data)
        instance.is_correct = instance.is_correct_answer()
        instance.save()
        return instance 

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = '__all__'
        read_only_fields = 'id', 'created_at', 'updated_at'

    def create(self, validated_data):
        """Create assignment submission and calculate score"""
        instance = super().create(validated_data)
        instance.calculate_score()
        return instance
    

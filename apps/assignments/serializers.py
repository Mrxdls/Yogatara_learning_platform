from rest_framework import serializers

from apps.assignments.models import AssignmentSubmission, Question, QuestionAttempt, Assignment

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = 'id', 'created_at', 'updated_at'
class AssignmentQuestionSerializer(serializers.ModelSerializer):
    # get an serializer for get question details
    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = 'id', 'created_at', 'updated_at'

    # send questions and receive answers
class QuestionAttemptSerializer(serializers.ModelSerializer):
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = QuestionAttempt
        fields = '__all__'
        read_only_fields = 'id', 'created_at', 'updated_at', 'is_correct'

    # def get_is_correct(self, obj):
    #     """Check if the provided answer is correct based on question type"""
    #     question_type = obj.question.question_type
        
    #     if question_type == 'mcq':
    #         # Single correct answer
    #         correct_keys = [item.get('key') for item in obj.question.correct_answer if isinstance(item, dict)]
    #         given_keys = [item.get('key') for item in obj.answer if isinstance(item, dict)]
    #         return len(given_keys) == 1 and given_keys[0] in correct_keys
        
    #     elif question_type == 'msq':
    #         # Multiple correct answers
    #         correct_keys = [item.get('key') for item in obj.question.correct_answer if isinstance(item, dict)]
    #         given_keys = [item.get('key') for item in obj.answer if isinstance(item, dict)]
    #         return set(correct_keys) == set(given_keys)
    #     return False

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
        instance.is_correct_answer()
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
    

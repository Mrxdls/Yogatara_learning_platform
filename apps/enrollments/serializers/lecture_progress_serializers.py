from rest_framework import serializers

from apps.enrollments.models import LectureProgress
from ..models import LectureProgress

class LectureProgressSerializer(serializers.ModelSerializer):
    lecture_title = serializers.CharField(source='lecture.title', read_only=True)
    section_title = serializers.CharField(source='lecture.section.title', read_only=True)

    class Meta:
        model = LectureProgress
        fields = '__all__'
        read_only_fields = [
            'id',
            'enrollment',
            'lecture_title',
            'section_title',
            'completion_percentage',
            'is_completed',
            'last_watched_at',
            'updated_at',
        ]

    def create(self, validated_data):
        # Ensure enrollment is set from context if needed
        # validated_data['enrollment'] = self.context['request'].user.enrollment or something
        return super().create(validated_data)

    def update(self, instance, validated_data):
        watched_seconds = validated_data.get('watched_seconds', instance.watched_seconds)
        total_seconds = validated_data.get('total_seconds', instance.total_seconds) or instance.total_seconds
        
        if total_seconds and total_seconds > 0:
            completion_percentage = round((watched_seconds / total_seconds) * 100, 2)
        else:
            completion_percentage = 0.00
        
        validated_data['completion_percentage'] = completion_percentage
        validated_data['is_completed'] = completion_percentage >= 100.00
        
        return super().update(instance, validated_data)
    

class CourseProgressSerializer(serializers.Serializer):
    enrollment_id = serializers.UUIDField()
    course_id = serializers.UUIDField(source='course.id')
    course_title = serializers.CharField(source='course.title')
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    sections = serializers.SerializerMethodField()

    def get_sections(self, obj):
        sections = obj.course.sections.filter(is_published=True).prefetch_related('lectures')
        section_data = []
        for section in sections:
            lectures = section.lectures.filter(is_published=True)
            lecture_progresses = {lp.lecture_id: lp for lp in obj.lecture_progress.filter(lecture__in=lectures)}
            
            completed_lectures = sum(1 for lp in lecture_progresses.values() if lp.is_completed)
            total_lectures = lectures.count()
            section_progress = (completed_lectures / total_lectures * 100) if total_lectures > 0 else 0
            
            section_data.append({
                'section_id': section.id,
                'title': section.title,
                'completed_lectures': completed_lectures,
                'total_lectures': total_lectures,
                'progress_percentage': round(section_progress, 2),
            })
        return section_data
    


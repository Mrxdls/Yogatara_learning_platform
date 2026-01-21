# API Implementation Roadmap

## Priority Order for Building APIs

### **Phase 1: Core Authentication & User Management** ⭐⭐⭐
**Timeline**: Week 1  
**Models**: User, UserProfile, UserSettings

1. **Authentication APIs** (`apps/authentication/`)
   - User Registration
   - Login (JWT)
   - Token Refresh
   - Email Verification
   - Password Reset

2. **User Profile APIs** (`apps/users/`)
   - Get/Update Profile
   - Manage Settings
   - Social Links
   - Skills Management

---

### **Phase 2: Course Catalog** ⭐⭐⭐
**Timeline**: Week 2  
**Models**: Category, Course, CourseMetadata, CoursePricing, Instructor

3. **Course Discovery APIs** (`apps/courses/`)
   - List Courses (with filters, search, pagination)
   - Course Details
   - Categories
   - Instructor Profiles

4. **Course Management APIs** (Instructor only)
   - Create/Update/Delete Course
   - Manage Course Metadata
   - Set Pricing

---

### **Phase 3: Course Content** ⭐⭐
**Timeline**: Week 3  
**Models**: Section, Lecture, VideoContent, PDFContent, LectureResource

5. **Content Structure APIs** (`apps/courses/`)
   - Sections CRUD
   - Lectures CRUD
   - Content Ordering

6. **Content Upload APIs** (`apps/videos/`)
   - Video Upload & Processing
   - PDF Upload
   - Lecture Resources
   - File Management

---

### **Phase 4: Enrollment & Progress** ⭐⭐⭐
**Timeline**: Week 4  
**Models**: Enrollment, VideoProgress, Bookmark, Note

7. **Enrollment APIs** (`apps/enrollments/`)
   - Enroll in Course
   - View My Enrollments
   - Unenroll

8. **Progress Tracking APIs** (`apps/enrollments/`)
   - Update Video Progress
   - Get Course Progress
   - Bookmarks Management
   - Notes Management

---

### **Phase 5: Assessments** ⭐
**Timeline**: Week 5-6  
**Models**: Assignment, AssignmentSubmission, Quiz, Question, QuizAttempt

9. **Assignment APIs** (`apps/assignments/`)
   - Create/View Assignments
   - Submit Assignment
   - Grade Submission (Instructor)

10. **Quiz APIs** (`apps/assignments/`)
    - Create Quiz & Questions
    - Start Quiz Attempt
    - Submit Answers
    - View Results

---

## Implementation Pattern (Follow for Each Phase)

### 1. **Create Serializers**
```python
# apps/<app_name>/serializers.py
from rest_framework import serializers
from .models import ModelName

class ModelNameSerializer(serializers.ModelSerializer):
    # Add any extra fields
    extra_field = serializers.SerializerMethodField()
    
    class Meta:
        model = ModelName
        fields = '__all__'  # or specify fields list
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_extra_field(self, obj):
        # Custom logic
        return value
    
    def validate_field_name(self, value):
        # Field-level validation
        return value
    
    def validate(self, attrs):
        # Object-level validation
        return attrs
```

### 2. **Create ViewSets**
```python
# apps/<app_name>/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ModelName
from .serializers import ModelNameSerializer

class ModelNameViewSet(viewsets.ModelViewSet):
    queryset = ModelName.objects.all()
    serializer_class = ModelNameSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter based on user
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        # Custom endpoint
        instance = self.get_object()
        # Logic here
        return Response({'status': 'success'})
```

### 3. **Configure URLs**
```python
# apps/<app_name>/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModelNameViewSet

router = DefaultRouter()
router.register(r'modelnames', ModelNameViewSet, basename='modelname')

urlpatterns = [
    path('', include(router.urls)),
]
```

### 4. **Include in Main URLs**
```python
# Learning_hub/urls.py
from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('apps.authentication.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/courses/', include('apps.courses.urls')),
    path('api/enrollments/', include('apps.enrollments.urls')),
    path('api/assignments/', include('apps.assignments.urls')),
]
```

---

## Common Permissions

Create these in a shared `permissions.py` file:

```python
# apps/common/permissions.py
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """Check if user owns the object"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsInstructor(permissions.BasePermission):
    """Check if user is an instructor"""
    def has_permission(self, request, view):
        return request.user.role == 'instructor'

class IsStudent(permissions.BasePermission):
    """Check if user is a student"""
    def has_permission(self, request, view):
        return request.user.role == 'student'

class IsEnrolled(permissions.BasePermission):
    """Check if student is enrolled in the course"""
    def has_object_permission(self, request, view, obj):
        from apps.enrollments.models import Enrollment
        return Enrollment.objects.filter(
            user=request.user,
            course=obj.course,
            status='active'
        ).exists()

class ReadOnly(permissions.BasePermission):
    """Read-only access"""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
```

---

## Filtering & Pagination

```python
# apps/courses/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination

class CoursePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = CoursePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filtering
    filterset_fields = ['category', 'level', 'status']
    
    # Search
    search_fields = ['title', 'description', 'course_code']
    
    # Ordering
    ordering_fields = ['created_at', 'title', 'price']
    ordering = ['-created_at']
```

---

## Testing Strategy

```python
# apps/<app_name>/tests.py
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.authentication.models import User

class ModelNameAPITestCase(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='student'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_items(self):
        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_item(self):
        data = {'title': 'Test Item'}
        response = self.client.post('/api/items/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

---

## API Documentation (drf-spectacular)

Already configured in settings. Access at:
- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

Add schema customization:
```python
# In your serializer or view
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    summary="List all courses",
    description="Get paginated list of courses with filtering",
    parameters=[
        OpenApiParameter(name='category', description='Filter by category ID'),
        OpenApiParameter(name='level', description='Filter by level'),
    ],
    responses={200: CourseSerializer(many=True)}
)
def list(self, request, *args, **kwargs):
    return super().list(request, *args, **kwargs)
```

---

## Quick Start Checklist

### Phase 1 (Authentication)
- [ ] Create User serializers (Register, Login, Profile)
- [ ] Create authentication views (Register, Login, Logout)
- [ ] Configure JWT settings
- [ ] Add email verification
- [ ] Test authentication flow

### Phase 2 (Courses)
- [ ] Create Course serializers (List, Detail, Create)
- [ ] Create Category serializers
- [ ] Build CourseViewSet with filters
- [ ] Add search functionality
- [ ] Test course CRUD operations

### Phase 3 (Content)
- [ ] Create Section/Lecture serializers
- [ ] Build content upload functionality
- [ ] Handle video/PDF processing
- [ ] Test content management

### Phase 4 (Enrollment)
- [ ] Create Enrollment serializers
- [ ] Build enrollment logic
- [ ] Create progress tracking endpoints
- [ ] Add bookmark/notes features
- [ ] Test enrollment flow

### Phase 5 (Assessments)
- [ ] Create Assignment/Quiz serializers
- [ ] Build submission logic
- [ ] Add grading functionality
- [ ] Test assessment flow

---

## Development Commands

```bash
# Start development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Access Django shell
python manage.py shell

# Check for issues
python manage.py check
```

---

## Recommended Tools

1. **Postman/Insomnia** - API testing
2. **Django Debug Toolbar** - Development debugging
3. **django-extensions** - Enhanced management commands
4. **django-cors-headers** - CORS handling for frontend
5. **celery** - Background tasks (video processing)
6. **redis** - Caching & task queue

---

Start with **Phase 1** and build incrementally. Each phase should be fully tested before moving to the next!

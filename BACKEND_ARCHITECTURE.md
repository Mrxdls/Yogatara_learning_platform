# Backend Architecture & API Documentation

## Table of Contents
1. [Database Schema Overview](#database-schema-overview)
2. [Model Relationships](#model-relationships)
3. [API Categories](#api-categories)
4. [Detailed API Endpoints](#detailed-api-endpoints)

---

## Database Schema Overview

### Core Entities

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER MANAGEMENT                          │
├─────────────────────────────────────────────────────────────────┤
│ User (authentication.User)                                       │
│   ├── UserProfile (users.UserProfile)           [1:1]           │
│   ├── UserSettings (users.UserSettings)         [1:1]           │
│   ├── UserSocial (users.UserSocial)            [1:1]           │
│   └── UserSkill (users.UserSkill)              [1:N]           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      COURSE MANAGEMENT                           │
├─────────────────────────────────────────────────────────────────┤
│ Category (courses.Category)                                      │
│ Course (courses.Course)                                          │
│   ├── CourseMetadata (courses.CourseMetadata)   [1:1]          │
│   ├── CoursePricing (courses.CoursePricing)     [1:1]          │
│   ├── CourseInstructor (courses.CourseInstructor) [M:N]        │
│   └── Section (courses.Section)                 [1:N]          │
│         └── Lecture (courses.Lecture)           [1:N]          │
│               ├── VideoContent (videos.VideoContent)  [1:1]     │
│               ├── PDFContent (videos.PDFContent)      [1:1]     │
│               ├── LectureResource (videos.LectureResource) [1:N]│
│               └── Quiz (assignments.Quiz)             [1:1]     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ENROLLMENT & PROGRESS                         │
├─────────────────────────────────────────────────────────────────┤
│ Enrollment (enrollments.Enrollment)                              │
│   ├── VideoProgress (enrollments.VideoProgress) [1:N]           │
│   ├── Bookmark (enrollments.Bookmark)          [1:N]           │
│   └── Note (enrollments.Note)                  [1:N]           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     ASSESSMENTS                                  │
├─────────────────────────────────────────────────────────────────┤
│ Assignment (assignments.Assignment)                              │
│   └── AssignmentSubmission                     [1:N]           │
│ Quiz (assignments.Quiz)                                          │
│   ├── Question (assignments.Question)          [1:N]           │
│   └── QuizAttempt (assignments.QuizAttempt)   [1:N]           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Model Relationships

### 1. **User Management Models**

#### **User** (`apps/authentication/models.py`)
- **Primary Key**: `id` (UUID)
- **Role**: TextChoices ('student', 'instructor', 'admin')
- **Relationships**:
  - Has ONE UserProfile
  - Has ONE UserSettings
  - Has ONE UserSocial
  - Has MANY UserSkills
  - Has MANY Enrollments
  - Has MANY created Courses (as instructor)

```python
# Example Usage
from apps.authentication.models import User

# Create a student user
student = User.objects.create_user(
    email='student@example.com',
    password='password123',
    role=User.Role.STUDENT
)

# Create an instructor
instructor = User.objects.create_user(
    email='instructor@example.com',
    password='password123',
    role=User.Role.INSTRUCTOR
)
```

#### **UserProfile** (`apps/users/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `user` → User (OneToOne)
- **Purpose**: Extended user information (name, bio, avatar, location)

```python
# Example Usage
from apps.users.models import UserProfile

# Create or update profile
profile, created = UserProfile.objects.get_or_create(
    user=student,
    defaults={
        'first_name': 'John',
        'last_name': 'Doe',
        'bio': 'Passionate learner',
        'location': 'New York'
    }
)
```

#### **UserSettings** (`apps/users/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `user` → User (OneToOne)
- **Purpose**: User preferences (theme, language, notifications, video settings)

#### **UserSocial** (`apps/users/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `user` → User (OneToOne)
- **Purpose**: Social media links

#### **UserSkill** (`apps/users/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `user` → User (ForeignKey)
- **Purpose**: User's skills with proficiency levels

---

### 2. **Course Management Models**

#### **Category** (`apps/courses/models.py`)
- **Primary Key**: `id` (UUID)
- **Self-Reference**: `parent_category` (for hierarchical categories)
- **Purpose**: Organize courses into categories

```python
# Example Usage
from apps.courses.models import Category

# Create parent category
programming = Category.objects.create(
    name='Programming',
    slug='programming',
    description='Programming courses'
)

# Create subcategory
python = Category.objects.create(
    name='Python',
    slug='python',
    parent_category=programming
)
```

#### **Course** (`apps/courses/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `category` → Category
  - `created_by` → User
- **Relationships**:
  - Has ONE CourseMetadata
  - Has ONE CoursePricing
  - Has MANY CourseInstructors (M:N with Instructor)
  - Has MANY Sections

```python
# Example Usage
from apps.courses.models import Course

course = Course.objects.create(
    course_code='PY101',
    title='Python for Beginners',
    slug='python-for-beginners',
    description='Learn Python from scratch',
    level='Beginner',
    category=python,
    created_by=instructor,
    status='published'
)
```

#### **Section** (`apps/courses/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `course` → Course
- **Purpose**: Organize lectures into sections

```python
# Example Usage
from apps.courses.models import Section

section = Section.objects.create(
    course=course,
    title='Getting Started',
    order_index=1
)
```

#### **Lecture** (`apps/courses/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `section` → Section
- **Content Types**: 'video', 'pdf', 'quiz', 'text'
- **Relationships**:
  - Has ONE VideoContent (if content_type='video')
  - Has ONE PDFContent (if content_type='pdf')
  - Has ONE Quiz (if content_type='quiz')
  - Has MANY LectureResources

```python
# Example Usage
from apps.courses.models import Lecture

lecture = Lecture.objects.create(
    section=section,
    title='Introduction to Python',
    content_type='video',
    order_index=1,
    duration_seconds=600
)
```

---

### 3. **Content Models**

#### **VideoContent** (`apps/videos/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `lecture` → Lecture (OneToOne)
- **Purpose**: Video-specific content (URL, provider, quality, captions)

```python
# Example Usage
from apps.videos.models import VideoContent

video = VideoContent.objects.create(
    lecture=lecture,
    video_url='https://vimeo.com/12345678',
    video_provider='vimeo',
    duration_seconds=600,
    thumbnail_url='https://example.com/thumb.jpg'
)
```

#### **PDFContent** (`apps/videos/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `lecture` → Lecture (OneToOne)

#### **LectureResource** (`apps/videos/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `lecture` → Lecture
- **Purpose**: Downloadable resources (PDFs, code files, documents)

---

### 4. **Enrollment & Progress Models**

#### **Enrollment** (`apps/enrollments/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `user` → User
  - `course` → Course
- **Status**: TextChoices ('active', 'completed', 'cancelled')
- **Payment Status**: TextChoices ('free', 'paid', 'refunded')
- **Unique Together**: ['user', 'course']

```python
# Example Usage
from apps.enrollments.models import Enrollment

enrollment = Enrollment.objects.create(
    user=student,
    course=course,
    status=Enrollment.Status.ACTIVE,
    payment_status=Enrollment.PaymentStatus.FREE
)
```

#### **VideoProgress** (`apps/enrollments/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `enrollment` → Enrollment
  - `lecture` → Lecture
- **Purpose**: Track video watching progress

```python
# Example Usage
from apps.enrollments.models import VideoProgress

progress = VideoProgress.objects.create(
    enrollment=enrollment,
    lecture=lecture,
    watched_seconds=300,
    total_seconds=600,
    completion_percentage=50.00
)
```

#### **Bookmark** (`apps/enrollments/models.py`)
- **Purpose**: Save specific points in videos/lectures

#### **Note** (`apps/enrollments/models.py`)
- **Purpose**: Take notes during lectures

---

### 5. **Assessment Models**

#### **Assignment** (`apps/assignments/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `course` → Course
- **Purpose**: Course assignments

```python
# Example Usage
from apps.assignments.models import Assignment

assignment = Assignment.objects.create(
    course=course,
    title='Python Basics Quiz',
    description='Test your Python knowledge',
    max_score=100.00,
    due_date='2026-02-01'
)
```

#### **AssignmentSubmission** (`apps/assignments/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `assignment` → Assignment
  - `enrollment` → Enrollment
  - `graded_by` → User (optional)
- **Status**: TextChoices ('submitted', 'graded', 'pending')

#### **Quiz** (`apps/assignments/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `lecture` → Lecture (OneToOne)

#### **Question** (`apps/assignments/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `quiz` → Quiz
- **Question Types**: 'multiple_choice', 'true_false', 'short_answer', 'essay'

#### **QuizAttempt** (`apps/assignments/models.py`)
- **Primary Key**: `id` (UUID)
- **Foreign Keys**:
  - `quiz` → Quiz
  - `enrollment` → Enrollment

---

## API Categories

### **Category 1: Authentication & Authorization**
**Models Used**: User  
**App**: `apps.authentication`

| Endpoint | Method | Description | Models |
|----------|--------|-------------|--------|
| `/api/auth/register/` | POST | User registration | User |
| `/api/auth/login/` | POST | User login (JWT) | User |
| `/api/auth/logout/` | POST | User logout | User |
| `/api/auth/refresh/` | POST | Refresh JWT token | User |
| `/api/auth/verify-email/` | POST | Verify email | User |
| `/api/auth/password-reset/` | POST | Request password reset | User |
| `/api/auth/password-reset-confirm/` | POST | Confirm password reset | User |

---

### **Category 2: User Profile Management**
**Models Used**: User, UserProfile, UserSettings, UserSocial, UserSkill  
**App**: `apps.users`

| Endpoint | Method | Description | Models |
|----------|--------|-------------|--------|
| `/api/users/me/` | GET | Get current user profile | User, UserProfile |
| `/api/users/me/` | PUT/PATCH | Update user profile | UserProfile |
| `/api/users/me/settings/` | GET | Get user settings | UserSettings |
| `/api/users/me/settings/` | PUT/PATCH | Update user settings | UserSettings |
| `/api/users/me/social/` | GET/PUT | Manage social links | UserSocial |
| `/api/users/me/skills/` | GET | List user skills | UserSkill |
| `/api/users/me/skills/` | POST | Add skill | UserSkill |
| `/api/users/me/skills/{id}/` | DELETE | Remove skill | UserSkill |
| `/api/users/{id}/` | GET | Get user public profile | User, UserProfile |

---

### **Category 3: Course Catalog & Discovery**
**Models Used**: Category, Course, CourseMetadata, CoursePricing, Instructor, CourseInstructor  
**App**: `apps.courses`

| Endpoint | Method | Description | Models |
|----------|--------|-------------|--------|
| `/api/courses/` | GET | List all courses (with filters) | Course, CourseMetadata, CoursePricing |
| `/api/courses/{id}/` | GET | Get course details | Course, CourseMetadata, CoursePricing, CourseInstructor |
| `/api/courses/` | POST | Create course (instructor) | Course |
| `/api/courses/{id}/` | PUT/PATCH | Update course | Course |
| `/api/courses/{id}/` | DELETE | Delete course | Course |
| `/api/courses/categories/` | GET | List categories | Category |
| `/api/courses/categories/{id}/` | GET | Get category with courses | Category, Course |
| `/api/courses/{id}/instructors/` | GET | List course instructors | CourseInstructor, Instructor |
| `/api/instructors/` | GET | List instructors | Instructor |
| `/api/instructors/{id}/` | GET | Get instructor profile | Instructor, Course |

---

### **Category 4: Course Content**
**Models Used**: Section, Lecture, VideoContent, PDFContent, LectureResource  
**Apps**: `apps.courses`, `apps.videos`

| Endpoint | Method | Description | Models |
|----------|--------|-------------|--------|
| `/api/courses/{course_id}/sections/` | GET | List course sections | Section |
| `/api/courses/{course_id}/sections/` | POST | Create section | Section |
| `/api/sections/{id}/` | PUT/PATCH | Update section | Section |
| `/api/sections/{id}/lectures/` | GET | List section lectures | Lecture |
| `/api/sections/{id}/lectures/` | POST | Create lecture | Lecture |
| `/api/lectures/{id}/` | GET | Get lecture details | Lecture, VideoContent, PDFContent |
| `/api/lectures/{id}/` | PUT/PATCH | Update lecture | Lecture |
| `/api/lectures/{id}/video/` | POST | Upload video content | VideoContent |
| `/api/lectures/{id}/pdf/` | POST | Upload PDF content | PDFContent |
| `/api/lectures/{id}/resources/` | GET | List lecture resources | LectureResource |
| `/api/lectures/{id}/resources/` | POST | Add resource | LectureResource |

---

### **Category 5: Enrollment**
**Models Used**: Enrollment, Course  
**App**: `apps.enrollments`

| Endpoint | Method | Description | Models |
|----------|--------|-------------|--------|
| `/api/enrollments/` | GET | List user enrollments | Enrollment, Course |
| `/api/enrollments/` | POST | Enroll in course | Enrollment |
| `/api/enrollments/{id}/` | GET | Get enrollment details | Enrollment |
| `/api/enrollments/{id}/` | DELETE | Unenroll from course | Enrollment |
| `/api/courses/{id}/enroll/` | POST | Enroll in specific course | Enrollment |

---

### **Category 6: Learning Progress**
**Models Used**: VideoProgress, Bookmark, Note, Enrollment  
**App**: `apps.enrollments`

| Endpoint | Method | Description | Models |
|----------|--------|-------------|--------|
| `/api/enrollments/{id}/progress/` | GET | Get overall progress | Enrollment, VideoProgress |
| `/api/lectures/{id}/progress/` | GET | Get lecture progress | VideoProgress |
| `/api/lectures/{id}/progress/` | POST/PUT | Update video progress | VideoProgress |
| `/api/enrollments/{id}/bookmarks/` | GET | List bookmarks | Bookmark |
| `/api/lectures/{id}/bookmarks/` | POST | Add bookmark | Bookmark |
| `/api/bookmarks/{id}/` | PUT/DELETE | Update/delete bookmark | Bookmark |
| `/api/enrollments/{id}/notes/` | GET | List notes | Note |
| `/api/lectures/{id}/notes/` | POST | Add note | Note |
| `/api/notes/{id}/` | PUT/DELETE | Update/delete note | Note |

---

### **Category 7: Assignments**
**Models Used**: Assignment, AssignmentSubmission, Enrollment  
**App**: `apps.assignments`

| Endpoint | Method | Description | Models |
|----------|--------|-------------|--------|
| `/api/courses/{id}/assignments/` | GET | List course assignments | Assignment |
| `/api/courses/{id}/assignments/` | POST | Create assignment (instructor) | Assignment |
| `/api/assignments/{id}/` | GET | Get assignment details | Assignment |
| `/api/assignments/{id}/` | PUT/PATCH | Update assignment | Assignment |
| `/api/assignments/{id}/submit/` | POST | Submit assignment | AssignmentSubmission |
| `/api/assignments/{id}/submissions/` | GET | List submissions (instructor) | AssignmentSubmission |
| `/api/submissions/{id}/` | GET | Get submission details | AssignmentSubmission |
| `/api/submissions/{id}/grade/` | POST | Grade submission (instructor) | AssignmentSubmission |

---

### **Category 8: Quizzes & Questions**
**Models Used**: Quiz, Question, QuizAttempt  
**App**: `apps.assignments`

| Endpoint | Method | Description | Models |
|----------|--------|-------------|--------|
| `/api/lectures/{id}/quiz/` | GET | Get lecture quiz | Quiz, Question |
| `/api/lectures/{id}/quiz/` | POST | Create quiz (instructor) | Quiz |
| `/api/quizzes/{id}/` | PUT/PATCH | Update quiz | Quiz |
| `/api/quizzes/{id}/questions/` | GET | List questions | Question |
| `/api/quizzes/{id}/questions/` | POST | Add question | Question |
| `/api/questions/{id}/` | PUT/DELETE | Update/delete question | Question |
| `/api/quizzes/{id}/start/` | POST | Start quiz attempt | QuizAttempt |
| `/api/quiz-attempts/{id}/` | GET | Get attempt details | QuizAttempt |
| `/api/quiz-attempts/{id}/submit/` | POST | Submit quiz answers | QuizAttempt |
| `/api/quiz-attempts/{id}/result/` | GET | Get quiz result | QuizAttempt |

---

## API Implementation Strategy

### **Step 1: Create Serializers** (for each category)

```python
# apps/users/serializers.py
from rest_framework import serializers
from .models import UserProfile, UserSettings

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'bio', 'avatar_url', ...]
        read_only_fields = ['id', 'created_at']
```

### **Step 2: Create ViewSets**

```python
# apps/users/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
```

### **Step 3: Configure URLs**

```python
# apps/users/urls.py
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')

urlpatterns = router.urls
```

---

## Model Usage Examples

### **Creating a Complete Course Flow**

```python
# 1. Create Course
course = Course.objects.create(
    course_code='PY101',
    title='Python Mastery',
    category=category,
    created_by=instructor
)

# 2. Add Metadata
CourseMetadata.objects.create(
    course=course,
    duration_minutes=600,
    has_certificate=True
)

# 3. Add Pricing
CoursePricing.objects.create(
    course=course,
    price=99.99,
    currency='USD'
)

# 4. Add Sections
section = Section.objects.create(
    course=course,
    title='Introduction',
    order_index=1
)

# 5. Add Lectures
lecture = Lecture.objects.create(
    section=section,
    title='Getting Started',
    content_type='video',
    order_index=1
)

# 6. Add Video Content
VideoContent.objects.create(
    lecture=lecture,
    video_url='https://vimeo.com/123456',
    video_provider='vimeo'
)
```

### **Student Enrollment & Progress**

```python
# 1. Enroll Student
enrollment = Enrollment.objects.create(
    user=student,
    course=course,
    status=Enrollment.Status.ACTIVE
)

# 2. Track Video Progress
VideoProgress.objects.create(
    enrollment=enrollment,
    lecture=lecture,
    watched_seconds=300,
    completion_percentage=50.00
)

# 3. Add Bookmark
Bookmark.objects.create(
    enrollment=enrollment,
    lecture=lecture,
    timestamp_seconds=180,
    title='Important concept'
)
```

---

## Next Steps

1. **Create Serializers** for each model
2. **Build ViewSets** for CRUD operations
3. **Configure Permissions** (IsStudent, IsInstructor, IsOwner)
4. **Add Filtering & Pagination**
5. **Implement Search** functionality
6. **Add API Documentation** using drf-spectacular
7. **Write Tests** for each endpoint

This architecture provides a solid foundation for building a comprehensive learning management system!

# API Contract Documentation - Normalized Design (3NF)
**Version:** 2.0  
**Last Updated:** January 20, 2026  
**Project:** YogataraWeb - Online Learning Platform  
**Database Design:** Third Normal Form (3NF)

---

## Table of Contents
1. [Database Schema (3NF)](#1-database-schema-3nf)
2. [Authentication & Authorization APIs](#2-authentication--authorization-apis)
3. [User Management APIs](#3-user-management-apis)
4. [Course APIs](#4-course-apis)
5. [Enrollment APIs](#5-enrollment-apis)
6. [Learning Progress APIs](#6-learning-progress-apis)
7. [Assessment APIs](#7-assessment-apis)
8. [Content Management APIs](#8-content-management-apis)
9. [Social & Interaction APIs](#9-social--interaction-apis)
10. [Analytics & Reporting APIs](#10-analytics--reporting-apis)
11. [Media & File Management APIs](#11-media--file-management-apis)
12. [Error Handling & Conventions](#12-error-handling--conventions)

---

## 1. Database Schema (3NF)

### 1.1 Normalized Entity Relationship

```
Users
├── UserProfiles (1:1)
├── UserSettings (1:1)
├── UserSocial (1:1)
├── UserSkills (1:N)
└── Enrollments (1:N)

Courses
├── CourseMetadata (1:1)
├── CoursePricing (1:1)
├── CourseInstructors (M:N) → Instructors
├── CourseTags (M:N) → Tags
├── CourseCategories (M:1) → Categories
├── Sections (1:N)
└── Reviews (1:N)

Sections
└── Lectures (1:N)

Lectures
├── VideoContent (1:1)
├── PDFContent (1:1)
├── QuizContent (1:1)
└── LectureResources (1:N)

Enrollments
├── VideoProgress (1:N)
├── QuizAttempts (1:N)
├── AssignmentSubmissions (1:N)
├── Bookmarks (1:N)
└── Notes (1:N)

Assessments
├── Assignments (Course → Assignment)
├── Quizzes (Lecture → Quiz)
└── Questions (Quiz → Question)
```

### 1.2 Core Entity Models

#### Users Table
```sql
CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('student', 'instructor', 'admin') DEFAULT 'student',
  email_verified BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login_at TIMESTAMP
);
```

#### User Profiles Table
```sql
CREATE TABLE user_profiles (
  profile_id UUID PRIMARY KEY,
  user_id UUID UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  display_name VARCHAR(100),
  avatar_url VARCHAR(500),
  bio TEXT,
  phone VARCHAR(20),
  location VARCHAR(100),
  timezone VARCHAR(50) DEFAULT 'UTC',
  website VARCHAR(255),
  education TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Courses Table
```sql
CREATE TABLE courses (
  course_id UUID PRIMARY KEY,
  course_code VARCHAR(50) UNIQUE NOT NULL,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) UNIQUE NOT NULL,
  short_description VARCHAR(500),
  description TEXT,
  level ENUM('Beginner', 'Intermediate', 'Advanced', 'All Levels'),
  language VARCHAR(50) DEFAULT 'English',
  status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
  category_id UUID REFERENCES categories(category_id),
  thumbnail_url VARCHAR(500),
  promo_video_url VARCHAR(500),
  created_by UUID REFERENCES users(user_id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  published_at TIMESTAMP
);
```

#### Course Metadata Table
```sql
CREATE TABLE course_metadata (
  metadata_id UUID PRIMARY KEY,
  course_id UUID UNIQUE REFERENCES courses(course_id) ON DELETE CASCADE,
  duration_minutes INT,
  total_lectures INT,
  total_sections INT,
  is_featured BOOLEAN DEFAULT FALSE,
  is_bestseller BOOLEAN DEFAULT FALSE,
  has_certificate BOOLEAN DEFAULT TRUE,
  drip_content BOOLEAN DEFAULT FALSE,
  comments_enabled BOOLEAN DEFAULT TRUE,
  avg_rating DECIMAL(3,2) DEFAULT 0,
  total_reviews INT DEFAULT 0,
  total_enrollments INT DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Course Pricing Table
```sql
CREATE TABLE course_pricing (
  pricing_id UUID PRIMARY KEY,
  course_id UUID UNIQUE REFERENCES courses(course_id) ON DELETE CASCADE,
  price DECIMAL(10,2) NOT NULL,
  sale_price DECIMAL(10,2),
  currency VARCHAR(3) DEFAULT 'USD',
  is_free BOOLEAN DEFAULT FALSE,
  sale_start_date TIMESTAMP,
  sale_end_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Instructors Table
```sql
CREATE TABLE instructors (
  instructor_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id),
  name VARCHAR(255) NOT NULL,
  title VARCHAR(255),
  bio TEXT,
  avatar_url VARCHAR(500),
  expertise TEXT[],
  total_students INT DEFAULT 0,
  total_courses INT DEFAULT 0,
  avg_rating DECIMAL(3,2) DEFAULT 0,
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Course Instructors Table (Many-to-Many)
```sql
CREATE TABLE course_instructors (
  course_id UUID REFERENCES courses(course_id) ON DELETE CASCADE,
  instructor_id UUID REFERENCES instructors(instructor_id) ON DELETE CASCADE,
  role VARCHAR(50) DEFAULT 'primary',
  order_index INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (course_id, instructor_id)
);
```

#### Sections Table
```sql
CREATE TABLE sections (
  section_id UUID PRIMARY KEY,
  course_id UUID REFERENCES courses(course_id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  order_index INT NOT NULL,
  is_published BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Lectures Table
```sql
CREATE TABLE lectures (
  lecture_id UUID PRIMARY KEY,
  section_id UUID REFERENCES sections(section_id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  content_type ENUM('video', 'pdf', 'quiz', 'text') NOT NULL,
  duration_seconds INT,
  order_index INT NOT NULL,
  is_preview BOOLEAN DEFAULT FALSE,
  is_published BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Video Content Table
```sql
CREATE TABLE video_content (
  video_id UUID PRIMARY KEY,
  lecture_id UUID UNIQUE REFERENCES lectures(lecture_id) ON DELETE CASCADE,
  video_url VARCHAR(500) NOT NULL,
  video_provider ENUM('youtube', 'vimeo', 'aws', 'custom') DEFAULT 'custom',
  video_quality JSONB, -- {1080p: 'url', 720p: 'url', 480p: 'url'}
  thumbnail_url VARCHAR(500),
  captions_url VARCHAR(500),
  duration_seconds INT,
  file_size_mb DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Enrollments Table
```sql
CREATE TABLE enrollments (
  enrollment_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  course_id UUID REFERENCES courses(course_id) ON DELETE CASCADE,
  enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completion_date TIMESTAMP,
  progress_percentage DECIMAL(5,2) DEFAULT 0,
  last_accessed_at TIMESTAMP,
  status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
  payment_status ENUM('free', 'paid', 'refunded') DEFAULT 'free',
  certificate_issued BOOLEAN DEFAULT FALSE,
  UNIQUE(user_id, course_id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Video Progress Table
```sql
CREATE TABLE video_progress (
  progress_id UUID PRIMARY KEY,
  enrollment_id UUID REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
  lecture_id UUID REFERENCES lectures(lecture_id) ON DELETE CASCADE,
  watched_seconds INT DEFAULT 0,
  total_seconds INT,
  is_completed BOOLEAN DEFAULT FALSE,
  completion_percentage DECIMAL(5,2) DEFAULT 0,
  last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(enrollment_id, lecture_id),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Categories Table
```sql
CREATE TABLE categories (
  category_id UUID PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  description TEXT,
  icon VARCHAR(50),
  parent_category_id UUID REFERENCES categories(category_id),
  is_active BOOLEAN DEFAULT TRUE,
  display_order INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Authentication & Authorization APIs

### 2.1 User Registration
**Endpoint:** `POST /api/v1/auth/register`  
**Rate Limit:** 5 requests per hour per IP  
**Authentication:** Not required

#### Request Body
```json
{
  "email": "string (required, valid email)",
  "password": "string (required, min: 8, pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)",
  "firstName": "string (required, min: 2, max: 100)",
  "lastName": "string (required, min: 2, max: 100)",
  "agreeToTerms": "boolean (required, must be true)"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "email": "alex@example.com",
    "emailVerificationSent": true,
    "createdAt": "2026-01-20T10:00:00Z"
  }
}
```

---

### 2.2 Email Verification
**Endpoint:** `POST /api/v1/auth/verify-email`  
**Authentication:** Not required

#### Request Body
```json
{
  "token": "string (required, JWT verification token)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Email verified successfully",
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "verified": true,
    "verifiedAt": "2026-01-20T10:05:00Z"
  }
}
```

---

### 2.3 User Login
**Endpoint:** `POST /api/v1/auth/login`  
**Rate Limit:** 10 requests per hour per IP  
**Authentication:** Not required

#### Request Body
```json
{
  "email": "string (required)",
  "password": "string (required)",
  "rememberMe": "boolean (optional, default: false)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "Bearer",
    "expiresIn": 3600,
    "user": {
      "userId": "550e8400-e29b-41d4-a716-446655440000",
      "email": "alex@example.com",
      "role": "student",
      "displayName": "Alex Johnson",
      "avatarUrl": "https://cdn.example.com/avatars/550e8400.jpg"
    }
  }
}
```

---

### 2.4 Refresh Access Token
**Endpoint:** `POST /api/v1/auth/refresh`  
**Authentication:** Refresh token required

#### Request Body
```json
{
  "refreshToken": "string (required)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  }
}
```

---

### 2.5 Logout
**Endpoint:** `POST /api/v1/auth/logout`  
**Authentication:** Required

#### Request Body
```json
{
  "refreshToken": "string (required)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### 2.6 Password Reset Request
**Endpoint:** `POST /api/v1/auth/password-reset/request`  
**Rate Limit:** 3 requests per hour per email  
**Authentication:** Not required

#### Request Body
```json
{
  "email": "string (required)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Password reset email sent",
  "data": {
    "emailSent": true,
    "expiresIn": 3600
  }
}
```

---

### 2.7 Password Reset Confirm
**Endpoint:** `POST /api/v1/auth/password-reset/confirm`  
**Authentication:** Not required

#### Request Body
```json
{
  "token": "string (required)",
  "newPassword": "string (required, min: 8)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

---

## 3. User Management APIs

### 3.1 Get Current User Profile
**Endpoint:** `GET /api/v1/users/me`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "email": "alex@example.com",
    "role": "student",
    "emailVerified": true,
    "profile": {
      "firstName": "Alex",
      "lastName": "Johnson",
      "displayName": "Alex Johnson",
      "avatarUrl": "https://cdn.example.com/avatars/550e8400.jpg",
      "bio": "Frontend developer passionate about React...",
      "phone": "+1-555-123-4567",
      "location": "San Francisco, CA",
      "timezone": "America/Los_Angeles",
      "website": "https://alexjohnson.dev",
      "education": "B.S. Computer Science, Stanford University"
    },
    "stats": {
      "enrolledCoursesCount": 5,
      "completedCoursesCount": 2,
      "certificatesEarned": 2,
      "totalLearningMinutes": 1470
    },
    "memberSince": "2023-01-12T00:00:00Z",
    "lastLogin": "2026-01-20T09:00:00Z"
  }
}
```

---

### 3.2 Update User Profile
**Endpoint:** `PATCH /api/v1/users/me/profile`  
**Authentication:** Required

#### Request Body
```json
{
  "firstName": "string (optional)",
  "lastName": "string (optional)",
  "displayName": "string (optional)",
  "bio": "string (optional, max: 500)",
  "phone": "string (optional)",
  "location": "string (optional)",
  "timezone": "string (optional)",
  "website": "string (optional, valid URL)",
  "education": "string (optional)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "profileId": "650e8400-e29b-41d4-a716-446655440000",
    "updatedAt": "2026-01-20T10:30:00Z"
  }
}
```

---

### 3.3 Update Avatar
**Endpoint:** `POST /api/v1/users/me/avatar`  
**Authentication:** Required  
**Content-Type:** multipart/form-data

#### Request Body (Form Data)
```
avatar: File (required, max: 5MB, formats: jpg, jpeg, png, webp)
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "avatarUrl": "https://cdn.example.com/avatars/550e8400-1642671000.jpg",
    "uploadedAt": "2026-01-20T10:35:00Z"
  }
}
```

---

### 3.4 Get User Skills
**Endpoint:** `GET /api/v1/users/me/skills`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "skills": [
      {
        "skillId": "750e8400-e29b-41d4-a716-446655440000",
        "name": "JavaScript",
        "proficiency": "advanced",
        "addedAt": "2023-02-15T00:00:00Z"
      },
      {
        "skillId": "750e8400-e29b-41d4-a716-446655440001",
        "name": "React",
        "proficiency": "intermediate",
        "addedAt": "2023-03-20T00:00:00Z"
      }
    ]
  }
}
```

---

### 3.5 Add User Skill
**Endpoint:** `POST /api/v1/users/me/skills`  
**Authentication:** Required

#### Request Body
```json
{
  "name": "string (required)",
  "proficiency": "string (enum: ['beginner', 'intermediate', 'advanced'], optional)"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "skillId": "750e8400-e29b-41d4-a716-446655440002",
    "name": "TypeScript",
    "proficiency": "intermediate",
    "addedAt": "2026-01-20T10:40:00Z"
  }
}
```

---

### 3.6 Delete User Skill
**Endpoint:** `DELETE /api/v1/users/me/skills/{skillId}`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Skill removed successfully"
}
```

---

### 3.7 Get/Update Social Links
**Endpoint:** `GET /api/v1/users/me/social`  
**Endpoint:** `PUT /api/v1/users/me/social`  
**Authentication:** Required

#### Request Body (PUT)
```json
{
  "facebook": "string (optional, username only)",
  "twitter": "string (optional, username only)",
  "linkedin": "string (optional, username only)",
  "github": "string (optional, username only)",
  "instagram": "string (optional, username only)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "facebook": "alexjohnson",
    "twitter": "alexj_dev",
    "linkedin": "alexjohnson",
    "github": "alexj-dev",
    "instagram": "alex.codes",
    "updatedAt": "2026-01-20T10:45:00Z"
  }
}
```

---

### 3.8 Get/Update User Settings
**Endpoint:** `GET /api/v1/users/me/settings`  
**Endpoint:** `PATCH /api/v1/users/me/settings`  
**Authentication:** Required

#### Request Body (PATCH)
```json
{
  "notifications": {
    "emailCourseUpdates": "boolean",
    "emailAssignments": "boolean",
    "emailAnnouncements": "boolean",
    "emailWeeklyDigest": "boolean",
    "pushCourseUpdates": "boolean",
    "pushAssignments": "boolean",
    "pushAnnouncements": "boolean"
  },
  "privacy": {
    "profileVisibility": "string (enum: ['public', 'private', 'connections'])",
    "showEnrolledCourses": "boolean",
    "showProgress": "boolean"
  },
  "preferences": {
    "theme": "string (enum: ['light', 'dark', 'auto'])",
    "language": "string",
    "autoplayVideos": "boolean",
    "defaultPlaybackSpeed": "number (0.5, 0.75, 1, 1.25, 1.5, 2)",
    "captionsEnabled": "boolean"
  }
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "settingsId": "850e8400-e29b-41d4-a716-446655440000",
    "updatedAt": "2026-01-20T10:50:00Z"
  }
}
```

---

## 4. Course APIs

### 4.1 Get All Courses (Browse/Explore)
**Endpoint:** `GET /api/v1/courses`  
**Authentication:** Optional  
**Cache:** 5 minutes

#### Query Parameters
```
?page=number (default: 1)
&limit=number (default: 20, max: 100)
&categoryId=uuid
&level=string (Beginner|Intermediate|Advanced|All Levels)
&language=string
&minPrice=number
&maxPrice=number
&isFree=boolean
&isFeatured=boolean
&isBestseller=boolean
&rating=number (min rating)
&search=string (min: 2 chars)
&sortBy=string (popularity|rating|price|recent|title)
&sortOrder=string (asc|desc, default: desc)
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "courses": [
      {
        "courseId": "450e8400-e29b-41d4-a716-446655440000",
        "courseCode": "VA01",
        "title": "Vedic Astrology: Complete Chart Analysis",
        "slug": "vedic-astrology-complete-chart-analysis",
        "shortDescription": "Master the art of Vedic astrology...",
        "level": "All Levels",
        "language": "English",
        "thumbnailUrl": "https://cdn.example.com/courses/va01.jpg",
        "category": {
          "categoryId": "350e8400-e29b-41d4-a716-446655440000",
          "name": "Vedic Astrology",
          "slug": "vedic-astrology"
        },
        "pricing": {
          "price": 149.99,
          "salePrice": 99.99,
          "currency": "USD",
          "isFree": false
        },
        "metadata": {
          "durationMinutes": 1125,
          "totalLectures": 42,
          "totalSections": 5,
          "avgRating": 4.9,
          "totalReviews": 342,
          "totalEnrollments": 1486,
          "isFeatured": true,
          "isBestseller": true
        },
        "instructors": [
          {
            "instructorId": "250e8400-e29b-41d4-a716-446655440000",
            "name": "Mridul",
            "title": "Jyotish Acharya & Vedic Scholar",
            "avatarUrl": "https://cdn.example.com/instructors/mridul.jpg"
          }
        ],
        "publishedAt": "2026-01-15T08:00:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalItems": 98,
      "itemsPerPage": 20,
      "hasNextPage": true,
      "hasPrevPage": false
    }
  }
}
```

---

### 4.2 Get Course by ID
**Endpoint:** `GET /api/v1/courses/{courseId}`  
**Authentication:** Optional (required for full access to private courses)  
**Cache:** 5 minutes

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "courseCode": "VA01",
    "title": "Vedic Astrology: Complete Chart Analysis",
    "slug": "vedic-astrology-complete-chart-analysis",
    "shortDescription": "Master the art of Vedic astrology...",
    "description": "This comprehensive course takes you from fundamentals...",
    "level": "All Levels",
    "language": "English",
    "status": "published",
    "thumbnailUrl": "https://cdn.example.com/courses/va01.jpg",
    "promoVideoUrl": "https://cdn.example.com/promos/va01.mp4",
    "category": {
      "categoryId": "350e8400-e29b-41d4-a716-446655440000",
      "name": "Vedic Astrology",
      "slug": "vedic-astrology"
    },
    "pricing": {
      "pricingId": "950e8400-e29b-41d4-a716-446655440000",
      "price": 149.99,
      "salePrice": 99.99,
      "currency": "USD",
      "isFree": false,
      "saleEndDate": "2026-01-31T23:59:59Z"
    },
    "metadata": {
      "durationMinutes": 1125,
      "totalLectures": 42,
      "totalSections": 5,
      "avgRating": 4.9,
      "totalReviews": 342,
      "totalEnrollments": 1486,
      "isFeatured": true,
      "isBestseller": true,
      "hasCertificate": true,
      "commentsEnabled": true,
      "dripContent": false
    },
    "instructors": [
      {
        "instructorId": "250e8400-e29b-41d4-a716-446655440000",
        "name": "Mridul",
        "title": "Jyotish Acharya & Vedic Scholar",
        "bio": "With over 20 years of experience...",
        "avatarUrl": "https://cdn.example.com/instructors/mridul.jpg",
        "totalStudents": 15430,
        "totalCourses": 8,
        "avgRating": 4.8
      }
    ],
    "tags": ["astrology", "vedic", "spirituality", "chart-reading"],
    "createdAt": "2026-01-10T08:00:00Z",
    "updatedAt": "2026-01-20T11:45:00Z",
    "publishedAt": "2026-01-15T08:00:00Z"
  }
}
```

---

### 4.3 Get Course Learning Objectives
**Endpoint:** `GET /api/v1/courses/{courseId}/learning-objectives`  
**Authentication:** Optional

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "objectives": [
      {
        "objectiveId": "a50e8400-e29b-41d4-a716-446655440000",
        "text": "Create and interpret Vedic birth charts with confidence",
        "orderIndex": 1
      },
      {
        "objectiveId": "a50e8400-e29b-41d4-a716-446655440001",
        "text": "Understand the influence of planets, houses, and signs",
        "orderIndex": 2
      }
    ]
  }
}
```

---

### 4.4 Get Course Requirements
**Endpoint:** `GET /api/v1/courses/{courseId}/requirements`  
**Authentication:** Optional

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "requirements": [
      {
        "requirementId": "b50e8400-e29b-41d4-a716-446655440000",
        "text": "No prior knowledge of astrology is required",
        "orderIndex": 1
      },
      {
        "requirementId": "b50e8400-e29b-41d4-a716-446655440001",
        "text": "A computer with internet access",
        "orderIndex": 2
      }
    ]
  }
}
```

---

### 4.5 Get Course Target Audience
**Endpoint:** `GET /api/v1/courses/{courseId}/target-audience`  
**Authentication:** Optional

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "targetAudience": [
      {
        "audienceId": "c50e8400-e29b-41d4-a716-446655440000",
        "text": "Anyone interested in learning Vedic astrology",
        "orderIndex": 1
      }
    ]
  }
}
```

---

### 4.6 Create Course (Admin/Instructor)
**Endpoint:** `POST /api/v1/courses`  
**Authentication:** Required (instructor/admin role)

#### Request Body
```json
{
  "courseCode": "string (optional, auto-generated if not provided)",
  "title": "string (required, max: 255)",
  "shortDescription": "string (required, max: 500)",
  "description": "string (required)",
  "level": "string (enum: ['Beginner', 'Intermediate', 'Advanced', 'All Levels'])",
  "language": "string (default: 'English')",
  "categoryId": "uuid (required)",
  "status": "string (enum: ['draft', 'published'], default: 'draft')"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "courseCode": "VA01",
    "slug": "vedic-astrology-complete-chart-analysis",
    "status": "draft",
    "createdAt": "2026-01-20T11:00:00Z"
  }
}
```

---

### 4.7 Update Course
**Endpoint:** `PATCH /api/v1/courses/{courseId}`  
**Authentication:** Required (instructor/admin role)

#### Request Body
Same as Create Course, all fields optional

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Course updated successfully",
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "updatedAt": "2026-01-20T11:05:00Z"
  }
}
```

---

### 4.8 Delete Course
**Endpoint:** `DELETE /api/v1/courses/{courseId}`  
**Authentication:** Required (admin role)

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Course deleted successfully"
}
```

---

### 4.9 Update Course Pricing
**Endpoint:** `PUT /api/v1/courses/{courseId}/pricing`  
**Authentication:** Required (instructor/admin role)

#### Request Body
```json
{
  "price": "number (required, min: 0)",
  "salePrice": "number (optional, min: 0, must be < price)",
  "currency": "string (default: 'USD')",
  "isFree": "boolean (default: false)",
  "saleStartDate": "string (ISO 8601, optional)",
  "saleEndDate": "string (ISO 8601, optional)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "pricingId": "950e8400-e29b-41d4-a716-446655440000",
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "price": 149.99,
    "salePrice": 99.99,
    "updatedAt": "2026-01-20T11:10:00Z"
  }
}
```

---

### 4.10 Update Course Metadata
**Endpoint:** `PATCH /api/v1/courses/{courseId}/metadata`  
**Authentication:** Required (instructor/admin role)

#### Request Body
```json
{
  "isFeatured": "boolean (optional)",
  "isBestseller": "boolean (optional)",
  "hasCertificate": "boolean (optional)",
  "dripContent": "boolean (optional)",
  "commentsEnabled": "boolean (optional)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Course metadata updated successfully"
}
```

---

## 5. Enrollment APIs

### 5.1 Enroll in Course
**Endpoint:** `POST /api/v1/enrollments`  
**Authentication:** Required

#### Request Body
```json
{
  "courseId": "uuid (required)",
  "paymentMethod": "string (enum: ['free', 'card', 'paypal'], optional)",
  "transactionId": "string (conditional: required if paymentMethod != 'free')"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "enrollmentDate": "2026-01-20T11:15:00Z",
    "status": "active",
    "paymentStatus": "paid",
    "progressPercentage": 0
  }
}
```

---

### 5.2 Get User Enrollments
**Endpoint:** `GET /api/v1/users/me/enrollments`  
**Authentication:** Required

#### Query Parameters
```
?status=string (active|completed|cancelled)
&page=number
&limit=number
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "enrollments": [
      {
        "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
        "course": {
          "courseId": "450e8400-e29b-41d4-a716-446655440000",
          "title": "Vedic Astrology: Complete Chart Analysis",
          "thumbnailUrl": "https://cdn.example.com/courses/va01.jpg",
          "instructors": [
            {
              "name": "Mridul",
              "avatarUrl": "https://cdn.example.com/instructors/mridul.jpg"
            }
          ]
        },
        "enrollmentDate": "2026-01-10T08:00:00Z",
        "lastAccessedAt": "2026-01-20T09:30:00Z",
        "progressPercentage": 35,
        "status": "active",
        "certificateIssued": false
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 1,
      "totalItems": 5
    }
  }
}
```

---

### 5.3 Get Enrollment Details
**Endpoint:** `GET /api/v1/enrollments/{enrollmentId}`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "enrollmentDate": "2026-01-10T08:00:00Z",
    "completionDate": null,
    "lastAccessedAt": "2026-01-20T09:30:00Z",
    "progressPercentage": 35,
    "status": "active",
    "paymentStatus": "paid",
    "certificateIssued": false,
    "stats": {
      "totalLectures": 42,
      "completedLectures": 15,
      "totalQuizzes": 10,
      "completedQuizzes": 5,
      "timeSpentMinutes": 485
    }
  }
}
```

---

### 5.4 Unenroll from Course
**Endpoint:** `DELETE /api/v1/enrollments/{enrollmentId}`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Unenrolled successfully",
  "data": {
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "status": "cancelled",
    "cancelledAt": "2026-01-20T11:20:00Z"
  }
}
```

---

## 6. Learning Progress APIs

### 6.1 Get Course Progress
**Endpoint:** `GET /api/v1/enrollments/{enrollmentId}/progress`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "progressPercentage": 35,
    "sections": [
      {
        "sectionId": "850e8400-e29b-41d4-a716-446655440000",
        "title": "Introduction to Vedic Astrology",
        "completedLectures": 4,
        "totalLectures": 5,
        "progressPercentage": 80
      },
      {
        "sectionId": "850e8400-e29b-41d4-a716-446655440001",
        "title": "Understanding the Birth Chart",
        "completedLectures": 2,
        "totalLectures": 5,
        "progressPercentage": 40
      }
    ],
    "currentSection": {
      "sectionId": "850e8400-e29b-41d4-a716-446655440001",
      "title": "Understanding the Birth Chart"
    },
    "nextLecture": {
      "lectureId": "750e8400-e29b-41d4-a716-446655440008",
      "title": "Planetary Positions and Their Meaning",
      "estimatedDuration": 2535
    }
  }
}
```

---

### 6.2 Update Video Progress
**Endpoint:** `POST /api/v1/enrollments/{enrollmentId}/video-progress`  
**Authentication:** Required

#### Request Body
```json
{
  "lectureId": "uuid (required)",
  "watchedSeconds": "number (required, min: 0)",
  "totalSeconds": "number (required, min: 0)",
  "isCompleted": "boolean (optional, auto-calculated if watchedSeconds >= 90% of totalSeconds)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "progressId": "050e8400-e29b-41d4-a716-446655440000",
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "lectureId": "750e8400-e29b-41d4-a716-446655440008",
    "watchedSeconds": 1200,
    "totalSeconds": 2535,
    "completionPercentage": 47.34,
    "isCompleted": false,
    "courseProgressPercentage": 36,
    "updatedAt": "2026-01-20T11:25:00Z"
  }
}
```

---

### 6.3 Get Video Progress for Lecture
**Endpoint:** `GET /api/v1/enrollments/{enrollmentId}/video-progress/{lectureId}`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "progressId": "050e8400-e29b-41d4-a716-446655440000",
    "lectureId": "750e8400-e29b-41d4-a716-446655440008",
    "watchedSeconds": 1200,
    "totalSeconds": 2535,
    "completionPercentage": 47.34,
    "isCompleted": false,
    "lastWatchedAt": "2026-01-20T11:25:00Z"
  }
}
```

---

### 6.4 Mark Lecture as Complete
**Endpoint:** `POST /api/v1/enrollments/{enrollmentId}/lectures/{lectureId}/complete`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Lecture marked as complete",
  "data": {
    "lectureId": "750e8400-e29b-41d4-a716-446655440008",
    "isCompleted": true,
    "completedAt": "2026-01-20T11:30:00Z",
    "courseProgressPercentage": 38
  }
}
```

---

## 7. Assessment APIs

### 7.1 Get Course Assignments
**Endpoint:** `GET /api/v1/courses/{courseId}/assignments`  
**Authentication:** Required (enrolled users)

#### Query Parameters
```
?status=string (pending|submitted|graded|overdue)
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "assignments": [
      {
        "assignmentId": "d50e8400-e29b-41d4-a716-446655440000",
        "title": "Birth Chart Analysis Project",
        "description": "Analyze a provided birth chart...",
        "instructions": "Detailed step-by-step instructions...",
        "maxScore": 100,
        "dueDate": "2026-01-25T23:59:59Z",
        "createdAt": "2026-01-10T10:00:00Z",
        "status": "pending",
        "submission": null
      },
      {
        "assignmentId": "d50e8400-e29b-41d4-a716-446655440001",
        "title": "Introduction Quiz",
        "description": "Test your knowledge...",
        "maxScore": 100,
        "dueDate": "2026-01-14T23:59:59Z",
        "createdAt": "2026-01-10T10:00:00Z",
        "status": "graded",
        "submission": {
          "submissionId": "e50e8400-e29b-41d4-a716-446655440000",
          "submittedAt": "2026-01-14T15:00:00Z",
          "score": 95,
          "grade": "A",
          "feedback": "Excellent work!"
        }
      }
    ]
  }
}
```

---

### 7.2 Get Assignment Details
**Endpoint:** `GET /api/v1/assignments/{assignmentId}`  
**Authentication:** Required (enrolled users)

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "assignmentId": "d50e8400-e29b-41d4-a716-446655440000",
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "title": "Birth Chart Analysis Project",
    "description": "Analyze a provided birth chart and identify key planetary positions...",
    "instructions": "1. Download the sample chart\n2. Identify all planetary positions...",
    "maxScore": 100,
    "dueDate": "2026-01-25T23:59:59Z",
    "allowLateSubmission": true,
    "lateSubmissionPenalty": 10,
    "resources": [
      {
        "resourceId": "f50e8400-e29b-41d4-a716-446655440000",
        "name": "Sample Birth Chart",
        "type": "pdf",
        "url": "https://cdn.example.com/resources/sample-chart.pdf"
      }
    ],
    "createdAt": "2026-01-10T10:00:00Z"
  }
}
```

---

### 7.3 Submit Assignment
**Endpoint:** `POST /api/v1/assignments/{assignmentId}/submissions`  
**Authentication:** Required  
**Content-Type:** multipart/form-data

#### Request Body (Form Data)
```
enrollmentId: uuid (required)
file: File (optional, max: 10MB, formats: pdf, doc, docx, txt)
textAnswer: string (optional, max: 5000)
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "submissionId": "e50e8400-e29b-41d4-a716-446655440001",
    "assignmentId": "d50e8400-e29b-41d4-a716-446655440000",
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "submittedAt": "2026-01-20T11:35:00Z",
    "fileUrl": "https://cdn.example.com/submissions/e50e8400.pdf",
    "status": "submitted",
    "isLate": false
  }
}
```

---

### 7.4 Get Quiz Questions
**Endpoint:** `GET /api/v1/quizzes/{quizId}/questions`  
**Authentication:** Required (enrolled users)

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "quizId": "c50e8400-e29b-41d4-a716-446655440000",
    "title": "Fundamental Concepts Quiz",
    "description": "Test your understanding of basic concepts",
    "timeLimit": 600,
    "totalQuestions": 10,
    "passingScore": 70,
    "maxAttempts": 3,
    "questions": [
      {
        "questionId": "g50e8400-e29b-41d4-a716-446655440000",
        "questionText": "What is the primary difference between Vedic and Western astrology?",
        "type": "multiple_choice",
        "points": 10,
        "orderIndex": 1,
        "options": [
          {
            "optionId": "h50e8400-e29b-41d4-a716-446655440000",
            "text": "Zodiac system used",
            "orderIndex": 1
          },
          {
            "optionId": "h50e8400-e29b-41d4-a716-446655440001",
            "text": "Number of planets",
            "orderIndex": 2
          }
        ]
      }
    ]
  }
}
```

---

### 7.5 Submit Quiz
**Endpoint:** `POST /api/v1/quizzes/{quizId}/attempts`  
**Authentication:** Required

#### Request Body
```json
{
  "enrollmentId": "uuid (required)",
  "answers": [
    {
      "questionId": "uuid (required)",
      "selectedOptionId": "uuid (required for multiple_choice)",
      "textAnswer": "string (required for text_answer)"
    }
  ],
  "timeTaken": "number (seconds)"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "attemptId": "i50e8400-e29b-41d4-a716-446655440000",
    "quizId": "c50e8400-e29b-41d4-a716-446655440000",
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "score": 80,
    "totalPoints": 100,
    "percentage": 80,
    "passed": true,
    "passingScore": 70,
    "attemptNumber": 1,
    "timeTaken": 420,
    "submittedAt": "2026-01-20T11:40:00Z",
    "answers": [
      {
        "questionId": "g50e8400-e29b-41d4-a716-446655440000",
        "isCorrect": true,
        "selectedOptionId": "h50e8400-e29b-41d4-a716-446655440000",
        "correctOptionId": "h50e8400-e29b-41d4-a716-446655440000",
        "pointsEarned": 10,
        "explanation": "Vedic astrology uses the sidereal zodiac..."
      }
    ],
    "canRetake": true,
    "attemptsRemaining": 2
  }
}
```

---

### 7.6 Get Quiz Attempts History
**Endpoint:** `GET /api/v1/quizzes/{quizId}/attempts`  
**Authentication:** Required

#### Query Parameters
```
?enrollmentId=uuid (required)
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "quizId": "c50e8400-e29b-41d4-a716-446655440000",
    "attempts": [
      {
        "attemptId": "i50e8400-e29b-41d4-a716-446655440000",
        "attemptNumber": 1,
        "score": 80,
        "percentage": 80,
        "passed": true,
        "submittedAt": "2026-01-20T11:40:00Z"
      }
    ],
    "bestScore": 80,
    "totalAttempts": 1,
    "maxAttempts": 3
  }
}
```

---

## 8. Content Management APIs

### 8.1 Get Course Sections
**Endpoint:** `GET /api/v1/courses/{courseId}/sections`  
**Authentication:** Optional (enrolled users see full content)

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "sections": [
      {
        "sectionId": "850e8400-e29b-41d4-a716-446655440000",
        "title": "Introduction to Vedic Astrology",
        "description": "Learn the fundamentals...",
        "orderIndex": 1,
        "totalLectures": 5,
        "totalDuration": 3600,
        "isPublished": true
      },
      {
        "sectionId": "850e8400-e29b-41d4-a716-446655440001",
        "title": "Understanding the Birth Chart",
        "description": "Deep dive into chart analysis...",
        "orderIndex": 2,
        "totalLectures": 5,
        "totalDuration": 7200,
        "isPublished": true
      }
    ]
  }
}
```

---

### 8.2 Get Section Lectures
**Endpoint:** `GET /api/v1/sections/{sectionId}/lectures`  
**Authentication:** Optional (enrolled users see full content)

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "sectionId": "850e8400-e29b-41d4-a716-446655440000",
    "lectures": [
      {
        "lectureId": "750e8400-e29b-41d4-a716-446655440000",
        "title": "Course Overview",
        "description": "Introduction to the course structure",
        "contentType": "video",
        "durationSeconds": 615,
        "orderIndex": 1,
        "isPreview": true,
        "isPublished": true
      },
      {
        "lectureId": "750e8400-e29b-41d4-a716-446655440001",
        "title": "History of Jyotisha",
        "description": "Learn about the origins...",
        "contentType": "video",
        "durationSeconds": 1110,
        "orderIndex": 2,
        "isPreview": false,
        "isPublished": true
      }
    ]
  }
}
```

---

### 8.3 Get Lecture Content
**Endpoint:** `GET /api/v1/lectures/{lectureId}/content`  
**Authentication:** Required (enrolled users or preview lectures)

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "lectureId": "750e8400-e29b-41d4-a716-446655440000",
    "contentType": "video",
    "video": {
      "videoId": "j50e8400-e29b-41d4-a716-446655440000",
      "videoUrl": "https://cdn.example.com/videos/lecture-001.mp4",
      "provider": "custom",
      "qualities": {
        "1080p": "https://cdn.example.com/videos/lecture-001-1080p.mp4",
        "720p": "https://cdn.example.com/videos/lecture-001-720p.mp4",
        "480p": "https://cdn.example.com/videos/lecture-001-480p.mp4"
      },
      "thumbnailUrl": "https://cdn.example.com/thumbnails/lecture-001.jpg",
      "captionsUrl": "https://cdn.example.com/captions/lecture-001.vtt",
      "durationSeconds": 615
    }
  }
}
```

---

### 8.4 Create Section (Admin/Instructor)
**Endpoint:** `POST /api/v1/courses/{courseId}/sections`  
**Authentication:** Required (instructor/admin role)

#### Request Body
```json
{
  "title": "string (required, max: 255)",
  "description": "string (optional)",
  "orderIndex": "number (required)"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "sectionId": "850e8400-e29b-41d4-a716-446655440002",
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "title": "Advanced Techniques",
    "orderIndex": 3,
    "createdAt": "2026-01-20T11:45:00Z"
  }
}
```

---

### 8.5 Update Section
**Endpoint:** `PATCH /api/v1/sections/{sectionId}`  
**Authentication:** Required (instructor/admin role)

#### Request Body
```json
{
  "title": "string (optional)",
  "description": "string (optional)",
  "orderIndex": "number (optional)",
  "isPublished": "boolean (optional)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Section updated successfully"
}
```

---

### 8.6 Delete Section
**Endpoint:** `DELETE /api/v1/sections/{sectionId}`  
**Authentication:** Required (instructor/admin role)

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Section deleted successfully"
}
```

---

### 8.7 Create Lecture
**Endpoint:** `POST /api/v1/sections/{sectionId}/lectures`  
**Authentication:** Required (instructor/admin role)

#### Request Body
```json
{
  "title": "string (required, max: 255)",
  "description": "string (optional)",
  "contentType": "string (enum: ['video', 'pdf', 'quiz', 'text'])",
  "durationSeconds": "number (optional)",
  "orderIndex": "number (required)",
  "isPreview": "boolean (default: false)"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "lectureId": "750e8400-e29b-41d4-a716-446655440010",
    "sectionId": "850e8400-e29b-41d4-a716-446655440000",
    "title": "New Lecture",
    "contentType": "video",
    "orderIndex": 6,
    "createdAt": "2026-01-20T11:50:00Z"
  }
}
```

---

### 8.8 Update Lecture
**Endpoint:** `PATCH /api/v1/lectures/{lectureId}`  
**Authentication:** Required (instructor/admin role)

#### Request Body
Same as Create Lecture, all fields optional

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Lecture updated successfully"
}
```

---

### 8.9 Delete Lecture
**Endpoint:** `DELETE /api/v1/lectures/{lectureId}`  
**Authentication:** Required (instructor/admin role)

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Lecture deleted successfully"
}
```

---

## 9. Social & Interaction APIs

### 9.1 Get Course Reviews
**Endpoint:** `GET /api/v1/courses/{courseId}/reviews`  
**Authentication:** Optional

#### Query Parameters
```
?page=number
&limit=number
&rating=number (filter by specific rating)
&sortBy=string (recent|helpful|rating)
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "summary": {
      "avgRating": 4.9,
      "totalReviews": 342,
      "ratingDistribution": {
        "5": 280,
        "4": 45,
        "3": 12,
        "2": 3,
        "1": 2
      }
    },
    "reviews": [
      {
        "reviewId": "k50e8400-e29b-41d4-a716-446655440000",
        "user": {
          "userId": "550e8400-e29b-41d4-a716-446655440001",
          "displayName": "Sarah Mitchell",
          "avatarUrl": "https://cdn.example.com/avatars/550e8400.jpg"
        },
        "rating": 5,
        "title": "Excellent Course!",
        "comment": "As someone coming from Western astrology...",
        "helpfulCount": 24,
        "isVerifiedPurchase": true,
        "createdAt": "2026-01-15T14:30:00Z",
        "updatedAt": "2026-01-15T14:30:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 35,
      "totalItems": 342
    }
  }
}
```

---

### 9.2 Create Course Review
**Endpoint:** `POST /api/v1/courses/{courseId}/reviews`  
**Authentication:** Required (enrolled users only)

#### Request Body
```json
{
  "rating": "number (required, min: 1, max: 5)",
  "title": "string (optional, max: 100)",
  "comment": "string (required, min: 50, max: 1000)"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "reviewId": "k50e8400-e29b-41d4-a716-446655440001",
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "rating": 5,
    "title": "Great learning experience",
    "comment": "This course exceeded my expectations...",
    "createdAt": "2026-01-20T12:00:00Z"
  }
}
```

---

### 9.3 Update Review
**Endpoint:** `PATCH /api/v1/reviews/{reviewId}`  
**Authentication:** Required (review author only)

#### Request Body
```json
{
  "rating": "number (optional)",
  "title": "string (optional)",
  "comment": "string (optional)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Review updated successfully"
}
```

---

### 9.4 Delete Review
**Endpoint:** `DELETE /api/v1/reviews/{reviewId}`  
**Authentication:** Required (review author or admin)

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Review deleted successfully"
}
```

---

### 9.5 Mark Review as Helpful
**Endpoint:** `POST /api/v1/reviews/{reviewId}/helpful`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "reviewId": "k50e8400-e29b-41d4-a716-446655440000",
    "helpfulCount": 25
  }
}
```

---

### 9.6 Add/Update Bookmark
**Endpoint:** `POST /api/v1/enrollments/{enrollmentId}/bookmarks`  
**Authentication:** Required

#### Request Body
```json
{
  "lectureId": "uuid (required)",
  "timestamp": "number (required, seconds)",
  "note": "string (optional, max: 500)"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "bookmarkId": "l50e8400-e29b-41d4-a716-446655440000",
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "lectureId": "750e8400-e29b-41d4-a716-446655440005",
    "timestamp": 180,
    "note": "Important concept about planetary aspects",
    "createdAt": "2026-01-20T12:05:00Z"
  }
}
```

---

### 9.7 Get Bookmarks
**Endpoint:** `GET /api/v1/enrollments/{enrollmentId}/bookmarks`  
**Authentication:** Required

#### Query Parameters
```
?lectureId=uuid (optional, filter by lecture)
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "bookmarks": [
      {
        "bookmarkId": "l50e8400-e29b-41d4-a716-446655440000",
        "lecture": {
          "lectureId": "750e8400-e29b-41d4-a716-446655440005",
          "title": "Planetary Aspects",
          "sectionTitle": "Understanding the Birth Chart"
        },
        "timestamp": 180,
        "note": "Important concept",
        "createdAt": "2026-01-20T12:05:00Z"
      }
    ]
  }
}
```

---

### 9.8 Delete Bookmark
**Endpoint:** `DELETE /api/v1/bookmarks/{bookmarkId}`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Bookmark deleted successfully"
}
```

---

### 9.9 Add/Update Note
**Endpoint:** `POST /api/v1/enrollments/{enrollmentId}/notes`  
**Authentication:** Required

#### Request Body
```json
{
  "lectureId": "uuid (required)",
  "content": "string (required, max: 2000)"
}
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "noteId": "m50e8400-e29b-41d4-a716-446655440000",
    "enrollmentId": "150e8400-e29b-41d4-a716-446655440000",
    "lectureId": "750e8400-e29b-41d4-a716-446655440003",
    "content": "Key points about birth chart interpretation...",
    "createdAt": "2026-01-20T12:10:00Z"
  }
}
```

---

### 9.10 Get Notes
**Endpoint:** `GET /api/v1/enrollments/{enrollmentId}/notes`  
**Authentication:** Required

#### Query Parameters
```
?lectureId=uuid (optional)
&search=string (optional)
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "notes": [
      {
        "noteId": "m50e8400-e29b-41d4-a716-446655440000",
        "lecture": {
          "lectureId": "750e8400-e29b-41d4-a716-446655440003",
          "title": "Creating a Birth Chart",
          "sectionTitle": "Understanding the Birth Chart"
        },
        "content": "Key points about...",
        "createdAt": "2026-01-20T12:10:00Z",
        "updatedAt": "2026-01-20T12:10:00Z"
      }
    ]
  }
}
```

---

### 9.11 Update Note
**Endpoint:** `PATCH /api/v1/notes/{noteId}`  
**Authentication:** Required

#### Request Body
```json
{
  "content": "string (required, max: 2000)"
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Note updated successfully"
}
```

---

### 9.12 Delete Note
**Endpoint:** `DELETE /api/v1/notes/{noteId}`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Note deleted successfully"
}
```

---

## 10. Analytics & Reporting APIs

### 10.1 Get Student Dashboard
**Endpoint:** `GET /api/v1/users/me/dashboard`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "stats": {
      "enrolledCoursesCount": 5,
      "inProgressCoursesCount": 3,
      "completedCoursesCount": 2,
      "totalLearningMinutes": 1470,
      "certificatesEarned": 2,
      "currentStreak": 7,
      "longestStreak": 15
    },
    "recentActivity": [
      {
        "activityId": "n50e8400-e29b-41d4-a716-446655440000",
        "type": "video_completed",
        "course": {
          "courseId": "450e8400-e29b-41d4-a716-446655440000",
          "title": "Vedic Astrology"
        },
        "lecture": {
          "lectureId": "750e8400-e29b-41d4-a716-446655440002",
          "title": "History of Jyotisha"
        },
        "timestamp": "2026-01-20T09:30:00Z"
      },
      {
        "activityId": "n50e8400-e29b-41d4-a716-446655440001",
        "type": "quiz_passed",
        "course": {
          "courseId": "450e8400-e29b-41d4-a716-446655440000",
          "title": "Vedic Astrology"
        },
        "quiz": {
          "quizId": "c50e8400-e29b-41d4-a716-446655440000",
          "title": "Fundamental Concepts Quiz"
        },
        "score": 80,
        "timestamp": "2026-01-19T15:00:00Z"
      }
    ],
    "upcomingDeadlines": [
      {
        "type": "assignment",
        "assignmentId": "d50e8400-e29b-41d4-a716-446655440000",
        "title": "Birth Chart Analysis Project",
        "course": {
          "courseId": "450e8400-e29b-41d4-a716-446655440000",
          "title": "Vedic Astrology"
        },
        "dueDate": "2026-01-25T23:59:59Z",
        "status": "pending"
      }
    ],
    "recommendedCourses": [
      {
        "courseId": "450e8400-e29b-41d4-a716-446655440001",
        "title": "Advanced Numerology",
        "reason": "Based on your interest in Vedic Astrology"
      }
    ]
  }
}
```

---

### 10.2 Get Learning Analytics
**Endpoint:** `GET /api/v1/users/me/analytics`  
**Authentication:** Required

#### Query Parameters
```
?period=string (week|month|year|all)
&courseId=uuid (optional)
```

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "period": "month",
    "learningTime": {
      "totalMinutes": 420,
      "byDay": [
        {
          "date": "2026-01-20",
          "minutes": 45
        },
        {
          "date": "2026-01-19",
          "minutes": 60
        }
      ]
    },
    "coursesProgress": [
      {
        "courseId": "450e8400-e29b-41d4-a716-446655440000",
        "courseTitle": "Vedic Astrology",
        "progressPercentage": 35,
        "minutesSpent": 485,
        "lecturesCompleted": 15,
        "quizzesCompleted": 5
      }
    ],
    "achievements": [
      {
        "achievementId": "o50e8400-e29b-41d4-a716-446655440000",
        "title": "Week Streak",
        "description": "7 days learning streak",
        "earnedAt": "2026-01-20T00:00:00Z"
      }
    ]
  }
}
```

---

### 10.3 Get Instructor Dashboard (Instructor/Admin)
**Endpoint:** `GET /api/v1/instructors/me/dashboard`  
**Authentication:** Required (instructor/admin role)

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "stats": {
      "totalCourses": 8,
      "totalStudents": 15430,
      "totalRevenue": 234500.50,
      "avgRating": 4.8,
      "totalReviews": 2145
    },
    "recentEnrollments": [
      {
        "enrollmentId": "150e8400-e29b-41d4-a716-446655440010",
        "student": {
          "userId": "550e8400-e29b-41d4-a716-446655440010",
          "displayName": "John Doe"
        },
        "course": {
          "courseId": "450e8400-e29b-41d4-a716-446655440000",
          "title": "Vedic Astrology"
        },
        "enrolledAt": "2026-01-20T11:00:00Z"
      }
    ],
    "pendingReviews": {
      "assignments": 12,
      "questions": 5
    }
  }
}
```

---

### 10.4 Get Course Analytics (Instructor/Admin)
**Endpoint:** `GET /api/v1/courses/{courseId}/analytics`  
**Authentication:** Required (instructor/admin role)

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "courseId": "450e8400-e29b-41d4-a716-446655440000",
    "enrollments": {
      "total": 1486,
      "active": 1243,
      "completed": 243,
      "byMonth": [
        {
          "month": "2026-01",
          "count": 145
        }
      ]
    },
    "revenue": {
      "total": 147614.00,
      "byMonth": [
        {
          "month": "2026-01",
          "amount": 14385.00
        }
      ]
    },
    "engagement": {
      "avgCompletionRate": 68,
      "avgTimeSpent": 892,
      "dropoffPoints": [
        {
          "sectionId": "850e8400-e29b-41d4-a716-446655440002",
          "sectionTitle": "Planetary Combinations",
          "dropoffRate": 15
        }
      ]
    },
    "reviews": {
      "avgRating": 4.9,
      "total": 342,
      "recent": [
        {
          "reviewId": "k50e8400-e29b-41d4-a716-446655440000",
          "rating": 5,
          "comment": "Excellent course...",
          "createdAt": "2026-01-20T10:00:00Z"
        }
      ]
    }
  }
}
```

---

## 11. Media & File Management APIs

### 11.1 Upload Video
**Endpoint:** `POST /api/v1/media/videos`  
**Authentication:** Required (instructor/admin role)  
**Content-Type:** multipart/form-data

#### Request Body (Form Data)
```
video: File (required, max: 500MB, formats: mp4, webm, mov)
title: string (optional)
quality: string (optional, auto-detect if not provided)
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "videoId": "j50e8400-e29b-41d4-a716-446655440001",
    "videoUrl": "https://cdn.example.com/videos/j50e8400.mp4",
    "thumbnailUrl": "https://cdn.example.com/thumbnails/j50e8400.jpg",
    "durationSeconds": 1234,
    "fileSizeMb": 145.5,
    "status": "processing",
    "uploadedAt": "2026-01-20T12:15:00Z"
  }
}
```

---

### 11.2 Upload PDF
**Endpoint:** `POST /api/v1/media/pdfs`  
**Authentication:** Required (instructor/admin role)  
**Content-Type:** multipart/form-data

#### Request Body (Form Data)
```
pdf: File (required, max: 50MB, format: pdf)
title: string (optional)
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "pdfId": "p50e8400-e29b-41d4-a716-446655440000",
    "pdfUrl": "https://cdn.example.com/pdfs/p50e8400.pdf",
    "fileSizeMb": 5.2,
    "uploadedAt": "2026-01-20T12:20:00Z"
  }
}
```

---

### 11.3 Upload Image
**Endpoint:** `POST /api/v1/media/images`  
**Authentication:** Required  
**Content-Type:** multipart/form-data

#### Request Body (Form Data)
```
image: File (required, max: 5MB, formats: jpg, jpeg, png, webp)
type: string (enum: ['avatar', 'thumbnail', 'general'])
```

#### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "imageId": "q50e8400-e29b-41d4-a716-446655440000",
    "imageUrl": "https://cdn.example.com/images/q50e8400.jpg",
    "thumbnailUrl": "https://cdn.example.com/thumbnails/q50e8400-thumb.jpg",
    "fileSizeMb": 1.2,
    "uploadedAt": "2026-01-20T12:25:00Z"
  }
}
```

---

### 11.4 Get Upload Status
**Endpoint:** `GET /api/v1/media/uploads/{uploadId}/status`  
**Authentication:** Required

#### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "uploadId": "j50e8400-e29b-41d4-a716-446655440001",
    "status": "completed",
    "progress": 100,
    "fileUrl": "https://cdn.example.com/videos/j50e8400.mp4",
    "processedAt": "2026-01-20T12:18:00Z"
  }
}
```

---

## 12. Error Handling & Conventions

### 12.1 Standard Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": [
      {
        "field": "fieldName",
        "message": "Specific validation error",
        "value": "invalidValue"
      }
    ],
    "requestId": "req-550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-01-20T12:30:00Z"
  }
}
```

### 12.2 HTTP Status Codes

| Status Code | Description | Usage |
|------------|-------------|-------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE with no response body |
| 400 | Bad Request | Validation errors, malformed request |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource, constraint violation |
| 422 | Unprocessable Entity | Semantic errors, business logic violations |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side errors |
| 503 | Service Unavailable | Temporary service disruption |

### 12.3 Error Codes

| Error Code | HTTP Status | Description |
|-----------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `INVALID_CREDENTIALS` | 401 | Wrong email/password |
| `TOKEN_EXPIRED` | 401 | JWT token expired |
| `TOKEN_INVALID` | 401 | Invalid JWT token |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource not found |
| `COURSE_NOT_FOUND` | 404 | Course not found |
| `USER_NOT_FOUND` | 404 | User not found |
| `DUPLICATE_EMAIL` | 409 | Email already registered |
| `DUPLICATE_ENROLLMENT` | 409 | Already enrolled in course |
| `PAYMENT_REQUIRED` | 402 | Payment required for access |
| `ENROLLMENT_REQUIRED` | 403 | Must be enrolled to access |
| `FILE_TOO_LARGE` | 413 | File size exceeds limit |
| `INVALID_FILE_TYPE` | 415 | Unsupported file type |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `QUIZ_ATTEMPTS_EXCEEDED` | 422 | Maximum quiz attempts reached |
| `ASSIGNMENT_OVERDUE` | 422 | Assignment submission deadline passed |
| `SERVER_ERROR` | 500 | Internal server error |

### 12.4 API Conventions

#### Naming Conventions
- **Endpoints:** Use plural nouns (`/courses`, `/users`, `/enrollments`)
- **Resource IDs:** Use UUIDs in path parameters (`/courses/{courseId}`)
- **Query Parameters:** Use camelCase (`?sortBy=recent`)
- **Request/Response Fields:** Use camelCase (`firstName`, `courseId`)

#### Pagination
```json
{
  "data": [...],
  "pagination": {
    "currentPage": 1,
    "totalPages": 10,
    "totalItems": 200,
    "itemsPerPage": 20,
    "hasNextPage": true,
    "hasPrevPage": false
  }
}
```

#### Filtering & Sorting
- Use query parameters: `?categoryId=uuid&level=Beginner&sortBy=rating&sortOrder=desc`
- Support multiple filters simultaneously
- Default sort order: newest/most relevant first

#### Date/Time Format
- Use ISO 8601 format: `2026-01-20T12:30:00Z`
- Always use UTC timezone

#### Authentication
- Header: `Authorization: Bearer {access_token}`
- Token expiration: 1 hour (access), 30 days (refresh)

#### Rate Limiting
- Headers returned:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

#### Versioning
- URL versioning: `/api/v1/...`
- Breaking changes require new version

#### CORS
- Allowed origins configured server-side
- Preflight requests handled automatically

---

## Database Indexing Recommendations

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Courses
CREATE INDEX idx_courses_category ON courses(category_id);
CREATE INDEX idx_courses_status ON courses(status);
CREATE INDEX idx_courses_slug ON courses(slug);

-- Enrollments
CREATE INDEX idx_enrollments_user ON enrollments(user_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);
CREATE INDEX idx_enrollments_user_course ON enrollments(user_id, course_id);

-- Video Progress
CREATE INDEX idx_video_progress_enrollment ON video_progress(enrollment_id);
CREATE INDEX idx_video_progress_lecture ON video_progress(lecture_id);

-- Sections
CREATE INDEX idx_sections_course ON sections(course_id);
CREATE INDEX idx_sections_order ON sections(course_id, order_index);

-- Lectures
CREATE INDEX idx_lectures_section ON lectures(section_id);
CREATE INDEX idx_lectures_order ON lectures(section_id, order_index);

-- Reviews
CREATE INDEX idx_reviews_course ON reviews(course_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(course_id, rating);
```

---

**Document Prepared For:** Backend Development Team  
**Database Design:** Third Normal Form (3NF) Compliant  
**API Design Pattern:** RESTful with resource-based endpoints  
**Last Updated:** January 20, 2026

from django.utils import timezone
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Category(models.Model):
    """
    Course Category model - organizes courses into categories.
    Maps to 'categories' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    
    # Self-referencing foreign key for hierarchical categories
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Instructor(models.Model):
    """
    Instructor model - stores instructor information.
    Maps to 'instructors' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instructor_profile'
    )
    
    # Instructor information
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    avatar_url = models.CharField(max_length=500, blank=True)
    expertise = models.JSONField(default=list, blank=True)  # Array of expertise areas
    
    # Statistics
    total_students = models.IntegerField(default=0)
    total_courses = models.IntegerField(default=0)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instructors'
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructors'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Course(models.Model):
    """
    Course model - core course information.
    Maps to 'courses' table in the database.
    """
    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('All Levels', 'All Levels'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    course_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    
    # Descriptions
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    
    # Course properties
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        blank=True
    )
    language = models.CharField(max_length=50, default='English')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Relationships
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    
    # Media
    thumbnail_url = models.CharField(max_length=500, blank=True)
    promo_video_url = models.CharField(max_length=500, blank=True)
    
    # Creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_courses'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'courses'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class CourseMetadata(models.Model):
    """
    Course Metadata model - stores course statistics and metadata (1:1 with Course).
    Maps to 'course_metadata' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='metadata'
    )
    
    # Course structure
    duration_minutes = models.IntegerField(null=True, blank=True)
    total_lectures = models.IntegerField(default=0)
    total_sections = models.IntegerField(default=0)
    
    # Features and flags
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    has_certificate = models.BooleanField(default=True)
    drip_content = models.BooleanField(default=False)
    comments_enabled = models.BooleanField(default=True)
    
    # Statistics
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    
    # Timestamp
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_metadata'
        verbose_name = 'Course Metadata'
        verbose_name_plural = 'Course Metadata'

    def __str__(self):
        return f"Metadata for {self.course.title}"


class CoursePricing(models.Model):
    """
    Course Pricing model - stores pricing information (1:1 with Course).
    Maps to 'course_pricing' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='pricing'
    )
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(max_length=3, default='INR')
    is_free = models.BooleanField(default=False)
    
    # Sale period
    sale_start_date = models.DateTimeField(null=True, blank=True)
    sale_end_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_pricing'
        verbose_name = 'Course Pricing'
        verbose_name_plural = 'Course Pricing'

    def __str__(self):
        return f"Pricing for {self.course.title}"


class CourseInstructor(models.Model):
    """
    Course-Instructor relationship model (Many-to-Many).
    Maps to 'course_instructors' table in the database.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='course_instructors'
    )
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name='course_instructors'
    )
    
    role = models.CharField(max_length=50, default='primary')
    order_index = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_instructors'
        verbose_name = 'Course Instructor'
        verbose_name_plural = 'Course Instructors'
        unique_together = ['course', 'instructor']
        ordering = ['order_index']

    def __str__(self):
        return f"{self.course.title} - {self.instructor.name}"


class Section(models.Model):
    """
    Course Section model - organizes lectures into sections.
    Maps to 'sections' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_index = models.IntegerField()
    is_published = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sections'
        verbose_name = 'Section'
        verbose_name_plural = 'Sections'
        ordering = ['course', 'order_index']
        unique_together = ['course', 'order_index']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lecture(models.Model):
    """
    Lecture model - individual lecture/lesson within a section.
    Maps to 'lectures' table in the database.
    """
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='lectures'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        default='video'
    )
    content_url = models.CharField(max_length=500, blank=True)
    order_index = models.IntegerField()
    # is_preview = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lectures'
        verbose_name = 'Lecture'
        verbose_name_plural = 'Lectures'
        ordering = ['section', 'order_index']
        unique_together = ['section', 'order_index']

    def __str__(self):
        return f"{self.section.title} - {self.title}"


class Coupon(models.Model):
    """
    Coupon model - stores coupon/discount codes.
    Maps to 'coupons' table in the database.
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Percentage Off'),
        ('fixed', 'Fixed Amount Off'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    code = models.CharField(max_length=50, unique=True)
    
    # Discount details (either percent OR fixed, not both)
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Validity
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Usage limits
    max_uses = models.IntegerField(null=True, blank=True)  # NULL = unlimited
    current_uses = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'coupons'
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def is_expired(self):
        """Check if coupon has expired"""
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return True
        if self.valid_to and now > self.valid_to:
            return True
        return False

    def can_be_used(self):
        """Check if coupon can be used based on active status and usage limits"""
        if not self.is_active:
            return False
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False
        if self.is_expired():
            return False
        return True

    def is_for_all_users(self):
        """Check if coupon is available to all users (no specific eligibility records)"""
        return not self.student_eligibilities.exists()

    def is_for_specific_users(self):
        """Check if coupon is restricted to specific users only"""
        return self.student_eligibilities.exists()
    

class CouponCourse(models.Model):
    """
    Coupon-Course relationship model - which courses a coupon applies to (Many-to-Many).
    Maps to 'coupon_courses' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='coupon_courses'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='coupon_courses'
    )
    
    is_applicable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_courses'
        verbose_name = 'Coupon Course'
        verbose_name_plural = 'Coupon Courses'
        unique_together = ['coupon', 'course']

    def __str__(self):
        return f"{self.coupon.code} - {self.course.title}"



class StudentCouponEligibility(models.Model):
    """
    Student Coupon Eligibility model - tracks which students can use which coupons.
    Maps to 'student_coupon_eligibility' table in the database.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_eligibilities'
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='student_eligibilities'
    )
    
    # Usage tracking
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_coupon_eligibility'
        verbose_name = 'Student Coupon Eligibility'
        verbose_name_plural = 'Student Coupon Eligibilities'
        unique_together = ['student', 'coupon']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.email} - {self.coupon.code}"

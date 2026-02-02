# apps/courses/viewss/__init__.py
from .lecture_view import LectureViewSet
from .section_view import SectionViewSet
from .category_view import CategoryViewSet
from .pricing_view import CoursePricingViewSet
from .course_views import CourseViewSet
from .coupon_views import CouponViewSet
__all__ = ['LectureViewSet',
            'SectionViewSet', 
            'CategoryViewSet', 
            'CoursePricingViewSet', 
            'CourseViewSet', 
            'CouponViewSet', 
            # 'CouponCourseViewSet'
            ]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
app_name = 'courses'

# Create router for viewsets
router = DefaultRouter()
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'lectures', LectureViewSet, basename='lecture')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'pricing', CoursePricingViewSet, basename='coursepricing')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'coupons', CouponViewSet, basename='coupon')
# router.register(r'coupon-courses', CouponCourseViewSet, basename='couponcourse')

urlpatterns = [
    path('', include(router.urls)),
]
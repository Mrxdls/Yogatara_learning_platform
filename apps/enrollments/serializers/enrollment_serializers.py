from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.utils import timezone

from ..models import Enrollment
from apps.courses.models import (
    Course,
    CoursePricing,
    Coupon,
    CouponCourse,
    StudentCouponEligibility,
)

GST_RATE = Decimal("0.18")
ENROLLMENT_EXPIRY_MINUTES = 60  # you can change to 30 later


def calculate_gst(amount: Decimal) -> Decimal:
    return (amount * GST_RATE).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


class EnrollmentInitSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    coupon_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._course = None
        self._coupon = None
        self._pricing_data = None
        self._is_free_course = False

    def validate(self, data):
        user = self.context["request"].user

        # 1 Course
        try:
            course = Course.objects.get(id=data["course_id"])
        except Course.DoesNotExist:
            raise serializers.ValidationError("Invalid course.")

        # Check if user is already enrolled
        if Enrollment.objects.filter(
            user=user,
            course=course,
            is_expired=False,
        ).exists():
            raise serializers.ValidationError(
                "User is already enrolled in this course."
            )

        # 3 Pricing
        try:
            pricing = CoursePricing.objects.get(course=course)
        except CoursePricing.DoesNotExist:
            raise serializers.ValidationError("Course pricing not found.")
        
        if pricing.is_free:
            # For free courses, set pricing to zero and mark as free
            base_amount = Decimal("0.00")
            discount_amount = Decimal("0.00")
            gst_amount = Decimal("0.00")
            final_amount = Decimal("0.00")
            coupon = None
            self._is_free_course = True
        else:
            # Paid course logic continues below
            base_amount = pricing.sale_price or pricing.price
            if base_amount <= 0:
                raise serializers.ValidationError("Invalid course price.")

            # 4 Coupon validation
            coupon = None
            discount_amount = Decimal("0.00")

            coupon_code = data.get("coupon_code")
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                except Coupon.DoesNotExist:
                    raise serializers.ValidationError("Invalid coupon code.")

                if not coupon.can_be_used():
                    raise serializers.ValidationError("Coupon is expired or inactive.")

                if not CouponCourse.objects.filter(
                    coupon=coupon,
                    course=course,
                    is_applicable=True,
                ).exists():
                    raise serializers.ValidationError(
                        "Coupon not applicable to this course."
                    )
                if coupon.is_for_specific_users():
                    eligibility = StudentCouponEligibility.objects.filter(
                        student=user,
                        coupon=coupon).first()
                    if eligibility and eligibility.is_used:
                        raise serializers.ValidationError(
                            "Coupon already used by this user.")

                if coupon.discount_type == "percent":
                    discount_amount = (
                        base_amount * coupon.discount_value / Decimal("100")
                    )
                else:
                    discount_amount = base_amount - coupon.discount_value

                discount_amount = min(discount_amount, base_amount)

            # 5 GST + final amount
            discounted_price = base_amount - discount_amount
            gst_amount = calculate_gst(discounted_price)
            final_amount = (discounted_price + gst_amount).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            self._is_free_course = False

        data.update({
            "course": course,
            "base_amount": base_amount,
            "discount_amount": discount_amount,
            "gst_amount": gst_amount,
            "final_amount": final_amount,
            "coupon": coupon,
        })

        # Store data as instance variables for create method
        self._course = course
        self._coupon = coupon
        self._pricing_data = {
            "base_amount": base_amount,
            "discount_amount": discount_amount,
            "gst_amount": gst_amount,
            "final_amount": final_amount,
        }


        return data

    def create(self, validated_data):
        user = self.context["request"].user

        # Use instance variables set in validate method
        course = getattr(self, '_course', None)
        coupon = getattr(self, '_coupon', None)
        pricing_data = getattr(self, '_pricing_data', {})


        # Defensive checks
        if not course:
            raise serializers.ValidationError("Course is required for enrollment")
        if not hasattr(course, 'id'):
            raise serializers.ValidationError("Invalid course object")

        # Check if it's a free course
        if getattr(self, '_is_free_course', False):
            # Create free enrollment
            enrollment = Enrollment.objects.create(
                user=user,
                course=course,
                coupon=coupon,
                base_amount=pricing_data.get('base_amount', 0),
                discount_amount=pricing_data.get('discount_amount', 0),
                gst_amount=pricing_data.get('gst_amount', 0),
                final_amount=pricing_data.get('final_amount', 0),
                payment_status=Enrollment.PaymentStatus.FREE,
                is_active=True,
                expires_at=None,
                is_expired=False,
            )
        else:
            # Create paid enrollment (pending payment)
            enrollment = Enrollment.objects.create(
                user=user,
                course=course,
                coupon=coupon,
                base_amount=pricing_data.get('base_amount', 0),
                discount_amount=pricing_data.get('discount_amount', 0),
                gst_amount=pricing_data.get('gst_amount', 0),
                final_amount=pricing_data.get('final_amount', 0),
                payment_status=Enrollment.PaymentStatus.PENDING,
                is_active=False,
                expires_at=timezone.now() + timedelta(
                    minutes=ENROLLMENT_EXPIRY_MINUTES
                ),
            )

        return enrollment


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = fields

    # add course representation
    def to_representation(self, instance):
        """Optimize course representation in enrollment detail"""
        representation = super().to_representation(instance)
        course = instance.course
        representation['course'] = {
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'thumbnail_url': course.thumbnail_url,
        }
        return representation



class EnrollmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'course',
            'payment_status',
            'is_active',
            'expires_at',
            'is_expired',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        """Optimize course representation in enrollment list"""
        representation = super().to_representation(instance)
        course = instance.course
        representation['course'] = {
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'thumbnail_url': course.thumbnail_url,
        }
        return representation

class ProgressEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'course',
            'is_active',
        ]
        read_only_fields = fields
    def to_representation(self, instance):
        """Optimize course representation in enrollment progress"""
        representation = super().to_representation(instance)
        course = instance.course
        representation['course'] = {
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'thumbnail_url': course.thumbnail_url,
        }
        return representation
    

class EnrollmentProgressUpdateSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2
    )
    is_completed = serializers.BooleanField()

    class Meta:
        model = Enrollment
        fields = [
            'progress_percentage',
            'is_completed',
        ]

    def validate_progress_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Progress percentage must be between 0 and 100."
            )
        return value
    

class EnrollmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = fields
    
    # calcuate progress percentage and auto update is_completed field when ever serializer is called
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # calculate progress percentage from lecture progress
        total_lectures = instance.course.sections.filter(is_published=True).aggregate(
            total_lectures=serializers.Count('lectures', filter=serializers.Q(lectures__is_published=True))
        )['total_lectures'] or 0

        completed_lectures = instance.lecture_progress.filter(is_completed=True).count()

        if total_lectures > 0:
            progress_percentage = (completed_lectures / total_lectures) * 100
        else:
            progress_percentage = 0.0

        representation['progress_percentage'] = round(progress_percentage, 2)

        # Auto update is_completed field
        is_completed = progress_percentage >= 100.0
        if instance.is_completed != is_completed:
            instance.is_completed = is_completed
            instance.save(update_fields=['is_completed'])

        return representation
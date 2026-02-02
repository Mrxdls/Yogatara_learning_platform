from rest_framework import serializers
from django.utils import timezone

from ..models import Enrollment, Payment


class PaymentInitSerializer(serializers.Serializer):
    enrollment_id = serializers.UUIDField()

    def validate(self, data):
        user = self.context["request"].user
        now = timezone.now()

        try:
            enrollment = (
                Enrollment.objects
                .select_for_update()
                .get(
                    id=data["enrollment_id"],
                    user=user,
                    payment_status=Enrollment.PaymentStatus.PENDING,
                    is_expired=False,
                )
            )
        except Enrollment.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid or already processed enrollment."
            )

        # Expiry enforcement (NON-NEGOTIABLE)
        if enrollment.expires_at <= now:
            enrollment.mark_expired()
            raise serializers.ValidationError(
                "Enrollment has expired. Please start again."
            )

        # Prevent duplicate active payments
        if Payment.objects.filter(
            enrollment=enrollment,
            status__in=[
                Payment.Status.CREATED,
                Payment.Status.AUTHORIZED,
            ]
        ).exists():
            raise serializers.ValidationError(
                "An active payment already exists for this enrollment."
            )

        # ✅ Trust enrollment snapshot blindly
        data["enrollment"] = enrollment
        data["amount"] = enrollment.final_amount

        return data




class PaymentVerifySerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()

    def validate(self, data):
        try:
            payment = Payment.objects.select_for_update().get(
                razorpay_order_id=data["razorpay_order_id"],
                status=Payment.Status.CREATED
            )
        except Payment.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid or already processed payment."
            )

        data["payment"] = payment
        return data

class PaymentCaptureSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()

    def validate(self, data):
        try:
            payment = Payment.objects.select_for_update().get(
                id=data["payment_id"],
                status=Payment.Status.AUTHORIZED
            )
        except Payment.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid or non-authorized payment."
            )

        data["payment"] = payment
        return data
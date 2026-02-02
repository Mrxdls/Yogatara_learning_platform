from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.http import HttpResponse
from django.db import transaction
import json

from ..models import Payment, Enrollment
from ..utils import verify_razorpay_signature
from drf_spectacular.utils import extend_schema


class RazorpayWebhookAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # VERY IMPORTANT


    @extend_schema(
        tags=['Webhooks'],
        request=None,
        responses={
            200: {
                'description': 'Webhook processed successfully',
            },
            400: {
                'description': 'Invalid signature',
            }
        })
    @transaction.atomic
    def post(self, request):
        received_signature = request.headers.get("X-Razorpay-Signature")
        payload = request.body  # raw bytes

        if not verify_razorpay_signature(payload, received_signature):
            return HttpResponse(status=400)

        event_data = json.loads(payload)
        event = event_data.get("event")
        entity = event_data["payload"]["payment"]["entity"]

        razorpay_order_id = entity["order_id"]
        razorpay_payment_id = entity["id"]

        try:
            payment = Payment.objects.select_for_update().get(
                razorpay_order_id=razorpay_order_id
            )
        except Payment.DoesNotExist:
            return HttpResponse(status=200)

        enrollment = payment.enrollment

        if event == "payment.captured":
            if enrollment.is_expired or enrollment.expires_at < timezone.now():
                
                payment.mark_failed("Captured after expiry")
                return HttpResponse(status=200)

            payment.status = Payment.Status.CAPTURED
            payment.razorpay_payment_id = razorpay_payment_id
            payment.gateway_response = entity
            payment.save()

            enrollment.payment_status = Enrollment.PaymentStatus.PAID
            enrollment.is_active = True
            enrollment.save()


        elif event == "payment.failed":
            payment.mark_failed(
                entity.get("error_description", "Payment failed")
            )

        elif event == "refund.processed":
            payment.status = Payment.Status.REFUNDED
            payment.save()

            enrollment.payment_status = Enrollment.PaymentStatus.REFUNDED
            enrollment.is_active = False
            enrollment.save()

        return HttpResponse(status=200)

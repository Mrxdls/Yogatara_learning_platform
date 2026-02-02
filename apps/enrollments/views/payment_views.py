import razorpay
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..serializers.payment_serializers import PaymentInitSerializer, PaymentVerifySerializer
from ..models import Payment
from ..utils import verify_razorpay_signature
from core.razor_client import razorpay_client
from drf_spectacular.utils import extend_schema


class PaymentInitAPIView(APIView):
    permission_classes = [IsAuthenticated]


    @extend_schema(
        tags=['Payments'],
        request=PaymentInitSerializer,
        responses={
            201: {
                'description': 'Payment initialized successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'payment_id': 'uuid-string',
                            'razorpay_order_id': 'order_XXXXXXXXXXXXXX',
                            'amount': '499.00',
                            'currency': 'INR',
                            'razorpay_key': 'rzp_test_XXXXXXXXXXXXXX'
                        }
                    }
                }
            }
        })
    @transaction.atomic
    def post(self, request):
        serializer = PaymentInitSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        enrollment = serializer.validated_data["enrollment"]
        amount = serializer.validated_data["amount"]

        # Razorpay expects amount in paise
        order = razorpay_client.order.create({
            "amount": int(amount * 100),
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "enrollment_id": str(enrollment.id),
                "course_id": str(enrollment.course.id),
                "user_id": str(request.user.id),
            }
        })

        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=amount,
            razorpay_order_id=order["id"],
            status=Payment.Status.CREATED,
        )

        return Response(
            {
                "payment_id": payment.id,
                "razorpay_order_id": order["id"],
                "amount": amount,
                "currency": "INR",
                "razorpay_key": settings.RAZORPAY_KEY_ID,
            },
            status=status.HTTP_201_CREATED
        )


class PaymentVerifyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payments'],
        request=PaymentVerifySerializer,
        responses={
            200: {
                'description': 'Payment verified successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'status': 'authorized'
                        }
                    }
                }
            },
            400: {
                'description': 'Payment verification failed',
                'content': {
                    'application/json': {
                        'example': {
                            'status': 'failed'
                        }
                    }
                }
            }
        })
    @transaction.atomic
    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.validated_data["payment"]
        order_id = request.data["razorpay_order_id"]
        payment_id = request.data["razorpay_payment_id"]
        signature = request.data["razorpay_signature"]

        is_valid = verify_razorpay_signature(
            order_id, payment_id, signature
        )

        if not is_valid:
            payment.mark_failed("Signature verification failed")
            return Response(
                {"status": "failed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.mark_authorized(
            payment_id=payment_id,
            signature=signature
        )

        return Response(
            {"status": "authorized"},
            status=status.HTTP_200_OK
        )

# write api mapping
from django.urls import path
from .views.payment_views import PaymentInitAPIView, PaymentVerifyAPIView
from .views.enrollment_views import EnrollmentInitAPIView
from .views.razorpay_webhook_view import RazorpayWebhookAPIView

urlpatterns = [
    path('enrollments/init/', EnrollmentInitAPIView.as_view(), name='enrollment-init'),
    path('payments/init/', PaymentInitAPIView.as_view(), name='payment-init'),
    path('payments/verify/', PaymentVerifyAPIView.as_view(), name='payment-verify'),
    path('webhooks/razorpay/', RazorpayWebhookAPIView.as_view(), name='razorpay-webhook'),
]
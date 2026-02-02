
import hmac
import hashlib
from django.conf import settings


def verify_razorpay_signature(payload, received_signature):
    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, received_signature)

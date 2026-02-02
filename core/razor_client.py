import razorpay
from django.conf import settings

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)
razorpay_client.set_app_details(
    {"title": "Yogatara Learning Platform", "version": "1.0"}
)
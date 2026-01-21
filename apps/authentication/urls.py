from django.urls import path
from .views import (
    SendEmailVerificationView,
    SignupView,
    LoginView,
    LogoutView,
    MeView,
    RefreshTokenView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationView,
)

urlpatterns = [
    # Authentication
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("send-verify-email/", SendEmailVerificationView.as_view(), name="send-verify_email"),
    path("verify-email/", EmailVerificationView.as_view(), name="verify_email"),
    
    # Token management
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    
    # Password management
    path("password/change/", ChangePasswordView.as_view(), name="change_password"),
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    
    # Email verification
    path("email/verify/", EmailVerificationView.as_view(), name="email_verify"),
]


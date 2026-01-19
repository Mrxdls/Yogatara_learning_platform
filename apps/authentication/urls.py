from django.urls import path
from .views import (
    SignupView,
    LoginView,
    LogoutView,
    MeView,
    RefreshTokenView,
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
]

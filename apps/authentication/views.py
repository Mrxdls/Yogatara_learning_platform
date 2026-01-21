from datetime import datetime
from time import time
import jwt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.core.mail import send_mail
from django.utils import timezone

from Learning_hub import settings
from apps.authentication.models import User

from .serializers import (
    SignupSerializer,
    LoginSerializer,
    UserMeSerializer,
    RefreshTokenSerializer,
    RefreshTokenResponseSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    SendVerificationEmailSerializer,
    TokenResponseSerializer
)
from apps.authentication.auth_helper import JWTTokenHelper, EmailHelper

class SignupView(APIView):
    """User registration endpoint."""
    permission_classes = [AllowAny]

    @extend_schema(
        request=SignupSerializer,
        responses={201: SignupSerializer},
        description="Register a new user account"
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        token = JWTTokenHelper.generate_verification_token(user, "email_verification")
        verification_link = f"http://localhost:8000/api/auth/verify-email?token={token}"
        
        EmailHelper.send_verification_email(user.email, verification_link)
        print(verification_link)
        return Response(
            {
                "message": "Account created successfully, please check your email to verify your account",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """User login endpoint - returns JWT tokens."""
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
        description="Login with email and password to get JWT tokens"
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        if user.is_email_verified is False:
            token = JWTTokenHelper.generate_verification_token(user, "email_verification")
            verification_link = f"http://localhost:8000/api/auth/verify-email?token={token}"
            EmailHelper.send_verification_email(user.email, verification_link)
            print(verification_link)
            return Response(
                {"error": "Email is not verified. Please verify your email before logging in."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        else:
            
            # Generate JWT tokens
            refresh = RefreshToken(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Update last login
            user.last_login_at = timezone.now()
            user.save()


            return Response(
                {
                    "access": access_token,
                    "refresh": refresh_token
                },
                status=status.HTTP_200_OK
            )


class LogoutView(APIView):
    """User logout endpoint - blacklists tokens from headers."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name='X-Refresh-Token',
                location=OpenApiParameter.HEADER,
                type=OpenApiTypes.STR,
                required=True,
                description='The refresh token to blacklist (required)'
            ),
        ],
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
        description="Logout by blacklisting tokens from Authorization and X-Refresh-Token headers. "
                    "Authorization header is required for authentication. X-Refresh-Token header is required."
    )
    def post(self, request):
        try:
            # Get access token from Authorization header (already authenticated)
            access_token = request.auth
            if access_token:
                try:
                    token = RefreshToken(access_token)
                    token.blacklist()
                except Exception:
                    pass  # Access token might not be blacklistable, continue

            # Get refresh token from X-Refresh-Token header
            refresh_token = request.headers.get('X-Refresh-Token')
            if not refresh_token:
                return Response(
                    {"error": "X-Refresh-Token header is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception:
                    return Response(
                        {"error": "Invalid refresh token"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MeView(APIView):
    """Get current authenticated user details."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Retrieve the current authenticated user's profile information"
    )
    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)


class RefreshTokenView(APIView):
    """Refresh access token using refresh token."""
    permission_classes = [AllowAny]

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={200: RefreshTokenResponseSerializer},
        description="Refresh the access token using a valid refresh token"
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        refresh_token = serializer.validated_data["refresh"]
        
        try:
            token = RefreshToken(refresh_token)
            return Response(
                {
                    "access": str(token.access_token),
                    "refresh": str(token),
                },
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class ChangePasswordView(APIView):
    """Change password for authenticated user."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
        description="Change password for the currently authenticated user"
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )


class PasswordResetRequestView(APIView):
    """Request password reset email."""
    permission_classes = [AllowAny]

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
        description="Request a password reset email. A reset token will be sent to the email if it exists."
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = JWTTokenHelper.generate_verification_token(
            serializer.validated_data['email'], "password_reset"
        )
        # verification_link = f"http://localhost:8000/api/auth/reset-password-confirm?token={token}"
        # EmailHelper.send_password_reset_email(
            # serializer.validated_data['email'],
            # verification_link
        # )
        return Response(
            {
                "message": "If an account exists with this email, you will receive a password reset link",
                "email_sent": True,
                "expires_in": 3600
            },
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token."""
    permission_classes = [AllowAny]

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
        description="Reset password using the token received via email"
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # TODO: Implement token validation and password reset
        # For now, return success (needs token generation/validation system)
        return Response(
            {"message": "Password has been reset successfully"},
            status=status.HTTP_200_OK
        )

class SendEmailVerificationView(APIView):
    """Send email verification link to user."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
        description="Send an email verification link to the authenticated user's email address"
    )
    def post(self, request):
        user = request.user

        if user.is_email_verified:
            return Response(
                {"message": "Email is already verified"},
                status=status.HTTP_200_OK
            )
        verificaiton_payload = {
            "user_id": str(user.id),
            "email": user.email,
            "type": "email_verification",
            "exp": datetime.utcnow() + jwt.datetime.timedelta(minutes=10)
        }
        
        verification_token = jwt.encode(
            verificaiton_payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        verificaiton_link = f"http://localhost:8000/api/auth/verify-email?token={verification_token}"
        try:

            send_mail(
                subject="Verify your email address",
                message=f"Please verify your email by clicking the following link: {verificaiton_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return Response(
                {"message": "Verification email sent successfully"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to send verification email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class EmailVerificationView(APIView):
    """Verify email address with token."""

    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='token',
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                required=True,
                description='The email verification token sent during registration'
            ),
        ],
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
        description="Verify email address using the token sent during registration"
    )
    def post(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response(
                {"error": "Token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            if user.is_email_verified:
                return Response(
                    {"message": "Email is already verified"},
                    status=status.HTTP_200_OK
                )
            user.is_email_verified = True
            user.save()
            access = str(RefreshToken.for_user(user).access_token)
            refresh = str(RefreshToken.for_user(user))
            return Response(
                {
                    "message": "Email verified successfully",
                    "access": access,
                    "refresh": refresh
                },
                status=status.HTTP_200_OK
            )

        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Token has expired"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except jwt.InvalidTokenError:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            ) 

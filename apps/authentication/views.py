from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .serializers import (
    SignupSerializer,
    LoginSerializer,
    UserMeSerializer,
    RefreshTokenSerializer,
    RefreshTokenResponseSerializer,
)


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

        return Response(
            {
                "message": "Account created successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """User login endpoint - returns JWT tokens."""
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        description="Login with email and password to get JWT tokens"
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """User logout endpoint - blacklists refresh token."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Logout by blacklisting the refresh token"
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
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

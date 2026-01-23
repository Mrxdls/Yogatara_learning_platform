from django.core.mail import send_mail
import jwt
from Learning_hub import settings
from datetime import datetime, timedelta

class EmailHelper:
    @staticmethod
    
    def send_verification_email(user_email, verification_link):
        """
        Send email verification link
        """
        try:
            send_mail(
                subject="Verify your email address",
                message=f"Please verify your email by clicking the following link:\n\n{verification_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False


    def send_password_reset_email(user_email, reset_link):
        """
        Send password reset link
        """
        try:
            send_mail(
                subject="Reset your password",
                message=f"Click the link below to reset your password:\n\n{reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False    
        


class JWTTokenHelper:
    @staticmethod
    def generate_verification_token(user, purpose):
        """
        Generate access and refresh tokens for a user
        """
        token = jwt.encode(
            {
                'user_id': str(user.id),
                'type': purpose,
                'exp': datetime.utcnow() + timedelta(minutes=10),
            },
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        return token
    
    @staticmethod
    def decode_verification_token(token, expected_purpose):
        """
        Decode and validate a verification token
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != expected_purpose:
                raise jwt.InvalidTokenError("Invalid token purpose")
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
        
    @staticmethod
    def blacklist_existing_tokens(user):
        """
        Blacklist all existing tokens for a user
        """
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

        tokens = OutstandingToken.objects.filter(user=user)
        BlacklistedToken.objects.bulk_create(
            [BlacklistedToken(token=token) for token in tokens],
            ignore_conflicts=True
        )
        print(f"Blacklisted {tokens.count()} tokens for user {user.email}")        


from rest_framework_simplejwt.tokens import RefreshToken


class CustomRefreshToken(RefreshToken):
    """
    Custom RefreshToken that adds user claims to both access and refresh tokens
    """

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)

        # Add custom claims to refresh token
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['role'] = user.role
        token['email_verified'] = user.email_verified
        token['is_superuser'] = user.is_superuser
        profile = user.profile
        token['full_name'] = profile.full_name

        return token
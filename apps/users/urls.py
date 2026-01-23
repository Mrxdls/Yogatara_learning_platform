from django.urls import path, include
from django.urls import re_path
from .views import (
    UserProfileView,
    UserSettingsView,
    UserSkillsView,
    UserSocialView,
    UserProfilePictureView,
)

urlpatterns = [
    path('me/profile/', UserProfileView.as_view(), name='user-profile'),
    path('me/settings/', UserSettingsView.as_view(), name='user-settings'),
    path('me/skills/', UserSkillsView.as_view(), name='user-skills'),
    path('me/social/', UserSocialView.as_view(), name='user-social'),
    path('me/profile-picture/', UserProfilePictureView.as_view(), name='user-profile-picture'),
]
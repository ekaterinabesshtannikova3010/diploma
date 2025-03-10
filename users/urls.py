from django.contrib.auth.views import LogoutView
from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .apps import UsersConfig
from .views import (InviteCodeView, VerifyCodeView, UserProfileView,
                    LinkUsersView, UserRegistrationView, UserRegistrationAPIView, InviteCodeAPIView, VerifyCodeAPIView,
                    UserProfileAPIView)

app_name = UsersConfig.name

router = DefaultRouter()
# router.register(r'user', UserViewSet)
# router.register(r'invite-codes', InviteCodeViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('api/register/', UserRegistrationAPIView.as_view(), name='api_register'),
    path('api/invite_code/', InviteCodeAPIView.as_view(), name='api_invite_code'),
    path('api/verify_code/', VerifyCodeAPIView.as_view(), name='api_verify_code'),
    path('api/profile/', UserProfileAPIView.as_view(), name='api_profile'),
    # path('api/request-verification-code/', RequestVerificationCodeView.as_view(), name='request_verification'),

    path('register/', UserRegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('invite_code/', InviteCodeView.as_view(), name='invite_code'),
    path('verify_code/', VerifyCodeView.as_view(), name='verify_code'),
    path('link-users/', LinkUsersView.as_view(), name='link_users'),
]

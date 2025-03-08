from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import views
from .apps import UsersConfig
from .views import (UserViewSet, MyTokenObtainPairView, LoginView,
                    AuthView, InviteCodeView, VerifyCodeView, UserProfileView, GenerateInviteCodeView,
                    LinkUsersView, AuthView_API, InviteCodeViewSet, UserRegistrationView)

app_name = UsersConfig.name

router = DefaultRouter()
router.register(r'user', UserViewSet)
# router.register(r'invite-codes', InviteCodeViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/auth/', AuthView_API.as_view(), name='auth_api'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/users/', UserViewSet.as_view({'get': 'list', 'post': 'create'}), name='user'),
    # path('api/request-verification-code/', RequestVerificationCodeView.as_view(), name='request_verification'),


    path('register/', UserRegistrationView.as_view(), name='register'),
    path('auth/', AuthView.as_view(), name='auth'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('generate-invite-code/', GenerateInviteCodeView.as_view(), name='generate_invite_code'),
    path('invite_code/', InviteCodeView.as_view(), name='invite_code'),
    path('verify_code/', VerifyCodeView.as_view(), name='verify_code'),
    path('link-users/', LinkUsersView.as_view(), name='link_users'),
    # path('confirm_code/', ConfirmCodeView.as_view(), name='confirm_code'),


]

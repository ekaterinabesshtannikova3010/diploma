import logging
import os
from random import randint
from time import sleep
from django.conf import settings
from django.contrib.auth import login

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.crypto import get_random_string
from django.views import View
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.contrib import messages
from smsaero import SmsAero, SmsAeroException
from .models import User, InviteCode, LoginCode
from .serializers import UserSerializer, InviteCodeSerializer, MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
import requests
api_key = os.getenv('API_KEY')
SMSAERO_API_KEY = os.getenv('API_KEY')
SMSAERO_EMAIL = 'dolmatova3010@yandex.ru'
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
SMS_AERO_API_URL = 'https://smsaero.ru/api/'
SMS_AERO_API_KEY = os.getenv('API_KEY')


def home(request):
    return render(request, 'users/base.html')



class UserRegistrationAPIView(APIView):
    """API для регистрации пользователя."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Пользователь зарегистрирован: {user.phone_number}")
            return Response({'message': 'Регистрация прошла успешно!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InviteCodeAPIView(APIView):
    """API для отправки кода подтверждения на номер телефона."""

    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone')
        if not phone_number:
            return Response({'error': 'Пожалуйста, введите номер телефона.'}, status=status.HTTP_400_BAD_REQUEST)

        # Удаляем все нецифровые символы
        phone_number = re.sub(r'\D', '', phone_number)

        # Проверяем, что номер телефона состоит из 10-15 цифр
        if len(phone_number) < 10 or len(phone_number) > 15:
            return Response({'error': 'Некорректный номер телефона.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            phone_number = int(phone_number)  # Преобразуем строку в целое число
        except ValueError:
            return Response({'error': 'Некорректный номер телефона. Убедитесь, что Вы ввели только цифры.'}, status=status.HTTP_400_BAD_REQUEST)

        code = LoginCode.create_code(str(phone_number))
        logger.debug(f"Сгенерирован код: {code} для номера: {phone_number}")

        # Отправляем SMS
        is_success = self.send_sms(phone_number, f'Ваш код подтверждения: {code}')
        if not is_success:
            return Response({'error': 'Не удалось отправить сообщение, попробуйте еще раз.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.debug(f"SMS успешно отправлено на номер: %s", phone_number)
        return Response({'message': 'Код подтверждения отправлен на Ваш номер.'}, status=status.HTTP_200_OK)

    def send_sms(self, phone: int, message: str) -> bool:
        if settings.FAKE_SMS_SUBMIT:
            return True

        api = SmsAero('dolmatova3010@yandex.ru', 'TNzg_oub8xthiLQpuVli_1gLpr2YaRA6')
        logger.debug(f"Отправка SMS на номер: {phone}. Сообщение: {message}")

        try:
            response = api.send_sms(phone, message)
        except SmsAeroException as e:
            logger.error(f'Failed to send sms due error %s', e)
            return False
        logger.debug(response)
        is_success = response
        if not is_success:
            logger.error(f'Invalid smsaero response: %s', response)
            return False

        return True


class VerifyCodeAPIView(APIView):
    """API для проверки введенного кода подтверждения."""

    def post(self, request):
        entered_code = request.data.get('code')
        phone_number = request.session.get('phone')

        login_code = LoginCode.objects.filter(
            phone_number=phone_number, code=entered_code, is_actual=True
        ).first()
        if not login_code:
            return Response({'error': 'Неверный код. Пожалуйста, попробуйте снова.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            LoginCode.objects.filter(phone_number=phone_number).delete()
            return Response({'error': 'Пользователь не найден. Пожалуйста, зарегистрируйтесь.'}, status=status.HTTP_404_NOT_FOUND)

        if not user.invite_code:
            user.invite_code = get_random_string(length=6)
            user.save()

        login(request, user)
        LoginCode.objects.filter(phone_number=phone_number).delete()

        return Response({'message': 'Вы успешно авторизованы!'}, status=status.HTTP_200_OK)

    def get(self, request):
        return Response({'message': 'Пожалуйста, отправьте код для проверки.'}, status=status.HTTP_200_OK)




class UserProfileAPIView(APIView):
    """API для профиля пользователя."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # Получаем текущего пользователя
        invited_users = User.objects.filter(invite_code=user.invite_code)  # Получаем пользователей по инвайт-коду
        return Response({'user': user, 'invited_users': invited_users.values()}, status=status.HTTP_200_OK)

    def post(self, request):
        # Логика для связывания пользователей по инвайт-коду
        invite_code = request.data.get('invite_code')
        phone_number = request.data.get('phone_number')  # Получаем номер телефона
        name = request.data.get('first_name')  # Получаем имя

        if phone_number and name:  # Проверка на наличие номера телефона и имени
            user = request.user
            user.phone_number = phone_number
            user.first_name = name
            user.save()  # Сохранение пользователя

            invited_users = User.objects.filter(invite_code=invite_code)
            if invite_code:
                return Response({'message': 'Пользователь успешно связан.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Введите корректный инвайт-код.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Неверный номер телефона или имя!'}, status=status.HTTP_400_BAD_REQUEST)
#
# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = MyTokenObtainPairSerializer




class UserInviteCodeViewSet(viewsets.ModelViewSet):
    """
    Представление для активации инвайт-кода.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=['post'])
    def activate_invite_code(self, request, pk=None):
        user = self.get_object()
        invite_code = request.data.get('invite_code')

        invite = get_object_or_404(InviteCode, code=invite_code)

        if invite.is_active:
            user.activated_invite_code = invite.code
            user.save()
            return Response({'message': 'Инвайт-код активирован успешно.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Инвайт-код не активен.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def users_with_invite_code(self, request):
        user = request.user  # Получаем текущего пользователя
        users = User.objects.filter(
            activated_invite_code=user.activated_invite_code)  # Фильтруем пользователей по инвайт-коду
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


# class UserProfileViewSet(viewsets.ModelViewSet):
#     """
#     Представление для получения профиля пользователя.
#     """
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#
#     @action(detail=True, methods=['get'])
#     def profile(self, request, pk=None):
#         user = self.get_object()
#         serializer = UserSerializer(user)
#         return Response(serializer.data, status=status.HTTP_200_OK)


class InviteCodeViewSet(viewsets.ModelViewSet):
    queryset = InviteCode.objects.all()
    serializer_class = InviteCodeSerializer


# class RequestVerificationCodeView(APIView):
#     """
#     Представление для отправки кода подтверждения на телефон.
#     """
#     model = User
#     template_name = 'users/сonfirmation.html'
#
#     def get(self, request):
#         return render(request, 'users/login.html')
#
#     def post(self, request):
#         phone_number = request.data.get('phone_number')
#         if not phone_number:
#             return Response({"error": "Номер телефона обязателен."}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Отправка кода
#         code = request_verification_code(phone_number)
#
#         # Сохранение или обновление пользователя
#         user, created = User.objects.get_or_create(phone_number=phone_number)
#         user.verification_code = code
#         user.save()
#
#         return Response({"message": "Код подтверждения отправлен."}, status=status.HTTP_200_OK)



""" Django реализация."""


class UserRegistrationView(View):
    """Представление для регистрации пользователя."""

    def get(self, request):
        return render(request, 'users/registration.html')

    def post(self, request):
        phone_number = request.POST.get('phone_number')
        first_name = request.POST.get('first_name')
        print(f"Полученный номер телефона: {phone_number}")
        print(f"Полученное имя пользователя: {first_name}")
        if phone_number and first_name:
            try:
                user = User.objects.create(phone_number=phone_number, first_name=first_name)
                user.save()
                messages.success(request, 'Регистрация прошла успешно!')
                return redirect('users:invite_code')  # Перенаправление на страницу входа
            except Exception as e:
                messages.error(request, f'Ошибка регистрации: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля!')

        return render(request, 'users/registration.html')


class InviteCodeView(View):
    """Представление для отправки кода подтверждения на номер телефона."""

    def post(self, request):
        phone_number = request.POST.get('phone')
        if not phone_number:
            messages.error(request, 'Пожалуйста, введите номер телефона.')
            logger.debug("Пользователь не ввел номер телефона.")
            return render(request, 'users/invite_code.html')

        # Удаляем все нецифровые символы
        phone_number = re.sub(r'\D', '', phone_number)

        # Проверяем, что номер телефона состоит из 10-15 цифр (в зависимости от формата)
        if len(phone_number) < 10 or len(phone_number) > 15:
            messages.error(request, 'Некорректный номер телефона. Убедитесь, что Вы ввели правильный номер.')
            return render(request, 'users/invite_code.html')

        try:
            phone_number = int(phone_number)  # Преобразуем строку в целое число
        except ValueError:
            messages.error(request, 'Некорректный номер телефона. Убедитесь, что Вы ввели только цифры.')
            return render(request, 'users/invite_code.html')

        code = LoginCode.create_code(str(phone_number))
        logger.debug(f"Сгенерирован код: {code} для номера: {phone_number}")

        # Отправляем SMS
        is_success = self.send_sms(phone_number, f'Ваш код подтверждения: {code}')
        if not is_success:
            messages.error(request, 'Не удалось отправить сообщение, попробуйте еще раз.')
            return render(request, 'users/invite_code.html')

        phone_number = str(phone_number)
        messages.success(request, 'Код подтверждения отправлен на Ваш номер.')
        request.session['phone'] = phone_number

        logger.debug(f"SMS успешно отправлено на номер: %s", phone_number)
        return redirect('users:verify_code')

    def get(self, request):
        return render(request, 'users/invite_code.html')

    def send_sms(self, phone: int, message: str) -> bool:
        if settings.FAKE_SMS_SUBMIT:
            return True

        api = SmsAero('dolmatova3010@yandex.ru', 'TNzg_oub8xthiLQpuVli_1gLpr2YaRA6')
        logger.debug(f"Отправка SMS на номер: {phone}. Сообщение: {message}")

        try:
            response = api.send_sms(phone, message)
        except SmsAeroException as e:
            logger.error(f'Failed to send sms due error %s', e)
            return False
        logger.debug(response)
        is_success = response
        if not is_success:
            logger.error(f'Invalid smsaero response: %s', response)
            return False

        return True


class VerifyCodeView(View):
    """Представление для проверки введенного кода подтверждения."""

    def post(self, request):
        entered_code = request.POST.get('code')
        phone_number = request.session.get('phone')

        login_code = LoginCode.objects.filter(
            phone_number=phone_number, code=entered_code, is_actual=True
        ).first()
        if not login_code:
            messages.error(request, 'Неверный код. Пожалуйста, попробуйте снова.')
            return render(request, 'users/verify_code.html')

        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            LoginCode.objects.filter(phone_number=phone_number).delete()
            return redirect('users:register')

        if not user.invite_code:
            user.invite_code = get_random_string(length=6)
            user.save()

        login(request, user)

        LoginCode.objects.filter(phone_number=phone_number).delete()

        return redirect('users:profile')

    def get(self, request):
        return render(request, 'users/verify_code.html')


#######

class UserProfileView(View):
    """Представление для профиля пользователя."""

    def get(self, request):
        user = request.user  # Получаем текущего пользователя
        invited_users = User.objects.filter(invite_code=user.invite_code)  # Получаем пользователей по инвайт-коду
        return render(request, 'users/profile.html', {'user': user, 'invited_users': invited_users})

    def post(self, request, invited_users=None):
        # Логика для связывания пользователей по инвайт-коду
        invite_code = request.POST.get('invite_code')
        phone_number = request.POST.get('phone_number')  # Получаем номер телефона
        name = request.POST.get('first_name')  # Получаем имя

        if phone_number and name:  # Проверка на наличие номера телефона и имени
            user = request.user
            user.phone_number = phone_number  #
            user.first_name = name
            user.save()  # Сохранение пользователя

            invited_users = User.objects.filter(invite_code=invite_code)
            if invite_code:
                messages.success(request, 'Пользователь успешно связан.')
            else:
                messages.error(request, 'Введите корректный инвайт-код.')
                return render(request, 'users/profile.html', {'user': request.user, 'invited_users': invited_users})

            messages.success(request, 'Вы успешно авторизованы и ваш профиль обновлён!')
            return redirect('users:profile')  # Перенаправляем на профиль пользователя
        else:
            messages.error(request, 'Неверный номер телефона или имя!')

        return render(request, 'users/profile.html', {'user': request.user, 'invited_users': invited_users})


#############

class LinkUsersView(View):
    def post(self, request):
        invite_code = request.POST.get('invite_code')
        user = request.user

        if invite_code:
            invited_users = User.objects.filter(invite_code=invite_code)
            for invited_user in invited_users:
                invited_user.linked_users.add(user)
                invited_user.save()

            messages.success(request, 'Пользователи успешно связаны.')
        else:
            messages.error(request, 'Введите корректный инвайт-код.')

        return redirect('users:profile')

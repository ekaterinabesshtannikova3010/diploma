import logging
import os
import random
import string
from random import randint
from time import sleep

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.contrib import messages
from smsaero import SmsAero, SmsAeroException

from .models import User, InviteCode
from .serializers import UserSerializer, InviteCodeSerializer, MyTokenObtainPairSerializer, AuthSerializer
from users.services import SMSAero, api_user, send_sms

from rest_framework_simplejwt.views import TokenObtainPairView
import requests

SMS_AERO_API_URL = 'https://smsaero.ru/api/'
SMS_AERO_API_KEY = os.getenv('API_KEY')


def home(request):
    return render(request, 'users/base.html')


class LoginView(View):
    """
        Контроллер для регистрации пользователя.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    model = User
    template_name = 'users/login.html'

    def get(self, request):
        return render(request, 'users/login.html')

    def post(self, request):
        phone_number = request.POST['phone_number']
        password = request.POST['password']
        try:
            user = User.objects.get(phone_number=phone_number)
            if user.check_password(password):
                request.session['user_id'] = user.id
                return redirect('home')
        except User.DoesNotExist:
            pass
        return render(request, 'users/login.html')


class AuthView_API(APIView):
    """Представление для авторизации с номером телефона и именем."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    model = User
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')  # Изменено на request.data
        first_name = request.data.get('first_name')  # Изменено на request.data
        try:
            user = User.objects.get(phone_number=phone_number)
            if user.check_password(first_name):  # Проверьте, что это правильная проверка
                request.session['user_id'] = user.id
                return Response({'message': 'Успешная авторизация!'}, status=200)  # Изменено на Response
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден.'}, status=404)  # Добавлено сообщение об ошибке

        return Response({'error': 'Неверные учетные данные.'}, status=400)

    def get(self, request):
        return Response({'message': 'GET запрос не поддерживается для этого эндпоинта.'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserViewSet(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    model = User
    template_name = 'users/confirm_code.html'
    """
    Представление для авторизации пользователя.
    """

    def list(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = UserSerializer(data=request.data)  # Инициализируем сериализатор с данными
        if serializer.is_valid():  # Проверяем на валидность
            serializer.save()  # Сохраняем объект
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # Возвращаем созданный объект
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def authorize(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"error": "Укажите номер телефона."}, status=status.HTTP_400_BAD_REQUEST)

        # Имитация отправки кода
        sleep(2)  # Задержка 1-2 секунды
        auth_code = str(randint(1000, 9999))  # Генерация 4-значного кода

        # Сохранение или обновление пользователя
        user, created = User.objects.get_or_create(phone_number=phone_number)
        user.verification_code = auth_code
        user.save()

        return Response({'auth_code': auth_code}, status=status.HTTP_200_OK)


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

api_key = os.getenv('API_KEY')
SMSAERO_API_KEY = os.getenv('API_KEY')
SMSAERO_EMAIL = 'dolmatova3010@yandex.ru'
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

""" Django эндпоинты."""


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
                return redirect('auth')  # Перенаправление на страницу входа
            except Exception as e:
                messages.error(request, f'Ошибка регистрации: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля!')

        return render(request, 'users/registration.html')


class AuthView(View):
    """Представление для авторизации с номером телефона и именем."""

    def post(self, request):
        phone_number = request.POST.get('phone_number')
        name = request.POST.get('first_name')

        # Логика авторизации
        if phone_number and name:  # Проверка на наличие номера телефона и имени
            messages.success(request, 'Вы успешно авторизованы!')
            return redirect('users:home')  # Укажите Ваш URL в случае успеха
        else:
            messages.error(request, 'Неверный номер телефона или имя!')

        return render(request, 'users/login.html')

    def get(self, request):
        return render(request, 'users/login.html')


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

        code = str(random.randint(1000, 9999))  # Генерация случайного 4-значного кода
        logger.debug(f"Сгенерирован код: {code} для номера: {phone_number}")

        # Отправляем SMS
        is_success = send_sms(phone_number, f'Ваш код подтверждения: {code}')

        if not is_success:
            messages.error(request, 'Не удалось отправить сообщение, попробуйте еще раз.')
            return render(request, 'users/invite_code.html')

        messages.success(request, 'Код подтверждения отправлен на Ваш номер.')
        request.session['confirmation_code'] = code
        logger.debug(f"SMS успешно отправлено на номер: %s", phone_number)
        return redirect('users:verify_code')

    def get(self, request):
        return render(request, 'users/invite_code.html')

    def send_sms(phone: int, message: str) -> bool:
        """
        Отправка SMS сообщения

        Параметры:
        phone (str): Номер телефона, на который будет отправлено SMS сообщение.
        message (str): Содержимое SMS сообщения.

        Возвращает:
        dict: Словарь, содержащий ответ от API SmsAero.
        """
        api = SmsAero('dolmatova3010@yandex.ru', 'TNzg_oub8xthiLQpuVli_1gLpr2YaRA6')
        logger.debug(f"Отправка SMS на номер: {phone}. Сообщение: {message}")

        try:
            response = api.send_sms(phone, message)
        except SmsAeroException as e:
            logger.error(f'Failed to send sms due error %s', e)
            return False

        is_success = response['success']
        if not is_success:
            logger.error(f'Invalid smsaero response: %s', response)
            return False

        return True


class VerifyCodeView(View):
    """Представление для проверки введенного кода подтверждения."""

    def post(self, request):
        entered_code = request.POST.get('code')

        if entered_code == request.session.get('confirmation_code'):
            invite_code = get_random_string(length=6)
            messages.success(request, f'Ваш инвайт-код: {invite_code}')
            return redirect('users:profile')
        else:
            messages.error(request, 'Неверный код. Пожалуйста, попробуйте снова.')
            return render(request, 'users/verify_code.html')

    def get(self, request):
        return render(request, 'users/verify_code.html')


#######


# @method_decorator(login_required, name='dispatch')
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

def generate_invite_code(length=6):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not InviteCode.objects.filter(code=code).exists():
            return code


class GenerateInviteCodeView(View):
    def post(self, request):
        invite_code = generate_invite_code()
        InviteCode.objects.create(code=invite_code)
        return JsonResponse({'invite_code': invite_code}, status=201)


class LinkUsersView(View):
    def post(self, request):
        invite_code = request.POST.get('invite_code')
        user = request.user

        # Логика связывания пользователей по инвайт-коду
        if invite_code:
            messages.success(request, 'Пользователь успешно связан.')
        else:
            messages.error(request, 'Введите корректный инвайт-код.')

        return redirect('users:profile')  # Перенаправление на страницу профиля

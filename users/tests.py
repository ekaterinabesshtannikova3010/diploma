from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status

from .models import User, LoginCode


class UserRegistrationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.registration_url = reverse('users:register')

    def test_registration_success(self):
        response = self.client.post(self.registration_url, {
            'phone_number': '1234567890',
            'first_name': 'TestUser'
        })
        self.assertEqual(response.status_code, 302)  # Проверка перенаправления
        self.assertTrue(User.objects.filter(phone_number='1234567890').exists())  # Проверка, что пользователь создан

    def test_registration_missing_fields(self):
        response = self.client.post(self.registration_url, {
            'phone_number': '',
            'first_name': ''
        })
        self.assertEqual(response.status_code, 200)  # Проверка, что возвращается форма
        self.assertContains(response, 'Пожалуйста, заполните все поля!')  # Проверка сообщения об ошибке

    def test_registration_duplicate_phone_number(self):
        User.objects.create(phone_number='1234567890', first_name='ExistingUser')
        response = self.client.post(self.registration_url, {
            'phone_number': '1234567890',
            'first_name': 'TestUser'
        })
        self.assertEqual(response.status_code, 200)  # Проверка, что возвращается форма
        self.assertContains(response, 'Ошибка регистрации:')  # Проверка сообщения об ошибке


class InviteCodeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('users:invite_code')  # Убедитесь, что это правильный путь

    def test_get_invite_code_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/invite_code.html')

    def test_post_invalid_phone_number(self):
        response = self.client.post(self.url, {'phone': 'invalid_phone'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Некорректный номер телефона. Убедитесь, что Вы ввели правильный номер.')

    def test_post_empty_phone_number(self):
        response = self.client.post(self.url, {'phone': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пожалуйста, введите номер телефона.')

from django.contrib import messages
class LinkUsersViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(first_name='testuser', phone_number='1234567890', password='password')
        self.invited_user = User.objects.create_user(first_name='invited_user', phone_number='0987654321', password='password', invite_code='12345')
        self.client.login(first_name='testuser', password='password')

    def test_link_users_with_valid_invite_code(self):
        response = self.client.post(reverse('users:link_users'), {'invite_code': '123456'})

        # Проверяем, что пользователи были связаны
        self.invited_user.refresh_from_db()
        self.assertIn(self.user, self.invited_user.linked_users.all())

        # Проверяем, что было успешно отправлено сообщение
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].tags, 'success')
        self.assertEqual(messages_list[0].message, 'Пользователи успешно связаны.')

        # Проверяем редирект
        self.assertRedirects(response, reverse('users:profile'))

    def test_link_users_with_invalid_invite_code(self):
        response = self.client.post(reverse('users:link_users'), {'invite_code': ''})

        # Проверяем, что пользователи не были связаны
        self.invited_user.refresh_from_db()
        self.assertNotIn(self.user, self.invited_user.linked_users.all())

        # Проверяем, что было выдано сообщение об ошибке
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].tags, 'error')
        self.assertEqual(messages_list[0].message, 'Введите корректный инвайт-код.')

        # Проверяем редирект
        self.assertRedirects(response, reverse('users:profile'))

    def test_link_users_with_nonexistent_invite_code(self):
        response = self.client.post(reverse('users:link_users'), {'invite_code': 'nonexistent_code'})

        # Проверяем, что пользователи не были связаны
        self.invited_user.refresh_from_db()
        self.assertNotIn(self.user, self.invited_user.linked_users.all())

        # Проверяем, что было выдано сообщение об ошибке
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].tags, 'error')
        self.assertEqual(messages_list[0].message, 'Введите корректный инвайт-код.')

        # Проверяем редирект
        self.assertRedirects(response, reverse('users:profile'))
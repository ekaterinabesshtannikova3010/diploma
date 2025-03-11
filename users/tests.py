from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse
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

    def test_registration_duplicate_phone_numbers(self):
        User.objects.create(phone_number='1234567899', first_name='ExistingUser')
        response = self.client.post(self.registration_url, {
            'phone_number': '1234567899',
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

    def test_post_valid_phone_number(self):
        # Создаем пользователя для теста
        user = User.objects.create_user(
            phone_number='1234567890',
            first_name='Test User',
            email='test@example.com',  # Обязательно указываем email
            password='password123'
        )
        response = self.client.post(self.url, {'phone': '1234567890'})
        self.assertEqual(response.status_code, 302)  # Проверка перенаправления
        self.assertTrue(user.invite_code)  # Проверка, что инвайт-код был сгенерирован


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='1234567890',
            first_name='Test User',
            email='test@example.com',  # Обязательно указываем email
            password='password123'
        )
        self.client.login(phone_number='1234567890', password='password123')

    def test_user_profile_view_get(self):
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')

    def test_user_profile_view_post(self):
        response = self.client.post(reverse('users:profile'), {
            'invite_code': 'ABC123',
            'phone_number': '0987654321',
            'first_name': 'Updated User'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '0987654321')
        self.assertEqual(self.user.first_name, 'Updated User')
        self.assertRedirects(response, reverse('users:profile'))

    def test_user_profile_view_post_no_invite_code(self):
        response = self.client.post(reverse('users:profile'), {
            'phone_number': '0987654321',
            'first_name': 'Updated User'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '0987654321')
        self.assertEqual(self.user.first_name, 'Updated User')
        # Проверяем, что сообщение об ошибке отображается
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Введите корректный инвайт-код.')
        self.assertEqual(response.status_code, 200)  # Ожидаем, что форма будет возвращена

    def test_user_profile_view_post_invalid_phone_number(self):
        response = self.client.post(reverse('users:profile'), {
            'invite_code': 'ABC123',
            'phone_number': '',  # Неверный номер телефона
            'first_name': 'Updated User'
        })
        self.assertEqual(response.status_code, 200)  # Ожидаем, что форма будет возвращена
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Неверный номер телефона или имя!')

    def test_user_profile_view_post_invalid_name(self):
        response = self.client.post(reverse('users:profile'), {
            'invite_code': 'ABC123',
            'phone_number': '0987654321',
            'first_name': ''  # Неверное имя
        })
        self.assertEqual(response.status_code, 200)  # Ожидаем, что форма будет возвращена
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Неверный номер телефона или имя!')


class LinkUsersViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='1234567890',
            first_name='Test User',
            email='test@example.com'  # Убедитесь, что email заполнен
        )
        self.invited_user = User.objects.create_user(
            phone_number='0987654321',
            first_name='Invited User',
            email='invited@example.com',  # Убедитесь, что email заполнен
            invite_code='ABC123'
        )
        self.client.login(phone_number='1234567890')  # Логинимся как основной пользователь

    def test_link_users_invalid_invite_code(self):
        response = self.client.post(reverse('users:link_users'), {'invite_code': 'INVALID'})
        self.assertEqual(response.status_code, 302)  # Проверяем, что происходит редирект
        self.assertNotIn(self.user, self.invited_user.linked_users.all())


class VerifyCodeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='1234567890',
            first_name='Test User',
            email='testuser@example.com',  # Добавляем email
            password='testpassword'
        )
        self.login_code = LoginCode.objects.create(
            phone_number=self.user.phone_number,
            code='123456',
            is_actual=True
        )
        self.url = reverse('users:verify_code')  # Убедитесь, что это правильный URL

    def test_verify_code_invalid(self):
        self.client.session['phone'] = self.user.phone_number
        response = self.client.post(self.url, {'code': 'wrongcode'})
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Неверный код. Пожалуйста, попробуйте снова.')

    def test_get_verify_code_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/verify_code.html')

    def test_verify_code_partial_match(self):
        self.client.session['phone'] = self.user.phone_number
        response = self.client.post(self.url, {'code': '1234'})  # Предположим, частичный ввод также недопустим
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Неверный код. Пожалуйста, попробуйте снова.')

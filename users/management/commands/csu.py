from django.core.management import BaseCommand
from users.models import User


class Command(BaseCommand):
    """Команда для создания суперпользователя"""

    def handle(self, *args, **kwargs):
        phone_number = "+79205051030"
        email = "test3010diploma@yandex.ru"
        password = "1234567!"

        if not User.objects.filter(phone_number=phone_number).exists():
            user = User.objects.create_superuser(phone_number=phone_number, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Суперпользователь {email} ({phone_number}) создан."))
        else:
            self.stdout.write(self.style.WARNING(f"Пользователь с номером {phone_number} уже существует."))

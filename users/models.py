# from django.contrib.auth.models import AbstractUser, BaseUserManager
# from django.db import models
# import random
# import string
#
#
#
# class CustomUserManager(BaseUserManager):
#     def create_user(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError("The Email field must be set")
#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#
#         if not extra_fields.get('is_staff'):
#             raise ValueError("Superuser must have is_staff=True.")
#         if not extra_fields.get('is_superuser'):
#             raise ValueError("Superuser must have is_superuser=True.")
#
#         return self.create_user(email, password, **extra_fields)
#
#     def get_by_natural_key(self, email):
#         return self.get(email=email)
#
#
# class User(AbstractUser):
#     """
#     Определение модели пользователя
#     """
#     username = None
#     phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
#     invite_code = models.CharField(max_length=6, unique=True, blank=True, null=True, verbose_name="Инвайт-код")
#     activated_invite_code = models.ForeignKey('InviteCode', on_delete=models.SET_NULL, null=True, blank=True,
#                                               related_name='users', verbose_name="Активированный инвайт-код")
#     referred_users = models.ManyToManyField('self', symmetrical=False, related_name='referrals', blank=True,
#                                             verbose_name="Пользователи, которые использовали инвайт-код")
#
#     USERNAME_FIELD = "phone_number"
#     REQUIRED_FIELDS = []
#
#     objects = CustomUserManager()
#
#     def save(self, *args, **kwargs):
#         if not self.invite_code:
#             self.invite_code = self.generate_invite_code()
#         super().save(*args, **kwargs)
#
#     def generate_invite_code(self):
#         return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
#
#     def __str__(self):
#         return self.phone_number
#
#     class Meta:
#         verbose_name = "пользователь"
#         verbose_name_plural = "пользователи"
#         ordering = ["phone_number"]
#
#
# class InviteCode(models.Model):
#     code = models.CharField(max_length=6, unique=True)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return self.code
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import random
import string
from django.db.transaction import atomic


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, email=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone Number field must be set")
        email = self.normalize_email(email) if email else None
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, email, password, **extra_fields)

    def get_by_natural_key(self, phone_number):
        return self.get(phone_number=phone_number)



class User(AbstractUser):
    username = None
    first_name = models.CharField(max_length=50, blank=True, verbose_name="Имя")
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона")
    invite_code = models.CharField(max_length=6, unique=True, blank=True, default="", verbose_name="Инвайт-код")
    linked_users = models.ManyToManyField('self', symmetrical=False, related_name='linked_by', blank=True)
    activated_invite_code = models.ForeignKey(
        'InviteCode', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activated_by', verbose_name="Активированный инвайт-код"
    )
    referred_users = models.ManyToManyField(
        'self', symmetrical=False, related_name='referrals', blank=True,
        verbose_name="Пользователи, которые использовали инвайт-код"
    )

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["first_name", "email"]

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)

    def generate_invite_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not User.objects.filter(invite_code=code).exists():
                return code

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["phone_number"]


class InviteCode(models.Model):
    code = models.CharField(max_length=6, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


def generate_login_code() -> str:
    return str(random.randint(1000, 9999))


class LoginCode(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=4, default=generate_login_code)
    is_actual = models.BooleanField(default=True)

    @classmethod
    def create_code(cls, phone: str):
        with atomic():
            LoginCode.objects.filter(phone_number=phone).update(is_actual=False)
            return LoginCode.objects.create(phone_number=phone).code

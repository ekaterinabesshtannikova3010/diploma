import os
import random
import time
import requests
from dotenv import load_dotenv

load_dotenv()

api_user = os.getenv('API_USER')
api_key = os.getenv('API_KEY')
from pprint import pprint
from smsaero import SmsAero, SmsAeroException


SMSAERO_EMAIL = 'dolmatova3010@yandex.ru'
SMSAERO_API_KEY = os.getenv('API_KEY')
def send_sms(phone: int, message: str) -> dict:
    """
    Sends an SMS message

    Parameters:
    phone (int): The phone number to which the SMS message will be sent.
    message (str): The content of the SMS message to be sent.

    Returns:
    dict: A dictionary containing the response from the SmsAero API.
    """
    api = SmsAero(SMSAERO_EMAIL, SMSAERO_API_KEY)
    return api.send_sms(phone, message)
# class SMSAero:
#     def __init__(self, api_user, api_key):
#         self.api_user = api_user
#         self.api_key = api_key
#         self.base_url = "https://smsaero.ru/api/"
#
#     # https: // email: api_key @ gate.smsaero.ru / v2 / sms / send?number = 79990000000 & text = your + text & sign = SMS
#     # Aero
#     def send_sms(self, phone_number, code):
#         url = f"{self.base_url}sms/send"
#         payload = {
#             "number": phone_number,
#             "text": f"Ваш код авторизации: {code}",
#             "sign": "SMSAero"
#         }
#         headers = {
#             "Content-Type": "application/json"
#         }
#
#         response = requests.post(url, json=payload, auth=(self.api_user, self.api_key), headers=headers)
#
#         if response.status_code == 200:
#             return response.json()  # Возвращаем ответ от API
#         else:
#             raise Exception(f"Ошибка отправки SMS: {response.text}")
#
#
# def send_sms(phone_number, code):
#     print(f"Sending SMS to {phone_number}: Your code is {code}")
# def send_sms(self, phone_number, message):
#     """
#     Отправка SMS с кодом на указанный номер телефона с использованием SMS Aero API.
#     """
#     try:
#         return send_sms(phone_number, message)  # Вызов функции отправки SMS
#     except Exception as e:
#         # Логируем ошибку и возвращаем None
#         print(f"Ошибка при отправке SMS: {e}")
#         return {'status': 'error'}
import typing
import sys

from smsaero import SmsAero, SmsAeroException


# def send_sms(email: str, api_key: str, phone: int, message: str) -> typing.Optional[dict]:
#     """
#     Sends an SMS message via SmsAero.
#
#     :param email: The email registered with SmsAero.
#     :param api_key: The API key from SmsAero.
#     :param phone: The phone number to send the SMS message to.
#     :param message: The text of the message to be sent.
#     :return: Returns a dictionary with the response data from SmsAero, or None if the message was not sent.
#     """
#     api = SmsAero(email, api_key)
    # return api.send_sms(phone, message)
#
#
# def generate_verification_code():
#     return str(random.randint(1000, 9999))
#
#
# def request_verification_code(phone_number):
#     code = generate_verification_code()
#     send_sms(phone_number, code)
#     time.sleep(2)  # Имитация задержки
#     return code

class SMSAero:
    def __init__(self, api_user, api_key):
        self.api_user = api_user
        self.api_key = api_key
        self.base_url = "https://smsaero.ru/api/"

    def send_sms(self, phone_number, code):
        url = f"{self.base_url}sms/send"
        payload = {
            "number": phone_number,
            "text": f"Ваш код авторизации: {code}",
            "sign": "SMSAero"
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, auth=(self.api_user, self.api_key), headers=headers)

        if response.status_code == 200:
            return response.json()  # Возвращаем ответ от API
        else:
            raise Exception(f"Ошибка отправки SMS: {response.text}")

    # Пример использования
# if __name__ == "__main__":
#     api_user = "your_api_user"  # Замените на Ваш API пользователь
#     api_key = "your_api_key"  # Замените на Ваш API ключ
#     phone_number = "+1234567890"  # Замените на номер телефона
#     code = "1234"  # Генерируемый код
#
#     sms_aero = SMSAero(api_user, api_key)
#     try:
#         response = sms_aero.send_sms(phone_number, code)
#         print("SMS отправлено:", response)
#     except Exception as e:
#         print(e)

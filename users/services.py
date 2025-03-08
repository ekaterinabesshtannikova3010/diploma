import os
import random
import time
import requests
from dotenv import load_dotenv
from smsaero import SmsAero, SmsAeroException

load_dotenv()

api_user = os.getenv('API_USER')
api_key = os.getenv('API_KEY')

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


class SMSAero:
    def __init__(self, api_user, api_key):
        self.api_user = api_user
        self.api_key = api_key
        self.base_url = "https://smsaero.ru/api/"

    def send_sms(self, phone_number: str, code: str):
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

    api_user = os.getenv('API_USER')
    api_key = os.getenv('API_KEY')

    SMSAERO_EMAIL = 'dolmatova3010@yandex.ru'
    SMSAERO_API_KEY = os.getenv('API_KEY')

    # Пример использования


if __name__ == "__main__":
    api_user = os.getenv('API_USER')  # Замените на Ваш API пользователь
    api_key = os.getenv('API_KEY')  # Замените на Ваш API ключ
    phone_number = "89521775201"  # Замените на номер телефона
    code = "1234"  # Генерируемый код

    sms_aero = SMSAero(api_user, api_key)
    try:
        response = sms_aero.send_sms(phone_number, code)
        print("SMS отправлено:", response)
    except Exception as e:
        print(e)

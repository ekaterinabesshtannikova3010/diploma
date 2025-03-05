import logging

from django.conf import settings
from smsaero import SmsAero, SmsAeroException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def send_sms(phone: int, message: str) -> bool:
    api = SmsAero(settings.SMSAERO_EMAIL, settings.SMSAERO_API_KEY)
    logger.debug('Отправка SMS на номер: %s. Сообщение: %s', phone, message)

    try:
        response_data = api.send_sms(phone, message)
    except SmsAeroException as e:
        logger.error(f'Failed to send sms due error %s', e)
        return False

    is_success = response_data['success']
    if not is_success:
        logger.error('Invalid smsaero response: %s', response_data)
        return False

    return True

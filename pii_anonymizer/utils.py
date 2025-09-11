import hashlib
import re
import phonenumbers
from phonenumbers import NumberParseException


def short_hash(text: str, length: int = 6) -> str:
    """Генерирует короткий md5-хэш из строки"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:length]


def normalize_phone(phone: str) -> str:
    """
    Нормализует телефонный номер в международный формат E.164.
    Для российских номеров: +7XXXXXXXXXX.
    Для других стран - соответствующий международный формат.
    :param phone: телефонный номер
    :return: нормализованный телефонный номер
    """
    try:
        # Пробуем разобрать номер с регионом RU по умолчанию
        parsed = phonenumbers.parse(phone, "RU")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
    except NumberParseException:
        pass

    # Для невалидных номеров или номеров, которые не удалось разобрать
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("8"):
        return "+7" + digits[1:]
    elif len(digits) == 10:
        return "+7" + digits
    return f"+{digits}" if digits else ""

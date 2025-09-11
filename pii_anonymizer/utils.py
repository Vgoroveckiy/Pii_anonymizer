import hashlib
import re
import phonenumbers
from phonenumbers import NumberParseException


def short_hash(text: str, length: int = 6) -> str:
    """
    Генерирует короткий md5-хэш из строки.

    Args:
        text (str): Исходная строка для хеширования
        length (int, optional): Длина возвращаемого хеша. По умолчанию 6.

    Returns:
        str: Хеш-строка заданной длины

    Пример:
        >>> short_hash("example")
        '1a79a4'
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:length]


def normalize_phone(phone: str) -> str:
    """
    Нормализует телефонный номер в международный формат E.164.

    Алгоритм:
    1. Пытается разобрать номер с помощью библиотеки phonenumbers (с регионом RU)
    2. Если номер валиден - возвращает в формате E.164
    3. Для невалидных номеров или номеров, которые не удалось разобрать:
        - Удаляет все нецифровые символы
        - Для российских номеров (начинающихся с 8 или длиной 10 цифр) приводит к формату +7...
        - Для других номеров добавляет знак '+' в начало

    Args:
        phone (str): Телефонный номер в произвольном формате

    Returns:
        str: Нормализованный телефонный номер в международном формате E.164

    Примеры:
        >>> normalize_phone("8 (999) 123-45-67")
        '+79991234567'
        >>> normalize_phone("+7 999 123 4567")
        '+79991234567'
        >>> normalize_phone("invalid")
        '+'
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

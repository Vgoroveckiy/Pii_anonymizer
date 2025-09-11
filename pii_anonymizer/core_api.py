import uuid
from typing import Tuple

from .core import PIIAnonymizer


def sanitize(text: str, session_id: str = None) -> Tuple[str, dict, str]:
    """
    Анонимизирует текст, заменяя PII-данные (имена, телефоны) на токены.
    Возвращает кортеж: (анонимизированный_текст, словарь_маппинга, session_id)

    Args:
        text: Текст для анонимизации
        session_id: Идентификатор сессии (если None, генерируется новый UUID)

    Returns:
        Tuple[str, dict, str]:
            - Анонимизированный текст
            - Словарь маппинга {токен: оригинальное_значение}
            - Идентификатор сессии

    Пример:
        sanitized, mapping, session_id = sanitize("Меня зовут Иван, телефон +79161234567")
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    anonymizer = PIIAnonymizer(session_id)
    sanitized_text = anonymizer.anonymize(text)

    # Получаем маппинг из хранилища
    mapping = anonymizer.store.load_session(session_id)
    return sanitized_text, mapping, session_id


def desanitize(text: str, mapping: dict) -> str:
    """
    Восстанавливает оригинальные PII-данные в тексте по предоставленному маппингу.

    Args:
        text: Текст с токенами (анонимизированный текст)
        mapping: Словарь маппинга {токен: оригинальное_значение}

    Returns:
        str: Текст с восстановленными PII-данными

    Пример:
        original_text = desanitize(sanitized_text, mapping)
    """
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text

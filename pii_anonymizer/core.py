import asyncio
from .extractor import PIIExtractor
from .replacer import PIIReplacer
from .store_factory import get_store  # Используем фабрику для создания хранилища
from .utils import normalize_phone


class PIIAnonymizer:
    """
    Основной класс для анонимизации и деанонимизации PII-данных в тексте.
    Не использует LLM, работает только с правилами для имён и телефонов.

    Args:
        session_id (str): Уникальный идентификатор сессии

    Attributes:
        extractor (PIIExtractor): Экстрактор сущностей
        replacer (PIIReplacer): Генератор токенов-заменителей
        store (RedisStore): Хранилище маппингов токен-значение
        session_id (str): Идентификатор текущей сессии

    Returns:
        PIIAnonymizer: Экземпляр анонимизатора

    Пример использования:
        >>> anonymizer = PIIAnonymizer("session-123")
        >>> sanitized = await anonymizer.anonymize("Иван, тел. 89161234567")
        >>> print(sanitized)
        "NAME_1, тел. PHONE_1"
        >>> restored = await anonymizer.deanonymize(sanitized)
        >>> print(restored)
        "Иван, тел. 89161234567"
    """

    def __init__(self, session_id: str):
        from .config import REDIS_CONFIG

        self.extractor = PIIExtractor()
        self.replacer = PIIReplacer()
        self.store = get_store(
            "redis", **REDIS_CONFIG
        )  # Используем только Redis с конфигурацией
        self.session_id = session_id

    async def anonymize(self, text: str) -> str:
        """
        Асинхронно анонимизирует PII-данные в тексте.

        Args:
            text (str): Исходный текст, содержащий PII-данные

        Returns:
            str: Текст с замененными PII-данными на токены
        """
        # Выносим CPU-intensive операцию в отдельный поток
        entities = await asyncio.to_thread(self.extractor.extract_all, text)
        replacements = []  # Список замен: (оригинал, плейсхолдер)

        # Обрабатываем телефоны
        for phone in entities["phone"]:
            normalized = normalize_phone(phone)
            placeholder = self.replacer.create_placeholder("phone", normalized)
            await self.store.save(self.session_id, placeholder, normalized, "phone")
            replacements.append((phone, placeholder))

            # Добавляем варианты для замены
            if phone.startswith("8") and len(phone) == 11:
                replacements.append(("+7" + phone[1:], placeholder))
            elif len(phone) == 10:
                replacements.append(("8" + phone, placeholder))

        # Обрабатываем имена
        for name in entities["name"]:
            placeholder = self.replacer.create_placeholder("name", name)
            await self.store.save(self.session_id, placeholder, name, "name")
            replacements.append((name, placeholder))

        # Сортируем по убыванию длины для правильной замены
        replacements.sort(key=lambda x: len(x[0]), reverse=True)

        # Выполняем все замены
        for original, placeholder in replacements:
            text = text.replace(original, placeholder)

        return text

    async def deanonymize(self, text: str) -> str:
        """
        Асинхронно восстанавливает оригинальный текст.

        Args:
            text (str): Текст, содержащий токены вместо PII-данных

        Returns:
            str: Текст с восстановленными PII-данными
        """
        mapping = await self.store.load_session(self.session_id)
        for placeholder, original in mapping.items():
            text = text.replace(placeholder, original)
        return text

import functools
from .config import PLACEHOLDER_PREFIX
from .utils import short_hash


class PIIReplacer:
    """
    Генерирует уникальные токены-заменители для PII-данных с использованием кэширования.

    Args:
        max_cache_size: Максимальный размер кэша для хранения сгенерированных токенов

    Attributes:
        cache (dict): Кэш для хранения сгенерированных токенов
        max_cache_size (int): Максимальный размер кэша

    Особенности:
        - Использует кэш для предотвращения дублирования токенов для одинаковых значений
        - При достижении max_cache_size кэш полностью очищается
        - Генерирует токены в формате: [ТИП_ХЕШ], где:
            ТИП - префикс из PLACEHOLDER_PREFIX (NAME или PHONE)
            ХЕШ - короткий хеш оригинального значения

    Пример использования:
        >>> replacer = PIIReplacer()
        >>> phone_token = replacer.create_placeholder("phone", "89161234567")
        >>> print(phone_token)
        [PHONE_1a2b3c]
    """

    def __init__(self, max_cache_size=1000):
        self.cache = {}
        self.max_cache_size = max_cache_size

    def create_placeholder(self, pii_type: str, original: str) -> str:
        """
        Создает токен-заменитель для PII-данных.

        Args:
            pii_type (str): Тип PII-данных ('name', 'phone')
            original (str): Оригинальное значение

        Returns:
            str: Токен-заменитель в формате [ТИП_ХЕШ], где:
                ТИП - префикс из PLACEHOLDER_PREFIX
                ХЕШ - короткий хеш оригинального значения (6 символов)

        Особенности:
            - Для одинаковых пар (pii_type, original) всегда возвращает одинаковый токен
            - При переполнении кэша (max_cache_size) кэш полностью очищается
        """
        key = (pii_type, original.lower())

        # Используем кэш
        if key in self.cache:
            return self.cache[key]

        # Очистка кэша при достижении лимита
        if len(self.cache) >= self.max_cache_size:
            self.cache.clear()

        prefix = PLACEHOLDER_PREFIX[pii_type]
        hash_part = short_hash(original)
        placeholder = f"[{prefix}_{hash_part}]"
        self.cache[key] = placeholder
        return placeholder

import functools
from .config import PLACEHOLDER_PREFIX
from .utils import short_hash


class PIIReplacer:
    """
    Генерирует уникальные токены-заменители для PII-данных с использованием кэширования.

    Args:
        max_cache_size: Максимальный размер кэша для хранения сгенерированных токенов

    Особенности:
        - Использует кэш для предотвращения дублирования токенов для одинаковых значений
        - Автоматически очищает кэш при достижении лимита
        - Генерирует токены в формате: [ТИП_ХЕШ]
    """

    def __init__(self, max_cache_size=1000):
        self.cache = {}
        self.max_cache_size = max_cache_size

    def create_placeholder(self, pii_type: str, original: str) -> str:
        """
        Создает токен-заменитель для PII-данных.

        Args:
            pii_type: Тип PII-данных ('name', 'phone')
            original: Оригинальное значение

        Returns:
            str: Токен-заменитель в формате [ТИП_ХЕШ]

        Процесс:
            1. Проверяет кэш на наличие готового токена
            2. При отсутствии генерирует новый токен
            3. Сохраняет в кэш для последующего использования
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

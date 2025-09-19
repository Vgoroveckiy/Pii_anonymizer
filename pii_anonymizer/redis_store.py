import aioredis
from aioredis import Redis


class RedisStore:
    """
    Асинхронное хранилище PII-данных в Redis с поддержкой TTL.

    Параметры инициализации:
        host (str): Хост Redis (обязательный)
        port (int): Порт Redis (обязательный)
        db (int): Номер базы данных (обязательный)
        ttl (int): Время жизни данных в секундах (обязательный)

    Исключения:
        ValueError: Если какой-либо из обязательных параметров не указан

    Возвращает:
        RedisStore: Экземпляр асинхронного хранилища Redis

    Пример использования:
        >>> store = RedisStore(host='192.168.1.139', port=6379, db=1, ttl=600)
        >>> await store.save("session-123", "PHONE_1", "+79161234567", "phone")
        >>> mapping = await store.load_session("session-123")
        >>> print(mapping)
        {'PHONE_1': '+79161234567'}
    """

    def __init__(self, host, port, db, ttl):
        """
        Инициализация асинхронного Redis-хранилища.

        Args:
            host (str): Хост Redis (обязательный)
            port (int): Порт Redis (обязательный)
            db (int): Номер базы данных (обязательный)
            ttl (int): Время жизни данных в секундах (обязательный)
        """
        if not host:
            raise ValueError("Redis host must be specified in configuration")
        if not port:
            raise ValueError("Redis port must be specified in configuration")
        if db is None:
            raise ValueError("Redis database number must be specified in configuration")
        if ttl is None:
            raise ValueError("Redis TTL must be specified in configuration")

        self.host = host
        self.port = port
        self.db = db
        self.ttl = ttl
        self.pool = None

    async def _get_connection(self):
        """Создает или возвращает существующий пул соединений"""
        if not self.pool:
            from .config import REDIS_CONFIG

            self.pool = await aioredis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                max_connections=REDIS_CONFIG[
                    "pool_size"
                ],  # Используем значение из конфигурации
            )
        return self.pool

    async def save(self, session_id, placeholder, original, pii_type):
        """
        Асинхронно сохраняет PII-данные в Redis.

        Args:
            session_id (str): Уникальный идентификатор сессии
            placeholder (str): Токен-заменитель
            original (str): Оригинальное значение
            pii_type (str): Тип PII-данных (например, 'phone', 'name')

        Returns:
            None
        """
        conn = await self._get_connection()
        key = f"pii_map:{session_id}"
        # Сохраняем в хэш Redis: ключ хэша = placeholder, значение = original
        await conn.hset(key, placeholder, original)
        # Устанавливаем TTL для всего хэша
        await conn.expire(key, self.ttl)

    async def load_session(self, session_id):
        """
        Асинхронно загружает все PII-данные для указанной сессии.

        Args:
            session_id (str): Идентификатор сессии

        Returns:
            dict: Словарь, где ключи - токены-заменители, значения - оригинальные данные.
                   Возвращает пустой словарь, если сессия не найдена.
        """
        conn = await self._get_connection()
        key = f"pii_map:{session_id}"
        # Получаем все пары ключ-значение из хэша
        mapping = await conn.hgetall(key)

        # Проверяем что данные есть и преобразуем в обычный dict
        if mapping:
            return {k: v for k, v in mapping.items()}
        return {}

    async def ping(self):
        """
        Асинхронно проверяет соединение с Redis.

        Возвращает:
            bool: True если соединение активно, False если произошла ошибка
        """
        try:
            conn = await self._get_connection()
            return await conn.ping()
        except aioredis.ConnectionError:
            return False

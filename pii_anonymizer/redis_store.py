import redis.asyncio as redis


class RedisStore:
    """
    Асинхронное хранилище PII-данных в Redis с использованием redis-py (асинхронный режим).

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
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    async def save(self, session_id, placeholder, original, pii_type):
        key = f"pii_map:{session_id}"
        # Сохраняем в хэш Redis: ключ хэша = placeholder, значение = original
        await self.redis.hset(key, placeholder, original)
        # Устанавливаем TTL для всего хэша
        await self.redis.expire(key, self.ttl)

    async def load_session(self, session_id):
        key = f"pii_map:{session_id}"
        # Получаем все пары ключ-значение из хэша
        mapping = await self.redis.hgetall(key)
        return mapping or {}

    async def close(self):
        """Закрывает соединение с Redis"""
        await self.redis.close()

    async def ping(self):
        try:
            return await self.redis.ping()
        except redis.RedisError:
            return False

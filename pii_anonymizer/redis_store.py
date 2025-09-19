import aioredis


class RedisStore:
    """
    Асинхронное хранилище PII-данных в Redis с поддержкой TTL (совместимость с aioredis 1.3.1).

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

    def __init__(self, host, port, db, ttl, pool_size=100):
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
        self.pool_size = pool_size
        self.pool = None

    async def _get_pool(self):
        """Создает или возвращает существующий пул соединений"""
        if not self.pool:
            from .config import REDIS_CONFIG

            # Создаем пул соединений для aioredis 1.3.1
            self.pool = await aioredis.create_pool(
                (self.host, self.port),
                db=self.db,
                encoding="utf-8",
                minsize=1,
                maxsize=self.pool_size,
            )
        return self.pool

    async def save(self, session_id, placeholder, original, pii_type):
        pool = await self._get_pool()
        key = f"pii_map:{session_id}"
        async with pool.get() as conn:
            # Сохраняем в хэш Redis: ключ хэша = placeholder, значение = original
            await conn.execute("hset", key, placeholder, original)
            # Устанавливаем TTL для всего хэша
            await conn.execute("expire", key, self.ttl)

    async def load_session(self, session_id):
        pool = await self._get_pool()
        key = f"pii_map:{session_id}"
        async with pool.get() as conn:
            # Получаем все пары ключ-значение из хэша
            mapping_list = await conn.execute("hgetall", key)
            # Преобразуем список [k1, v1, k2, v2] в словарь {k1: v1, k2: v2}
            if not mapping_list:
                return {}
            it = iter(mapping_list)
            return dict(zip(it, it))

    async def ping(self):
        try:
            pool = await self._get_pool()
            async with pool.get() as conn:
                return await conn.execute("ping") == b"PONG"
        except aioredis.RedisError:
            return False

import redis


class RedisStore:
    """
    Хранилище PII-данных в Redis с поддержкой TTL.

    Параметры инициализации:
        host (str): Хост Redis (обязательный)
        port (int): Порт Redis (обязательный)
        db (int): Номер базы данных (обязательный)
        ttl (int): Время жизни данных в секундах (обязательный)

    Исключения:
        ValueError: Если какой-либо из обязательных параметров не указан

    Пример использования:
        >>> store = RedisStore(host='192.168.1.139', port=6379, db=1, ttl=600)
        >>> store.save("session-123", "PHONE_1", "+79161234567", "phone")
        >>> mapping = store.load_session("session-123")
        >>> print(mapping)
        {'PHONE_1': '+79161234567'}
    """

    def __init__(self, host, port, db, ttl):
        """
        Инициализация Redis-хранилища.

        :param host: Хост Redis (обязательный)
        :param port: Порт Redis (обязательный)
        :param db: Номер базы данных (обязательный)
        :param ttl: Время жизни данных в секундах (обязательный)
        """
        if not host:
            raise ValueError("Redis host must be specified in configuration")
        if not port:
            raise ValueError("Redis port must be specified in configuration")
        if db is None:
            raise ValueError("Redis database number must be specified in configuration")
        if ttl is None:
            raise ValueError("Redis TTL must be specified in configuration")

        self.r = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,  # Автоматическое декодирование в строки
        )
        self.ttl = ttl

    def save(self, session_id, placeholder, original, pii_type):
        """
        Сохраняет PII-данные в Redis.

        Параметры:
            session_id (str): Уникальный идентификатор сессии
            placeholder (str): Токен-заменитель
            original (str): Оригинальное значение
            pii_type (str): Тип PII-данных (например, 'phone', 'name')

        Действия:
            1. Создает ключ в формате "pii_map:{session_id}"
            2. Сохраняет пару placeholder-original в Redis Hash
            3. Устанавливает TTL для всего хэша
        """
        key = f"pii_map:{session_id}"
        # Сохраняем в хэш Redis: ключ хэша = placeholder, значение = original
        self.r.hset(key, placeholder, original)
        # Устанавливаем TTL для всего хэша
        self.r.expire(key, self.ttl)

    def load_session(self, session_id):
        """
        Загружает все PII-данные для указанной сессии.

        Параметры:
            session_id (str): Идентификатор сессии

        Возвращает:
            dict: Словарь вида {placeholder: original} или пустой словарь, если сессия не найдена
        """
        key = f"pii_map:{session_id}"
        # Получаем все пары ключ-значение из хэша
        mapping = self.r.hgetall(key)

        # Проверяем что данные есть и преобразуем в обычный dict
        if mapping:
            return {k: v for k, v in mapping.items()}
        return {}

    def ping(self):
        """
        Проверяет соединение с Redis.

        Возвращает:
            bool: True если соединение активно, False если произошла ошибка
        """
        try:
            return self.r.ping()
        except redis.exceptions.ConnectionError:
            return False

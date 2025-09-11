import redis
from typing import Optional, Dict


class RedisStore:
    """Реализация хранилища для маппингов токен-значение на базе Redis.

    Args:
        config (dict): Конфигурация подключения к Redis, включая:
            host (str): Хост Redis
            port (int): Порт Redis
            db (int): Номер базы данных Redis
            password (str, optional): Пароль для аутентификации
            ttl (int, optional): Время жизни записей в секундах (по умолчанию 3600)

    Attributes:
        client (redis.Redis): Клиент Redis
        ttl (int): Время жизни записей в секундах

    Пример использования:
        >>> config = {"host": "localhost", "port": 6379, "db": 0}
        >>> store = RedisStore(config)
        >>> store.save_mapping("token1", "value1")
        >>> value = store.get_mapping("token1")
        >>> print(value)
        "value1"
    """

    def __init__(self, config: Dict):
        """
        Инициализирует клиент Redis с заданной конфигурацией.

        Args:
            config: Словарь с параметрами подключения к Redis
        """
        self.client = redis.Redis(
            host=config["host"],
            port=config["port"],
            db=config["db"],
            password=config.get("password"),
            decode_responses=True,
        )
        self.ttl = config.get("ttl", 3600)  # TTL по умолчанию 1 час
        self.client = redis.Redis(
            host=config["host"],
            port=config["port"],
            db=config["db"],
            password=config.get("password"),
            decode_responses=True,
        )
        self.ttl = config.get("ttl", 3600)

    def save_mapping(self, token: str, value: str) -> None:
        """Сохраняет маппинг токен-значение в Redis с установленным TTL.

        Args:
            token (str): Токен-ключ
            value (str): Сохраняемое значение

        Raises:
            redis.RedisError: В случае ошибки подключения или записи в Redis
        """
        self.client.set(token, value, ex=self.ttl)

    def get_mapping(self, token: str) -> Optional[str]:
        """Возвращает значение по токену или None если не найдено.

        Args:
            token (str): Токен-ключ для поиска

        Returns:
            str | None: Найденное значение или None

        Raises:
            redis.RedisError: В случае ошибки подключения к Redis
        """
        return self.client.get(token)

    def delete_mapping(self, token: str) -> None:
        """Удаляет маппинг по токену.

        Args:
            token (str): Токен-ключ для удаления

        Raises:
            redis.RedisError: В случае ошибки подключения к Redis
        """
        self.client.delete(token)

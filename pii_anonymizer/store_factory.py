from .redis_store import RedisStore


def get_store(store_type, **kwargs):
    """
    Фабрика для создания экземпляров хранилища.

    Args:
        store_type (str): Тип хранилища (поддерживается только 'redis')
        **kwargs: Дополнительные параметры для инициализации хранилища.
                  Для RedisStore: host, port, db, ttl

    Returns:
        Store: Экземпляр хранилища (в текущей реализации RedisStore)

    Raises:
        ValueError: Если указан неподдерживаемый тип хранилища

    Пример использования:
        >>> from pii_anonymizer.store_factory import get_store
        >>> store = get_store("redis", host="localhost", port=6379, db=0, ttl=3600)
        >>> type(store)
        <class 'pii_anonymizer.redis_store.RedisStore'>
    """
    if store_type == "redis":
        # Передаем только необходимые параметры для RedisStore
        required_params = {
            "host": kwargs.get("host"),
            "port": kwargs.get("port"),
            "db": kwargs.get("db"),
            "ttl": kwargs.get("ttl"),
        }
        return RedisStore(**required_params)
    else:
        raise ValueError(f"Unsupported store type: {store_type}")

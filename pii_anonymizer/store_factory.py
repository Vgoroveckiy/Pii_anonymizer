from .redis_store import RedisStore


def get_store(store_type, **kwargs):
    """
    Фабрика для создания экземпляров хранилища.

    Параметры:
        store_type (str): Тип хранилища (поддерживается только 'redis')
        **kwargs: Дополнительные параметры для инициализации хранилища

    Возвращает:
        Экземпляр хранилища

    Исключения:
        ValueError: Если указан неподдерживаемый тип хранилища
    """
    if store_type == "redis":
        return RedisStore(**kwargs)
    else:
        raise ValueError(f"Unsupported store type: {store_type}")

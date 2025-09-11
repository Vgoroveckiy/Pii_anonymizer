import redis
from typing import Optional


class RedisStore:
    def __init__(self, config):
        self.client = redis.Redis(
            host=config["host"],
            port=config["port"],
            db=config["db"],
            password=config.get("password"),
            decode_responses=True,
        )
        self.ttl = config.get("ttl", 3600)

    def save_mapping(self, token: str, value: str) -> None:
        """Сохраняет маппинг токен-значение в Redis"""
        self.client.set(token, value, ex=self.ttl)

    def get_mapping(self, token: str) -> Optional[str]:
        """Возвращает значение по токену или None если не найдено"""
        return self.client.get(token)

    def delete_mapping(self, token: str) -> None:
        """Удаляет маппинг по токену"""
        self.client.delete(token)

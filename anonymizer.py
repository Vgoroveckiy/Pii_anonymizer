import os
import uuid
import json
from functools import wraps
from quart import Quart, request, jsonify
from pii_anonymizer import PIIAnonymizer
from pii_anonymizer.config import REDIS_CONFIG, SESSION_TTL_MINUTES
from pii_anonymizer.redis_store import RedisStore

# Конфигурация файла токенов
TOKENS_FILE = "tokens.json"

app = Quart(__name__)

# Инициализация хранилища
store = RedisStore(**REDIS_CONFIG)


# --- Декоратор для проверки API ключа ---
def require_api_key(scope=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            api_key = request.headers.get("X-API-KEY")
            if not api_key:
                return jsonify({"error": "API key is missing"}), 401

            tokens = load_tokens()
            token_data = tokens.get(api_key)

            if not token_data:
                return jsonify({"error": "Invalid API key"}), 401

            # Проверка разрешений (scopes)
            required_scopes = scope if isinstance(scope, list) else [scope]
            user_scope = token_data.get("scope")
            if scope and user_scope not in required_scopes:
                return jsonify({"error": "Insufficient permissions"}), 403

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def load_tokens():
    """Загружает токены из файла"""
    if not os.path.exists(TOKENS_FILE):
        return {}
    try:
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_tokens(tokens):
    """Сохраняет токены в файл"""
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


@app.route("/generate-token", methods=["POST"])
async def generate_token():
    """Генерирует уникальный токен сессии"""
    data = await request.get_json()
    scope = data.get("scope", "read")

    if scope not in ["read", "full"]:
        return jsonify({"error": "Invalid scope. Use 'read' or 'full'"}), 400

    token = str(uuid.uuid4())
    tokens = load_tokens()
    tokens[token] = {"scope": scope}
    save_tokens(tokens)

    return jsonify({"token": token}), 201


@app.route("/anonymize", methods=["POST"])
@require_api_key(scope="full")
async def anonymize_text():
    """Анонимизирует текст и возвращает session_id"""
    data = await request.get_json()
    text = data.get("text")

    if not text:
        return jsonify({"error": "Text is required"}), 400

    # Генерируем session_id для операции
    session_id = str(uuid.uuid4())
    anonymizer = PIIAnonymizer(session_id)
    anonymized_text = anonymizer.anonymize(text)

    return jsonify({"sanitized": anonymized_text, "session_id": session_id})


@app.route("/restore", methods=["POST"])
@require_api_key(scope=["read", "full"])
async def restore_text():
    """Восстанавливает текст по session_id"""
    data = await request.get_json()
    sanitized = data.get("sanitized")
    session_id = data.get("session_id")

    if not sanitized:
        return jsonify({"error": "Sanitized text is required"}), 400
    if not session_id:
        return jsonify({"error": "Session ID is required"}), 400

    anonymizer = PIIAnonymizer(session_id)
    restored_text = anonymizer.deanonymize(sanitized)

    return jsonify({"restored_text": restored_text})


@app.route("/status", methods=["GET"])
@require_api_key(scope=["read", "full"])
async def service_status():
    """Проверяет статус сервиса и подключение к Redis"""
    try:
        is_connected = store.ping()
        return jsonify(
            {
                "status": "running",
                "redis_connected": is_connected,
                "session_ttl_minutes": SESSION_TTL_MINUTES,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# Используем официальный образ Python
FROM docker-hub.vgorovetskiy.keenetic.pro/python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта
COPY . .

# Запускаем приложение через ASGI-сервер Hypercorn
CMD ["hypercorn", "anonymizer:app", "--bind", "0.0.0.0:5000"]

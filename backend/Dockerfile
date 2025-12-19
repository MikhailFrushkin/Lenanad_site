# Dockerfile
FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt /app/

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем остальной код проекта
COPY . /app/

# Создаем директорию для статики
RUN mkdir -p /app/static /app/media /app/django_cache

# Создаем не-root пользователя для безопасности
RUN adduser --disabled-password --gecos '' django-user && \
    chown -R django-user:django-user /app
USER django-user

# Открываем порт
EXPOSE 8000

# Команда по умолчанию
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "backend.wsgi:application"]
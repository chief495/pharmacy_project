# ============== BUILD STAGE ==============
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Настройки UV для оптимизации
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

# Создаем виртуальное окружение в отдельной директории
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файлы зависимостей
COPY pyproject.toml uv.lock /app/
WORKDIR /app

# Генерируем requirements.txt и устанавливаем зависимости
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip compile -q pyproject.toml -o requirements.txt && \
    uv pip install --no-deps -r requirements.txt

# Копируем весь остальной код
COPY . /app

# ============== RUNTIME STAGE ==============
FROM python:3.13-slim-bookworm

# Устанавливаем системные зависимости для runtime
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем виртуальное окружение из builder-стадии
COPY --from=builder /opt/venv /opt/venv

# Копируем код приложения
COPY --from=builder /app /app

# Настраиваем окружение
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
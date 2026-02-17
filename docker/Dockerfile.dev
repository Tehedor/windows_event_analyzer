# --- Etapa 1: Builder ---
FROM python:3.12.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /install

# Dependencias necesarias SOLO para compilar wheels
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libdbus-1-dev \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo requirements para cachear mejor
COPY app/requirements.txt .

# Instalamos dependencias en un prefijo aislado
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Etapa 2: Runtime ---
FROM python:3.12.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiamos SOLO las librerías ya compiladas
COPY --from=builder /install /usr/local

# Copiamos el código fuente
COPY app/ .

# Limpieza opcional
RUN find . -name "__pycache__" -type d -exec rm -rf {} +

EXPOSE 8050

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8050"]
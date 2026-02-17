# Dockerfile
FROM python:3.12.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libdbus-1-dev \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY ../app .
# Exponer el puerto
EXPOSE 8050

# COMANDO DE ARRANQUE (Crucial)
CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server", "--workers=1", "--threads=1"]  
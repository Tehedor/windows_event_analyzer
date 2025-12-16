# Dockerfile
FROM python:3.13.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY ../app .
# Exponer el puerto
EXPOSE 8050

# COMANDO DE ARRANQUE (Crucial)
CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server", "--workers=1", "--threads=1"]  
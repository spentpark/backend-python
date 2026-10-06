# --- Stage 1: Build de dependencias ---
FROM python:3.14-slim AS builder

WORKDIR /build

# aiomysql usa PyMySQL (Python puro) y no enlaza con libmariadb, por lo que no
# se instalan cabeceras de MariaDB. gcc/python3-dev se mantienen por si alguna
# dependencia no publica wheel para Python 3.14 (no afectan a la imagen final).
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Se instalan en un prefijo local para copiarlas al stage final
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Stage 2: Imagen final ---
FROM python:3.14-slim

# Sin archivos .pyc en el contenedor y logs sin buffer (visibles al instante
# en `docker logs`). El bytecode de site-packages ya se generó en el builder.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias Python instaladas en el stage de build
COPY --from=builder /install /usr/local

# Usuario no root. Se crea antes de copiar el código para poder asignar la
# propiedad con `COPY --chown` y evitar una capa extra con `chown -R`.
RUN adduser --disabled-password --gecos "" --no-create-home appuser

# Código de la aplicación
COPY --chown=appuser:appuser app/ ./app/

# Credenciales: se copian para mantener el arranque actual, pero lo recomendable
# es inyectarlas en runtime (`docker run --env-file .env ...`) para no dejarlas
# embebidas en la imagen.
COPY --chown=appuser:appuser .env .env

USER appuser

EXPOSE 8000

# Healthcheck sin dependencias externas (usa solo la librería estándar)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

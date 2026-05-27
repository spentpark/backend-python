# --- Stage 1: Build ---
FROM python:3.13-slim as builder

# Evitar que Python genere archivos .pyc y activar el buffer de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Instalar dependencias del sistema necesarias para compilar paquetes de Python
# (gcc y libmariadb son necesarios para aiomysql/cryptography si no hay wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias en una carpeta local para luego copiarla
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Stage 2: Final ---
FROM python:3.13-slim

WORKDIR /app

# Copiar las librerías instaladas desde el stage anterior
COPY --from=builder /install /usr/local

# Instalar librerías de ejecución necesarias para MariaDB
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Copiar el código de la aplicación
# (Asegúrate de que el contexto de build sea la raíz del proyecto)
COPY app/ ./app/

# Crear un usuario no root por seguridad
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Exponer el puerto de FastAPI
EXPOSE 8000

# Comando para ejecutar la aplicación
# Usamos el módulo app.main para que reconozca los paquetes correctamente
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

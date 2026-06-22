# =============================================================
# Dockerfile - App web Flask (Inventario ITU)
# =============================================================
# pymssql trae sus binarios (FreeTDS) en la wheel, asi que NO
# hace falta instalar el driver ODBC de Microsoft. La imagen
# queda mas liviana que con msodbcsql18.
# =============================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# pymssql necesita estas libs del sistema para compilar/conectar.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc freetds-dev freetds-bin \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario no-root (buena practica de seguridad)
RUN useradd -m appuser
USER appuser

EXPOSE 5000

# La app esta en frontend/src/app.py -> objeto "app"
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "2", \
     "--timeout", "60", "--chdir", "frontend/src", "app:app"]

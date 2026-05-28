# Imagen del backend: motor de análisis y pronóstico bursátil (API HTTP).
FROM python:3.11-slim

WORKDIR /app

COPY requirements-engine.txt ./
RUN pip install --no-cache-dir -r requirements-engine.txt

COPY engine ./engine

EXPOSE 8000

# Sobreescribe host/puerto con CMD si lo necesitas.
CMD ["python", "-m", "engine.api", "--host", "0.0.0.0", "--port", "8000"]

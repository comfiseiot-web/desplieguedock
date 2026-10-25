# 1. Imagen base: la misma versión de Python que usó Colab para entrenar
FROM python:3.13-slim

# 2. Carpeta de trabajo dentro del contenedor
WORKDIR /app

# 3. Primero solo los requisitos (así Docker reutiliza esta capa si no cambian)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Después el código, el modelo y su ficha técnica
COPY main.py modelo.joblib metadata.json ./

# 5. Puerto en el que escucha la API
EXPOSE 8000

# 6. Comando que se ejecuta al arrancar el contenedor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
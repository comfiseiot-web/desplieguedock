"""
API de sensación térmica — Módulo 12 (Virtualización y Despliegue en la Nube)

Carga el modelo entrenado en Colab (Paso 1) y lo expone como un servicio web.
Ejecutar desde la carpeta app/:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
Documentación interactiva: /docs
"""

import json
import socket
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

CARPETA = Path(__file__).parent
FEATURES = ["temperatura", "humedad"]

# Aquí quedan el modelo y su ficha técnica una vez cargados
recursos = {}


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Se ejecuta UNA vez, al arrancar el servidor (no en cada petición)
    recursos["modelo"] = joblib.load(CARPETA / "modelo.joblib")
    recursos["metadata"] = json.loads((CARPETA / "metadata.json").read_text(encoding="utf-8"))
    print(f"✅ Modelo cargado: {recursos['metadata']['modelo']}")
    yield
    recursos.clear()


app = FastAPI(
    title="API de sensación térmica",
    description="Predice la sensación térmica a partir de la temperatura y la humedad de un ESP32.",
    version="1.0",
    lifespan=ciclo_de_vida,
)


class Lectura(BaseModel):
    temperatura: float = Field(..., description="Temperatura en °C", examples=[30])
    humedad: float = Field(..., description="Humedad relativa en %", examples=[80])


class Prediccion(BaseModel):
    sensacion_termica: float
    unidad: str
    modelo: str
    atendido_por: str


@app.get("/")
def inicio():
    """Información general del servicio y del modelo."""
    meta = recursos["metadata"]
    return {
        "servicio": "API de sensación térmica",
        "modelo": meta["modelo"],
        "entradas": meta["entradas"],
        "metricas_prueba": meta["metricas_prueba"],
        "documentacion": "/docs",
    }


@app.get("/salud")
def salud():
    """Responde si el servicio está vivo y el modelo cargado."""
    return {"estado": "ok", "modelo_cargado": "modelo" in recursos}


@app.post("/predecir", response_model=Prediccion)
def predecir(lectura: Lectura):
    """Recibe temperatura y humedad y devuelve la sensación térmica estimada."""
    meta = recursos["metadata"]

    # El modelo solo es confiable dentro del rango con el que se entrenó
    for variable in FEATURES:
        valor = getattr(lectura, variable)
        rango = meta["entradas"][variable]
        if not rango["min"] <= valor <= rango["max"]:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"{variable} = {valor} {rango['unidad']} está fuera del rango de entrenamiento "
                    f"({rango['min']} – {rango['max']} {rango['unidad']}). "
                    "El modelo no es confiable fuera de ese rango."
                ),
            )

    entrada = pd.DataFrame([[lectura.temperatura, lectura.humedad]], columns=FEATURES)
    resultado = float(recursos["modelo"].predict(entrada)[0])

    return Prediccion(
        sensacion_termica=round(resultado, 2),
        unidad=meta["salida"]["unidad"],
        modelo=meta["modelo"],
        atendido_por=socket.gethostname(),  # ¿quién respondió? (útil en el Paso 3)
    )

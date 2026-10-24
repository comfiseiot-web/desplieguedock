# Módulo 12 · Del modelo al contenedor

**Virtualización y Despliegue en la Nube — ERA 3**

En este laboratorio llevas el modelo de sensación térmica que entrenaste en Colab hasta un servicio web que corre en la nube.

| Paso | Dónde | Qué se hace |
|---|---|---|
| 1 | Colab | Entrenar y exportar el modelo |
| 2 | Codespaces | [Probar la API sin Docker](#paso-2--probar-la-api-sin-docker) |
| 3 | Codespaces | [Escribir el Dockerfile, construir la imagen y ejecutar el contenedor](#paso-3--del-código-al-contenedor) |
| 4 | GitHub | [Publicar la imagen y probarla en otra máquina](#paso-4--tu-imagen-en-cualquier-máquina) |

## Estructura del repositorio

```
.
├── .devcontainer/
│   └── devcontainer.json   ← describe la máquina del Codespace (Python + Docker)
├── .github/workflows/
│   └── publicar-imagen.yml ← publica tu imagen sola con cada push (Paso 4)
├── app/
│   ├── main.py             ← la API (FastAPI)
│   ├── modelo.joblib       ← el modelo entrenado en Colab
│   ├── metadata.json       ← ficha técnica del modelo
│   ├── requirements.txt    ← versiones exactas de las librerías
│   └── Dockerfile          ← lo escribirás tú en el Paso 3
└── README.md
```

> El repositorio ya trae un modelo de respaldo. Si no terminaste el Paso 1, puedes continuar con ese.

---

## Paso 2 — Probar la API sin Docker

La pregunta de este paso es: **¿funciona mi código?** Todavía no usamos Docker. Así, si algo falla más adelante, sabremos que el problema es del contenedor y no de la API.

### 2.1 Crea tu copia del repositorio

1. En la página de este repositorio, pulsa **Use this template → Create a new repository**.
2. Créalo en **tu** cuenta y déjalo **Public**. Así el Codespace usará tu cuota gratuita y, en el Paso 4, tu imagen podrá descargarse desde cualquier máquina.

### 2.2 Abre el Codespace

1. En **tu** repositorio: botón verde **Code → pestaña Codespaces → Create codespace on main**.
2. Espera a que termine de prepararse. La primera vez tarda unos minutos, porque está instalando las librerías de `requirements.txt`.

Al terminar verás VS Code en el navegador, con el explorador de archivos a la izquierda y una terminal abajo.

### 2.3 Sube tus archivos del Paso 1 (opcional)

Si entrenaste tu propio modelo, arrastra tus tres archivos (`modelo.joblib`, `metadata.json` y `requirements.txt`) a la carpeta `app/` y acepta reemplazar los existentes.

Luego reinstala las librerías, porque tus versiones pueden ser distintas a las del respaldo:

```bash
pip install -r app/requirements.txt
```

### 2.4 Arranca la API

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Debes ver en la terminal:

```
✅ Modelo cargado: Polinómica grado 2
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Aparecerá un aviso abajo a la derecha: **Open in Browser**. Ábrelo. Si no lo ves, ve a la pestaña **PORTS** (junto a TERMINAL) y abre la dirección del puerto `8000`.

### 2.5 Prueba la API

Agrega `/docs` al final de la dirección que se abrió. Verás la documentación interactiva que FastAPI genera sola.

1. Abre **GET /** → *Try it out* → *Execute*. Revisa qué modelo está cargado y en qué rangos se entrenó.
2. Abre **POST /predecir** → *Try it out*, escribe:
   ```json
   { "temperatura": 30, "humedad": 80 }
   ```
   y pulsa *Execute*. Debes obtener una sensación térmica cercana a **37 °C**.
3. Ahora prueba con `"temperatura": 42`. ¿Qué responde la API? ¿Por qué crees que se diseñó así?
4. Prueba con `"temperatura": "calor"`. ¿Quién detectó el error: tu código o FastAPI?

También puedes probar desde una **segunda terminal** (botón **+** en el panel de terminales):

```bash
curl -X POST localhost:8000/predecir \
     -H "Content-Type: application/json" \
     -d '{"temperatura": 30, "humedad": 80}'
```

Fíjate en el campo `atendido_por` de la respuesta y anota su valor. Lo volverás a mirar en el Paso 3.

### 2.6 Detén la API

En la terminal donde corre `uvicorn`, pulsa **Ctrl + C**.

### ✅ Lista de verificación

- [ ] La terminal muestra `✅ Modelo cargado`.
- [ ] `/docs` abre en el navegador.
- [ ] `/predecir` responde ≈ 37 °C para 30 °C y 80 %.
- [ ] Una temperatura fuera de rango devuelve un error **422** con un mensaje claro.
- [ ] Anotaste el valor de `atendido_por`.

### Errores frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Error loading ASGI app. Could not import module "main"` | Ejecutaste `uvicorn` fuera de la carpeta `app/` | `cd app` y repite |
| `ModuleNotFoundError: No module named 'sklearn'` (u otra librería) | Las librerías no se instalaron | `pip install -r app/requirements.txt` desde la raíz |
| `InconsistentVersionWarning` o error al cargar `modelo.joblib` | Tu `requirements.txt` no coincide con las versiones con que se entrenó el modelo | Sube los tres archivos del **mismo** Colab y reinstala |
| La página del puerto no abre | El servidor no está corriendo o escucha en `127.0.0.1` | Verifica que usaste `--host 0.0.0.0` |
| `{"detail":"Not Found"}` | Escribiste en la dirección una ruta que no existe, por ejemplo `/post/predecir` | En la dirección solo se agrega `/docs`. El POST se hace desde esa página |
| `Address already in use` | Ya hay otro `uvicorn` corriendo | Ciérralo con Ctrl + C en la otra terminal |

### Para pensar antes del Paso 3

1. El Codespace ya tenía Python y tú instalaste las librerías a mano. Si un compañero tuviera otra versión de Python o de scikit-learn, ¿obtendría el mismo resultado?
2. ¿Qué tendrías que escribirle a alguien para que ejecute tu API en su propio computador? Esa lista de instrucciones es, casi literalmente, lo que será el **Dockerfile**.

---

## Paso 3 — Del código al contenedor

La pregunta de este paso es: **¿funciona mi contenedor?** La API ya funciona (Paso 2). Ahora la vas a empaquetar con su propio Python y sus propias librerías, para que corra igual en cualquier máquina.

Para eso escribirás un **Dockerfile**: la receta que Docker sigue, línea por línea, para construir una **imagen**. Al ejecutar esa imagen obtienes un **contenedor**.

> **Imagen** = la plantilla congelada (como una clase). **Contenedor** = una copia en ejecución de esa plantilla (como un objeto).

### 3.1 Las seis instrucciones que necesitas

| Instrucción | Qué hace | Ejemplo |
|---|---|---|
| `FROM` | Elige la imagen base: el sistema operativo y el Python de partida | `FROM python:3.11-slim` |
| `WORKDIR` | Crea una carpeta dentro del contenedor y se ubica en ella | `WORKDIR /proyecto` |
| `COPY` | Copia archivos de tu carpeta al contenedor | `COPY datos.csv .` |
| `RUN` | Ejecuta un comando **mientras se construye** la imagen | `RUN pip install numpy` |
| `EXPOSE` | Documenta en qué puerto escucha la aplicación | `EXPOSE 5000` |
| `CMD` | El comando que se ejecuta **cuando arranca** el contenedor | `CMD ["python", "app.py"]` |

Los ejemplos son genéricos: **no los copies tal cual**. Tu Dockerfile necesita otros valores.

### 3.2 Crea el archivo en el lugar correcto

1. Detén la API del Paso 2 si sigue corriendo (**Ctrl + C**).
2. En el explorador, haz **clic derecho sobre la carpeta `app` → Nuevo archivo**.
3. Nómbralo exactamente **`Dockerfile`**: con D mayúscula y **sin extensión** (no `Dockerfile.txt`).

Comprueba en la terminal que quedó junto a los demás archivos:

```bash
cd /workspaces/*/app
ls
```

Debes ver: `Dockerfile  main.py  metadata.json  modelo.joblib  requirements.txt`.

> Si el `Dockerfile` aparece fuera de `app/`, arrástralo con el ratón sobre la carpeta `app`.

### 3.3 Completa la receta

Copia esta plantilla en tu `Dockerfile` y **reemplaza cada `____`**. Las pistas de cada bloque te dicen dónde buscar la respuesta.

```dockerfile
# 1. Imagen base
#    Pista: abre metadata.json y busca con qué versión de Python se entrenó el modelo.
#    Usa solo mayor.menor (por ejemplo 3.11, no 3.11.4).
FROM python:____-slim

# 2. Carpeta de trabajo dentro del contenedor
WORKDIR /app

# 3. Instalar las librerías
#    Pista: ¿qué archivo tiene las versiones exactas? Primero se copia, luego se instala.
COPY ____ .
RUN pip install --no-cache-dir -r ____

# 4. Copiar lo que la API necesita para funcionar
#    Pista: el código, el modelo y su ficha técnica (tres archivos).
COPY ____ ____ ____ ./

# 5. Puerto de la API
#    Pista: el mismo que usaste en el Paso 2.
EXPOSE ____

# 6. Comando de arranque
#    Pista: es el mismo comando uvicorn del Paso 2, pero SIN --reload
#    (en producción el código no cambia), escrito como lista de palabras.
CMD ["uvicorn", "main:app", "--host", "____", "--port", "____"]
```

Antes de seguir, responde mentalmente: ¿por qué `RUN pip install` va **antes** de copiar `main.py`? Lo comprobarás en el desafío del final.

### 3.4 Construye la imagen

Desde la carpeta `app`:

```bash
docker build -t sensacion-api .
```

- `-t sensacion-api` le pone nombre a la imagen.
- El **punto final** le dice a Docker: "usa esta carpeta". Sin él, el comando falla.

La primera vez tarda uno o dos minutos. Verás cada instrucción de tu Dockerfile como un paso: `[1/5]`, `[2/5]`… El más lento es `RUN pip install`.

Cuando termine, comprueba que la imagen existe y mira su tamaño:

```bash
docker images
```

### 3.5 Ejecuta el contenedor

```bash
docker run --rm -p 8000:8000 sensacion-api
```

| Parte | Significado |
|---|---|
| `--rm` | Borra el contenedor cuando lo detengas (la imagen se conserva) |
| `-p 8000:8000` | Conecta el puerto 8000 del Codespace con el 8000 del contenedor |
| `sensacion-api` | La imagen de la que se crea el contenedor |

Debe aparecer de nuevo `✅ Modelo cargado`, pero esta vez **dentro del contenedor**.

### 3.6 ¿Quién responde ahora?

1. Abre la API: pestaña **Puertos** → globo 🌐 del puerto `8000` → agrega `/docs` a la dirección.
2. **POST /predecir → Try it out → Execute** con `{"temperatura": 30, "humedad": 80}`.
3. Anota `sensacion_termica` y `atendido_por`.
4. Abre una **segunda terminal** (botón **+**) y escribe:
   ```bash
   docker ps
   ```

Compara:

- `sensacion_termica` debe ser **la misma** del Paso 2.
- `atendido_por` **cambió**: ya no es el nombre del Codespace. Compáralo con la columna **CONTAINER ID** de `docker ps`.
- En los registros de la primera terminal, las peticiones ya no llegan desde tu IP, sino desde una dirección `172.17.x.x`: la red interna de Docker.

### 3.7 Detén el contenedor

En la terminal donde corre, **Ctrl + C**. Luego `docker ps` debe mostrar la lista vacía.

### 🧪 Desafío: la caché de Docker

1. Construye otra vez **sin cambiar nada**: `docker build -t sensacion-api .` ¿Cuánto tardó? ¿Qué dice junto a cada paso?
2. Abre `main.py`, cambia el texto de `description=` en `FastAPI(...)` y guarda.
3. Construye de nuevo. ¿Qué pasos se repitieron y cuáles dicen `CACHED`?
4. Explica con tus palabras por qué el Dockerfile copia `requirements.txt` antes que `main.py`. ¿Qué pasaría si copiaras todo en una sola línea al principio?

### ✅ Lista de verificación

- [ ] El `Dockerfile` está dentro de `app/`, sin extensión.
- [ ] `docker build` termina sin errores y `docker images` muestra `sensacion-api`.
- [ ] El contenedor muestra `✅ Modelo cargado`.
- [ ] `/predecir` responde la misma sensación térmica que en el Paso 2.
- [ ] `atendido_por` coincide con el **CONTAINER ID** de `docker ps`.
- [ ] Hiciste commit y push de tu `Dockerfile` (ver abajo).

### Guarda tu trabajo en GitHub

```bash
git add app/Dockerfile
git commit -m "Agrega Dockerfile de la API"
git push
```

Abre tu repositorio en GitHub y verifica que `app/Dockerfile` aparece. **Ese repositorio es tu entrega.** En el Paso 4 verás que este push hizo algo más.

### Errores frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `requires 1 argument` | Olvidaste el punto final de `docker build` | `docker build -t sensacion-api .` |
| `failed to read dockerfile: open Dockerfile: no such file or directory` | El `Dockerfile` no está en `app/`, tiene otro nombre (`dockerfile`, `Dockerfile.txt`) o la terminal no está en `app/` | Revisa con `ls` y corrige el nombre o la ubicación |
| `"/modelo.joblib": not found` (u otro archivo) | El archivo no existe en `app/` o está mal escrito en el `COPY` | Compara los nombres del `COPY` con los de `ls` |
| `pip install` falla con un error largo (`No matching distribution found`, `subprocess-exited-with-error`) | La versión de Python en `FROM` no es la del entrenamiento: las librerías fijadas no existen para esa versión | Usa la versión de `metadata.json` |
| `port is already allocated` o `address already in use` | La API del Paso 2 u otro contenedor ya ocupa el puerto 8000 | Ctrl + C en la otra terminal, o `docker ps` y `docker stop <id>` |
| El contenedor arranca pero la página no abre | Falta `-p 8000:8000` en `docker run`, o en `CMD` usaste otro host distinto de `0.0.0.0` | Revisa el comando y el `CMD` |
| Los cambios en `main.py` no aparecen | El contenedor usa la imagen **construida antes** del cambio | Vuelve a ejecutar `docker build` y luego `docker run` |

### Para pensar antes del Paso 4

1. En el Paso 2 el Codespace tenía Python 3.12. ¿Qué versión tiene el contenedor? ¿Por qué no importa cuál tenga el Codespace?
2. Ahora tu API solo existe mientras tu Codespace está encendido. ¿Qué necesitarías para que un compañero ejecute **tu imagen** en su computador sin tener tu código?

---

## Paso 4 — Tu imagen en cualquier máquina

La pregunta de este paso es: **¿funciona en otra máquina?** Tu imagen ya está publicada: el push del Paso 3 se encargó de eso. Ahora la vas a encontrar y a ejecutar en una máquina que no tiene tu código.

### 4.1 Mira lo que hizo tu push

1. En tu repositorio de GitHub, abre la pestaña **Actions**.
2. Verás una ejecución con el mensaje de tu commit (*"Agrega Dockerfile de la API"*). Haz clic en ella y luego en **publicar** para ver cada paso.
3. Espera el ✅ verde (uno o dos minutos).

GitHub leyó tu `Dockerfile`, construyó la imagen en sus servidores y la publicó. Es lo mismo que hiciste a mano con `docker build`, pero automático. Las instrucciones están en `.github/workflows/publicar-imagen.yml`: ábrelo y lee el nombre de cada paso.

> **Esto es CI/CD** (integración y entrega continuas): cada `git push` construye y publica una versión nueva sin pasos manuales. Es la forma en que los equipos llevan su código a producción.

### 4.2 Encuentra tu imagen

En la página principal de tu repositorio, a la derecha, en **Packages**, haz clic en el paquete. Verás:

- Las etiquetas `latest` y `1` (el número de la ejecución).
- El comando `docker pull ghcr.io/<tu-usuario>/<tu-repo>:1`. **Copia de ahí el nombre de tu imagen.**
- La etiqueta **Public**. Si dice *Private*: **Package settings → Change visibility → Public**.

### 4.3 Abre una máquina limpia

1. Ve a [github.com/codespaces](https://github.com/codespaces) → **Templates** → en la tarjeta **Blank**, pulsa **Use this template**.
2. Se abre un Codespace **vacío**: no tiene tu código, ni tu modelo, ni tus librerías.

### 4.4 Ejecuta tu imagen

En la terminal de ese Codespace vacío (cambia el nombre por el de tu imagen, **todo en minúsculas**):

```bash
docker run --rm -p 8000:8000 ghcr.io/<tu-usuario>/<tu-repo>:latest
```

Primero verás *"Unable to find image … locally"*: esta máquina no tiene la imagen, así que Docker la **descarga** de GitHub y la ejecuta.

Abre `/docs` desde la pestaña **Puertos** y prueba **POST /predecir** con `{"temperatura": 30, "humedad": 80}`. Debe dar la misma sensación térmica de siempre, con un `atendido_por` nuevo.

### 4.5 Limpieza

Detén la API con **Ctrl + C** y borra el Codespace en blanco: [github.com/codespaces](https://github.com/codespaces) → **⋯** → **Delete**.

### 🧪 Desafío: ejecuta la imagen de un compañero

Pídele a un compañero el nombre de su imagen y ejecútala en tu Codespace en blanco. ¿Necesitaste su código? ¿Qué Python y qué librerías usó?

### ✅ Lista de verificación

- [ ] La ejecución en **Actions** terminó con ✅ verde.
- [ ] Tu paquete aparece en **Packages** y es **Public**.
- [ ] La imagen corre en un Codespace en blanco con un solo `docker run`.
- [ ] `/predecir` responde la misma sensación térmica que en los pasos anteriores.

### Errores frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| ❌ rojo en Actions | El `Dockerfile` tiene un error | Abre la ejecución, mira el paso en rojo, corrige el `Dockerfile` y vuelve a hacer push |
| No aparece ninguna ejecución en Actions | El push no cambió nada dentro de `app/` | Verifica que `app/Dockerfile` está en GitHub; también puedes usar **Run workflow** en Actions |
| `not found` o `manifest unknown` | Nombre de la imagen mal escrito, con mayúsculas o pegado dos veces | Cópialo de la página del paquete y revisa que termine en `:latest` |
| `denied` o `unauthorized` | El paquete es privado | Hazlo público (4.2) |
| Error 502 al abrir la página | La API no está corriendo en ese Codespace | Ejecuta de nuevo el `docker run` y recarga |

### Para cerrar

1. Compara los tres entornos donde corrió tu modelo: Colab, tu Codespace y el Codespace en blanco. ¿En cuáles tuviste que instalar librerías a mano?
2. Si mañana cambias `main.py` y haces push, ¿qué pasos tendrías que repetir para que un compañero use la versión nueva?

---

### Al terminar la sesión

Detén tu Codespace para no gastar cuota: pulsa **F1** (o **Ctrl + Shift + P**), escribe `Stop Current Codespace` y presiona Enter. También puedes detenerlo desde [github.com/codespaces](https://github.com/codespaces), en el menú **⋯** de tu Codespace. Al final del curso puedes borrarlo desde [github.com/codespaces](https://github.com/codespaces).

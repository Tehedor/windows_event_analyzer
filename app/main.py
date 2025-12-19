# main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.routes import router as api_router


# =====================================================
# APP
# =====================================================

app = FastAPI(
    title="Visualizador de Ventanas",
    description="Interfaz web para la consulta y visualización de ventanas de eventos",
    version="1.0.0",
)


# =====================================================
# RUTAS API
# =====================================================

app.include_router(api_router)


# =====================================================
# FRONTEND (templates + static)
# =====================================================

# Templates HTML
templates = Jinja2Templates(directory="frontend/templates")

# Archivos estáticos (css / js / icons / etc.)
app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static",
)


# =====================================================
# RUTA PRINCIPAL (index)
# =====================================================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    Página principal de la aplicación web
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


# =====================================================
# HEALTHCHECK (opcional, pero útil)
# =====================================================

@app.get("/health")
def health():
    return {"status": "ok"}

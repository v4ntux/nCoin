from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.constants import APP_VERSION
from app.services.errors import GameError
from app.web.routes import api_router

WEBAPP_DIR = Path(__file__).resolve().parents[2] / "webapp"


def create_app() -> FastAPI:
    app = FastAPI(title="nCoin", version=APP_VERSION)
    app.include_router(api_router, prefix="/api")

    @app.exception_handler(GameError)
    async def game_error_handler(request: Request, exc: GameError) -> JSONResponse:
        return JSONResponse(
            status_code=400, content={"error": exc.code, "message": exc.message}
        )

    app.mount("/", StaticFiles(directory=str(WEBAPP_DIR), html=True), name="webapp")
    return app

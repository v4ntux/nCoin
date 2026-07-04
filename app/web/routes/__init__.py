from fastapi import APIRouter

from app.web.routes import admin, game, p2p, social, state, tasks, wallet

api_router = APIRouter()
api_router.include_router(state.router, tags=["state"])
api_router.include_router(p2p.router, tags=["p2p"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(game.router, tags=["game"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(social.router, tags=["social"])
api_router.include_router(wallet.router, tags=["wallet"])

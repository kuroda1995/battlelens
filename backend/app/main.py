from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import calculations, parties, species

settings = get_settings()

app = FastAPI(title="BattleLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin] if settings.frontend_origin != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(species.router)
app.include_router(parties.router)
app.include_router(calculations.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

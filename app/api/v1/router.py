from fastapi import APIRouter
from app.api.v1.calls import router as calls_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.dispatch import router as dispatch_router
from app.api.v1.telemetry import router as telemetry_router

api_v1_router = APIRouter()
api_v1_router.include_router(calls_router)
api_v1_router.include_router(incidents_router)
api_v1_router.include_router(dispatch_router)
api_v1_router.include_router(telemetry_router)

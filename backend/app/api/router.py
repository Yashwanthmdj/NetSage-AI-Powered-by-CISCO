from fastapi import APIRouter

from app.api import analytics, cases, diagnoses, health, rai, reviews, rules, verifications

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(cases.router)
api_router.include_router(reviews.router)
api_router.include_router(analytics.router)
api_router.include_router(rai.router)
api_router.include_router(rules.router)
api_router.include_router(diagnoses.router)
api_router.include_router(verifications.router)

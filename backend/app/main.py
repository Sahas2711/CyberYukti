import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.ai_routes import router as ai_router
from backend.app.api.case_routes import router as case_router
from backend.app.api.approval_routes import router as approval_router
from backend.app.api.audit_routes import router as audit_router
from backend.app.api.dashboard_routes import router as dashboard_router

app = FastAPI(title="CyberYukti API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router, prefix="/api/ai", tags=["AI"])
app.include_router(case_router, prefix="/api/cases", tags=["Cases"])
app.include_router(approval_router, prefix="/api/cases", tags=["Approval"])
app.include_router(audit_router, prefix="/api/cases", tags=["Audit"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/health")
async def health():
    return {"status": "ok"}

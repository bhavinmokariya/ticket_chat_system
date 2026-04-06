from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api.routes import customer_auth, staff_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Auth System API",
    description="Full-stack authentication system with JWT, refresh tokens, and role-based access.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
# CORS Configuration
# Allow both frontend servers (customer on :5173, admin on :5174)
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Customer frontend
        "http://localhost:5174",  # Admin/Support frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Register Routers
# ─────────────────────────────────────────────
app.include_router(customer_auth.router, prefix="/api/auth")
app.include_router(staff_auth.router, prefix="/api/auth")


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Auth System API is running.", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

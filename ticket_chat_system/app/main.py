from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.db import connect_to_mongo, close_mongo_connection
from app.routes import auth_routes, ticket_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to MongoDB and create indexes. Shutdown: close connection."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Ticket Support System",
    description="Customer support ticketing system with JWT auth, RBAC, and real-time chat.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Customer frontend
        "http://localhost:5174",   # Admin/Support frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_routes.router)
app.include_router(ticket_routes.router)

# Team-3: Uncomment when websocket and message routes are ready
# app.include_router(websocket_routes.router)
# app.include_router(message_routes.router)


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Ticket Support System is running.", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
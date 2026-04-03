from fastapi import FastAPI
from ticket_chat_system.app.routes import ticket_routes

app = FastAPI(
    title="Ticket Support System",
    description="Customer support ticketing system with real-time chat.",
    version="1.0.0"
)

# ── Routers ───────────────────────────────────────────
app.include_router(ticket_routes.router)

# Team-1: include auth_routes here when ready
# app.include_router(auth_routes.router)

# Team-3: include websocket_routes here when ready
# app.include_router(websocket_routes.router)
# app.include_router(message_routes.router)


@app.get("/")
async def root():
    return {"message": "Ticket Support System is running."}

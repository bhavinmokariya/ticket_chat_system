from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.message_service import *
from app.message_schema import Ticket, Message
from app.websocket.websocket_routes import router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Customer Support Chatbot API!"}


@app.post("/create-ticket")
async def create(ticket: Ticket):
    return await create_ticket(ticket.dict())



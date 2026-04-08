from app.db import ticket_collection
from app.mongo_helper import serialize_mongo
from datetime import datetime

# Create ticket
async def create_ticket(ticket_data):
    await ticket_collection.insert_one(ticket_data)
    return serialize_mongo(ticket_data)


# Get ticket by ID
async def get_ticket(ticket_id: int):
    ticket = await ticket_collection.find_one({"ticket_id": ticket_id})
    return serialize_mongo(ticket)


# Add message to ticket
async def add_message(ticket_id: int, message: dict):
    result = await ticket_collection.update_one(
        {"ticket_id": ticket_id},
        {
            "$push": {"messages": message},
            "$set": {
                "last_message_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    return result.modified_count


# Get all messages of ticket
async def get_messages(ticket_id: int):
    ticket = await ticket_collection.find_one({"ticket_id": ticket_id})
    if ticket:
        ticket = serialize_mongo(ticket)
        return ticket.get("messages", [])
    return []
from motor.motor_asyncio import AsyncIOMotorClient
from ticket_chat_system.app.config.settings import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

# Collections
tickets_collection = db["tickets"]
customers_collection = db["customers"]
support_collection = db["support_engineers"]
roles_collection = db["roles"]

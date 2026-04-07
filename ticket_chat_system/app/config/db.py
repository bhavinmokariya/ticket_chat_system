from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config.settings import settings

_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    _database = _client[settings.DB_NAME]
    print(f"Connected to MongoDB: {settings.DB_NAME}")
    # await create_indexes()


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()
        print("MongoDB connection closed.")


def get_database():  # ✅ ADD THIS
    return _database


async def create_indexes():
    db = get_database()

    await db.customers.create_index("email", unique=True)
    await db.customers.create_index("customer_id", unique=True)

    await db.support_engineers.create_index("email", unique=True)
    await db.support_engineers.create_index("support_id", unique=True)

    await db.roles.create_index("role_id", unique=True)
    await db.roles.create_index("role_name", unique=True)

    await db.tickets.create_index("ticket_id", unique=True)
    await db.tickets.create_index("ticket_number", unique=True)
    await db.tickets.create_index("customer_id")
    await db.tickets.create_index("assigned_engineer_id")
    await db.tickets.create_index("status")

    await db.refresh_tokens.create_index("token", unique=True)
    await db.refresh_tokens.create_index("user_id")
    await db.refresh_tokens.create_index("expires_at")

    print("Database indexes created.")
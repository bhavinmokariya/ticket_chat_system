from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _database = _client[settings.DATABASE_NAME]
    print(f"Connected to MongoDB: {settings.DATABASE_NAME}")

    # Create indexes for performance and uniqueness
    await create_indexes()


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()
        print(" MongoDB connection closed.")


async def create_indexes():
    """
    Create database indexes for performance and data integrity.
    These indexes prevent duplicate emails and speed up lookups.
    """
    db = get_database()

    # Customers: unique email, index on customer_id
    await db.customers.create_index("email", unique=True)
    await db.customers.create_index("customer_id", unique=True)

    # Support Engineers: unique email, index on support_id
    await db.support_engineers.create_index("email", unique=True)
    await db.support_engineers.create_index("support_id", unique=True)

    # Roles: unique role_id and role_name
    await db.roles.create_index("role_id", unique=True)
    await db.roles.create_index("role_name", unique=True)

    # Refresh tokens: index on token string, user_id, expiry (for cleanup)
    await db.refresh_tokens.create_index("token", unique=True)
    await db.refresh_tokens.create_index("user_id")
    await db.refresh_tokens.create_index("expires_at")  # For TTL cleanup queries

    print(" Database indexes created.")


def get_database() -> AsyncIOMotorDatabase:
    """Return the active database instance."""
    return _database
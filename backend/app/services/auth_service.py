from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError
from app.schemas.auth import CreateSupportEngineerRequest

from app.db.mongodb import get_database
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings


# ─────────────────────────────────────────────
# Helper: Auto-increment ID
# ─────────────────────────────────────────────

async def get_next_id(collection_name: str, id_field: str) -> int:
    """
    Get the next auto-increment ID for a collection.
    Finds the max existing ID and adds 1.
    """
    db = get_database()
    collection = db[collection_name]
    last_doc = await collection.find_one(
        {}, sort=[(id_field, -1)], projection={id_field: 1}
    )
    if last_doc:
        return last_doc[id_field] + 1
    return 1


# ─────────────────────────────────────────────
# Customer Auth Service
# ─────────────────────────────────────────────

async def register_customer(name: str, email: str, password: str) -> dict:
    """
    Register a new customer.
    - Checks for duplicate email.
    - Hashes password.
    - Inserts into 'customers' collection.
    Returns the created customer document.
    """
    db = get_database()

    # Check if email already exists
    existing = await db.customers.find_one({"email": email})
    if existing:
        raise ValueError("Email already registered.")

    # Auto-increment customer_id
    customer_id = await get_next_id("customers", "customer_id")

    now = datetime.now(timezone.utc)
    customer_doc = {
        "customer_id": customer_id,
        "name": name,
        "email": email,
        "password": hash_password(password),
        "is_active": True,
        "created_at": now,
        "last_login": None,
    }

    await db.customers.insert_one(customer_doc)
    return customer_doc


async def authenticate_customer(email: str, password: str) -> Optional[dict]:
    """
    Authenticate a customer by email and password.
    Returns the customer document if valid, None otherwise.
    """
    db = get_database()
    customer = await db.customers.find_one({"email": email})

    if not customer:
        return None
    if not customer.get("is_active"):
        raise ValueError("Account is deactivated.")
    if not verify_password(password, customer["password"]):
        return None

    # Update last_login timestamp
    await db.customers.update_one(
        {"email": email},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    customer["last_login"] = datetime.now(timezone.utc)
    return customer


# ─────────────────────────────────────────────
# Support Engineer Auth Service
# ─────────────────────────────────────────────

async def authenticate_support_engineer(email: str, password: str) -> Optional[dict]:
    """
    Authenticate a support engineer or admin.
    Returns the engineer document with role info if valid, None otherwise.
    """
    db = get_database()
    engineer = await db.support_engineers.find_one({"email": email})

    if not engineer:
        return None
    if not engineer.get("is_active"):
        raise ValueError("Account is deactivated.")
    if not verify_password(password, engineer["password"]):
        return None

    # Fetch role name from roles collection
    role_doc = await db.roles.find_one({"role_id": engineer["role_id"]})
    role_name = role_doc["role_name"] if role_doc else "support"

    # Update last_seen and is_online
    await db.support_engineers.update_one(
        {"email": email},
        {"$set": {"last_seen": datetime.now(timezone.utc), "is_online": True}}
    )

    engineer["role_name"] = role_name
    return engineer

async def create_support_engineer(details : CreateSupportEngineerRequest) -> dict:
    db = get_database()

    # Check if email exists in support engineers
    existing = await db.support_engineers.find_one({"email": details.email})
    if existing:
        raise ValueError(f"Email '{details.email}' is already registered.")

    # Check if email exists in customers
    existing_customer = await db.customers.find_one({"email": details.email})
    if existing_customer:
        raise ValueError(f"Email '{details.email}' is already registered as a customer.")

    # Generate support_id
    support_id = await get_next_id("support_engineers", "support_id")

    now = datetime.now(timezone.utc)

    engineer_doc = {
        "support_id": support_id,
        "name": details.name,
        "email": details.email,
        "password": hash_password(details.password),
        "role_id": details.role_id,
        "department": details.department,
        "is_active": True,
        "is_online": False,
        "last_seen": None,
        "created_at": now,
    }

    result = await db.support_engineers.insert_one(engineer_doc)
    engineer_doc["_id"] = result.inserted_id

    return engineer_doc

# ─────────────────────────────────────────────
# Token Service
# ─────────────────────────────────────────────

async def create_tokens_for_user(
    user_id: str,
    user_type: str,
    role: str,
    name: str,
    email: str,
) -> Tuple[str, str]:
    """
    Create and store access + refresh tokens for a user.
    - user_id: "customer_1" or "support_101"
    - user_type: "customer" or "support_engineer"
    - role: "customer", "support", or "admin"
    Returns (access_token, refresh_token).
    """
    token_data = {
        "sub": user_id,
        "user_type": user_type,
        "role": role,
        "name": name,
        "email": email,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store refresh token in MongoDB
    db = get_database()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await db.refresh_tokens.insert_one({
        "token": refresh_token,
        "user_id": user_id,
        "user_type": user_type,
        "role": role,
        "created_at": now,
        "expires_at": expires_at,
    })

    return access_token, refresh_token


async def refresh_access_token(refresh_token: str) -> str:
    """
    Validate a refresh token and issue a new access token.
    - Checks token exists in DB and is not revoked/expired.
    Returns a new access_token string.
    """
    db = get_database()

    # Step 1: Decode JWT to check signature and expiry
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise ValueError("Invalid or expired refresh token.")

    if payload.get("type") != "refresh":
        raise ValueError("Token type mismatch. Expected refresh token.")

    # Step 2: Check token exists in DB.
    # If the user already logged out, the token was deleted — so it won't be found.
    # No need for an is_revoked flag; absence == invalid.
    token_doc = await db.refresh_tokens.find_one({"token": refresh_token})
    if not token_doc:
        raise ValueError("Refresh token not found or already used after logout.")

    # Step 3: Issue new access token with same payload
    token_data = {
        "sub": payload["sub"],
        "user_type": payload["user_type"],
        "role": payload["role"],
        "name": payload["name"],
        "email": payload["email"],
    }
    new_access_token = create_access_token(token_data)
    return new_access_token


async def revoke_refresh_token(refresh_token: str) -> bool:
    """
    Delete a refresh token from the database on logout.
    Physically removing it (instead of just flagging is_revoked=True) means:
    - The token is completely gone — cannot be reused even if stolen
    - The DB stays clean without needing a separate cleanup job
    Returns True if the token was found and deleted.
    """
    db = get_database()
    result = await db.refresh_tokens.delete_one({"token": refresh_token})
    return result.deleted_count > 0


async def revoke_all_tokens_for_user(user_id: str) -> int:
    """
    Delete ALL refresh tokens for a given user.
    Useful for:
    - Password change (invalidate all existing sessions)
    - Admin-forced logout from all devices
    - Suspicious activity response
    Returns the number of tokens deleted.
    """
    db = get_database()
    result = await db.refresh_tokens.delete_many({"user_id": user_id})
    return result.deleted_count


async def cleanup_expired_tokens() -> int:
    """
    Delete all refresh tokens that have passed their expiry date.
    Call this periodically (e.g., on a scheduled task or at login time)
    to keep the refresh_tokens collection from growing indefinitely.
    Returns the number of tokens deleted.
    """
    db = get_database()
    now = datetime.now(timezone.utc)
    result = await db.refresh_tokens.delete_many({"expires_at": {"$lt": now}})
    return result.deleted_count


async def get_current_user_from_token(access_token: str) -> dict:
    """
    Decode an access token and return the user payload.
    Used as a dependency in protected routes.
    """
    try:
        payload = decode_token(access_token)
    except JWTError:
        raise ValueError("Invalid or expired access token.")

    if payload.get("type") != "access":
        raise ValueError("Token type mismatch. Expected access token.")

    return payload

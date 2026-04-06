from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    AccessTokenResponse,
    SupportEngineerResponse,
    MessageResponse,
    CreateSupportEngineerRequest,
)
from app.services.auth_service import (
    authenticate_support_engineer,
    create_tokens_for_user,
    refresh_access_token,
    revoke_refresh_token,
    revoke_all_tokens_for_user,
    cleanup_expired_tokens,
    create_support_engineer,
)
from app.api.dependencies import get_current_user, require_role

router = APIRouter(prefix="/staff", tags=["Staff Auth (Support & Admin)"])


@router.post("/login", response_model=TokenResponse)
async def staff_login(data: LoginRequest):
    """
    Login for Support Engineers and Admins.
    These accounts are pre-created in the database - no public registration.
    Returns access token (15 min) and refresh token (7 days).
    """
    try:
        engineer = await authenticate_support_engineer(
            email=data.email, password=data.password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    role_name = engineer.get("role_name", "support")
    user_id = f"support_{engineer['support_id']}"

    access_token, refresh_token = await create_tokens_for_user(
        user_id=user_id,
        user_type="support_engineer",
        role=role_name,
        name=engineer["name"],
        email=engineer["email"],
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": role_name,
        "name": engineer["name"],
    }

#create staff

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def add_support_engineer(details: CreateSupportEngineerRequest):
    try:
        engineer = await create_support_engineer(details)

        # Convert ObjectId to string (important for JSON response)
        engineer["_id"] = str(engineer["_id"])

        return {
            "success": True,
            "message": "Support engineer created successfully",
            "data": engineer
        }

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong"
        )

@router.post("/refresh", response_model=AccessTokenResponse)
async def staff_refresh_token(data: RefreshTokenRequest):
    """
    Use a valid refresh token to get a new access token.
    Call this when the access token expires (401 response).
    """
    try:
        new_access_token = await refresh_access_token(data.refresh_token)
        return {"access_token": new_access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout", response_model=MessageResponse)
async def staff_logout(
    data: RefreshTokenRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Logout by DELETING the refresh token from the database.
    - Token is physically removed so it cannot be reused.
    - Also marks the engineer as offline in support_engineers collection.
    - Cleans up expired tokens from the collection.
    """
    # Mark engineer as offline
    if current_user.get("user_type") == "support_engineer":
        from app.db.mongodb import get_database
        from datetime import datetime, timezone
        db = get_database()
        await db.support_engineers.update_one(
            {"email": current_user["email"]},
            {"$set": {"is_online": False, "last_seen": datetime.now(timezone.utc)}}
        )

    deleted = await revoke_refresh_token(data.refresh_token)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token not found. It may have already been logged out.",
        )
    # Opportunistic cleanup: remove any other expired tokens
    await cleanup_expired_tokens()
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=SupportEngineerResponse)
async def get_staff_profile(
    current_user: dict = Depends(require_role("support", "admin"))
):
    """
    Get the currently logged-in support engineer or admin's profile.
    Only accessible to support and admin roles.
    """
    from app.db.mongodb import get_database
    db = get_database()

    # Extract support_id from "support_101" format
    user_id_str = current_user["sub"]  # e.g., "support_101"
    support_id = int(user_id_str.split("_")[1])

    engineer = await db.support_engineers.find_one({"support_id": support_id})
    if not engineer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engineer not found.",
        )

    return {
        "support_id": engineer["support_id"],
        "name": engineer["name"],
        "email": engineer["email"],
        "role_id": engineer["role_id"],
        "department": engineer["department"],
        "is_active": engineer["is_active"],
        "is_online": engineer["is_online"],
        "last_seen": engineer.get("last_seen"),
        "created_at": engineer["created_at"],
    }


# ─────────────────────────────────────────────
# Example: Admin-only route
# ─────────────────────────────────────────────

@router.get("/admin/dashboard", tags=["Admin"])
async def admin_dashboard(current_user: dict = Depends(require_role("admin"))):
    """
    Example admin-only route using role-based access control.
    Only users with 'admin' role can access this.
    """
    return {
        "message": "Welcome to the Admin Dashboard!",
        "admin": current_user["name"],
        "role": current_user["role"],
    }


@router.get("/support/dashboard", tags=["Support"])
async def support_dashboard(
    current_user: dict = Depends(require_role("support", "admin"))
):
    """
    Support dashboard - accessible by both support and admin roles.
    """
    return {
        "message": "Welcome to the Support Dashboard!",
        "user": current_user["name"],
        "role": current_user["role"],
    }

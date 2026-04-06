from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.auth import (
    CustomerRegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    AccessTokenResponse,
    CustomerResponse,
    MessageResponse,
)
from app.services.auth_service import (
    register_customer,
    authenticate_customer,
    create_tokens_for_user,
    refresh_access_token,
    revoke_refresh_token,
    revoke_all_tokens_for_user,
    cleanup_expired_tokens,
)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/customer", tags=["Customer Auth"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def customer_register(data: CustomerRegisterRequest):
    """
    Register a new customer account.
    Only customers can self-register.
    Support engineers and admins are pre-inserted in the database.
    """
    try:
        customer = await register_customer(
            name=data.name,
            email=data.email,
            password=data.password,
        )
        return {"message": f"Account created successfully. Welcome, {customer['name']}!"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def customer_login(data: LoginRequest):
    """
    Login as a customer.
    Returns access token (15 min) and refresh token (7 days).
    """
    try:
        customer = await authenticate_customer(email=data.email, password=data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user_id = f"customer_{customer['customer_id']}"
    access_token, refresh_token = await create_tokens_for_user(
        user_id=user_id,
        user_type="customer",
        role="customer",
        name=customer["name"],
        email=customer["email"],
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": "customer",
        "name": customer["name"],
    }


@router.post("/refresh", response_model=AccessTokenResponse)
async def customer_refresh_token(data: RefreshTokenRequest):
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
async def customer_logout(
    data: RefreshTokenRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Logout by DELETING the refresh token from the database.
    - The token is physically removed (not just flagged) so it can never be reused.
    - Also cleans up any other expired tokens for hygiene.
    - The client must also delete tokens from localStorage.
    """
    deleted = await revoke_refresh_token(data.refresh_token)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token not found. It may have already been logged out.",
        )
    # Opportunistic cleanup: remove any other expired tokens from the collection
    await cleanup_expired_tokens()
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=CustomerResponse)
async def get_customer_profile(current_user: dict = Depends(get_current_user)):
    """
    Get the currently logged-in customer's profile.
    Requires a valid access token.
    """
    if current_user.get("role") != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Customer accounts only.",
        )

    from app.db.mongodb import get_database
    db = get_database()

    # Extract customer_id from "customer_1" format
    user_id_str = current_user["sub"]  # e.g., "customer_1"
    customer_id = int(user_id_str.split("_")[1])

    customer = await db.customers.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    return {
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "email": customer["email"],
        "is_active": customer["is_active"],
        "created_at": customer["created_at"],
        "last_login": customer.get("last_login"),
        "role": "customer",
    }

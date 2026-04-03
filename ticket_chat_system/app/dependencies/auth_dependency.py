from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# ---------------------------------------------------------------
# PLACEHOLDER — Team-1 will replace this with real JWT validation
# ---------------------------------------------------------------
# This dependency should decode the JWT token and return a dict:
# {
#     "id": int,              # customer_id or support_id
#     "role": str,            # "admin" | "customer" | "support_engineer"
#     "is_online": bool       # only relevant for support engineers
# }
# ---------------------------------------------------------------

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
#     """
#     PLACEHOLDER: Team-1 replaces this with real JWT decode logic.
#     Returns a mock user for development/testing purposes.
#     """
#     # TODO: Team-1 — decode token, validate, return real user dict
#     # Example return shape:
#     # return {"id": 1, "role": "customer", "is_online": False}
#     # return {"id": 101, "role": "support_engineer", "is_online": True}
#     # return {"id": 1, "role": "admin", "is_online": True}

#     raise HTTPException(
#         status_code=status.HTTP_501_NOT_IMPLEMENTED,
#         detail="Auth dependency not yet implemented. Team-1 please integrate JWT here."
#     )


async def get_current_user() -> dict:
    """
    TEMP: Dummy user for testing (NO AUTH)
    Change role/id here to test different flows
    """
    return {
        "id": 101,
        "role": "support_engineer",  # change: admin | customer | support_engineer
        "is_online": True
    }
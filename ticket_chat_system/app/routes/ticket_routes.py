# from fastapi import APIRouter, Depends, Query
# from typing import Optional

# from app.dependencies.auth_dependency import get_current_user
# from app.dependencies.role_dependency import require_roles
# from app.constants.roles import Role
# from app.schemas.ticket_schema import (
#     TicketCreateRequest,
#     TicketCreateResponse,
#     TicketSummaryOut,
#     TicketDetailOut,
#     SubjectsListResponse
# )
# from app.services import ticket_service

# router = APIRouter(prefix="/tickets", tags=["Tickets"])


# # ─────────────────────────────────────────────
# # GET /tickets/subjects
# # Public-ish: Customer fetches predefined subjects for dropdown
# # ─────────────────────────────────────────────

# @router.get("/subjects", response_model=SubjectsListResponse)
# async def get_subjects(current_user: dict = Depends(require_roles([Role.CUSTOMER, Role.ADMIN]))):
#     """Returns list of predefined subjects for the ticket creation dropdown."""
#     subjects = ticket_service.get_predefined_subjects()
#     return {"subjects": subjects}


# # ─────────────────────────────────────────────
# # POST /tickets/create
# # Customer only
# # ─────────────────────────────────────────────

# @router.post("/create", response_model=TicketCreateResponse, status_code=201)
# async def create_ticket(payload: TicketCreateRequest,current_user: dict = Depends(require_roles([Role.CUSTOMER]))):
#     """
#     Customer creates a new support ticket.
#     Subject must be from predefined list. Priority is auto-assigned.
#     All online support engineers are notified (via Team-3 placeholder).
#     """
#     ticket = await ticket_service.create_ticket(
#         customer_id=current_user["id"],
#         subject=payload.subject,
#         description=payload.description
#     )
#     return {
#         "ticket_number": ticket["ticket_number"],
#         "subject": ticket["subject"],
#         "priority": ticket["priority"],
#         "status": ticket["status"],
#         "created_at": ticket["created_at"],
#     }


# # ─────────────────────────────────────────────
# # GET /tickets/my
# # Customer only — view their own tickets
# # ─────────────────────────────────────────────

# @router.get("/my", response_model=list[TicketSummaryOut])
# async def get_my_tickets(current_user: dict = Depends(require_roles([Role.CUSTOMER]))):
#     """Returns all tickets belonging to the logged-in customer."""
#     return await ticket_service.get_my_tickets(customer_id=current_user["id"])


# # ─────────────────────────────────────────────
# # GET /tickets/open
# # Support Engineers & Admin only
# # ─────────────────────────────────────────────

# @router.get("/open", response_model=list[TicketSummaryOut])
# async def get_open_tickets(current_user: dict = Depends(require_roles([Role.SUPPORT, Role.ADMIN]))):
#     """
#     Returns all open & unassigned tickets.
#     Support engineers use this to find tickets to pick up.
#     """
#     return await ticket_service.get_open_tickets()


# # ─────────────────────────────────────────────
# # GET /tickets/all
# # Support Engineers & Admin only — with optional filters
# # ─────────────────────────────────────────────

# @router.get("/all", response_model=list[TicketSummaryOut])
# async def get_all_tickets(
#     status: Optional[str] = Query(None, description="Filter by status: open | in_progress | resolved | closed"),
#     priority: Optional[str] = Query(None, description="Filter by priority: low | medium | high"),
#     assigned_engineer_id: Optional[int] = Query(None, description="Filter by assigned engineer ID"),
#     current_user: dict = Depends(require_roles([Role.SUPPORT, Role.ADMIN]))
# ):
#     """
#     Returns all tickets with optional filters.
#     Admin can track any engineer's tickets using assigned_engineer_id filter.
#     """
#     return await ticket_service.get_all_tickets(
#         status_filter=status,
#         priority_filter=priority,
#         assigned_engineer_id=assigned_engineer_id
#     )


# # ─────────────────────────────────────────────
# # GET /tickets/{ticket_number}
# # Customer: own tickets only | Support & Admin: any ticket
# # ─────────────────────────────────────────────

# @router.get("/{ticket_number}", response_model=TicketDetailOut)
# async def get_ticket(ticket_number: str,current_user: dict = Depends(get_current_user)):      # All roles, filtered in service
#     """
#     Fetch full ticket details including chat messages.
#     Customers can only access their own tickets.
#     Support engineers and admin can access any ticket.
#     """
#     return await ticket_service.get_ticket_by_number(
#         ticket_number=ticket_number,
#         current_user=current_user
#     )


# # ─────────────────────────────────────────────
# # POST /tickets/take/{ticket_number}
# # Support Engineers only
# # ─────────────────────────────────────────────

# @router.post("/take/{ticket_number}")
# async def take_ticket(
#     ticket_number: str,
#     current_user: dict = Depends(require_roles([Role.SUPPORT]))
# ):
#     """
#     Engineer picks up an open ticket.
#     Engineer must be online. First-come-first-serve enforced atomically.
#     """
#     ticket = await ticket_service.take_ticket(
#         ticket_number=ticket_number,
#         engineer=current_user
#     )
#     return {
#         "message": f"Ticket {ticket_number} successfully assigned to you.",
#         "ticket_number": ticket["ticket_number"],
#         "status": ticket["status"],
#         "assigned_engineer_id": ticket["assigned_engineer_id"]
#     }


# # ─────────────────────────────────────────────
# # POST /tickets/resolve/{ticket_number}
# # Support Engineers (assigned only) & Admin
# # ─────────────────────────────────────────────

# @router.post("/resolve/{ticket_number}")
# async def resolve_ticket(
#     ticket_number: str,
#     current_user: dict = Depends(require_roles([Role.SUPPORT, Role.ADMIN]))
# ):
#     """
#     Marks ticket as resolved.
#     If customer messages again on a resolved ticket, it auto-reopens (handled by Team-3).
#     """
#     ticket = await ticket_service.resolve_ticket(
#         ticket_number=ticket_number,
#         engineer=current_user
#     )
#     return {
#         "message": f"Ticket {ticket_number} marked as resolved.",
#         "ticket_number": ticket["ticket_number"],
#         "status": ticket["status"]
#     }


# # ─────────────────────────────────────────────
# # POST /tickets/close/{ticket_number}
# # Support Engineers (assigned only) & Admin
# # ─────────────────────────────────────────────

# @router.post("/close/{ticket_number}")
# async def close_ticket(
#     ticket_number: str,
#     current_user: dict = Depends(require_roles([Role.SUPPORT, Role.ADMIN]))
# ):
#     """
#     Permanently closes a ticket. Cannot be reopened after this.
#     Ticket must be in_progress or resolved before closing.
#     """
#     ticket = await ticket_service.close_ticket(
#         ticket_number=ticket_number,
#         engineer=current_user
#     )
#     return {
#         "message": f"Ticket {ticket_number} has been closed.",
#         "ticket_number": ticket["ticket_number"],
#         "status": ticket["status"],
#         "closed_at": ticket["closed_at"]
#     }
from fastapi import APIRouter, Depends, Query
from typing import Optional

from ticket_chat_system.app.dependencies.auth_dependency import get_current_user
from ticket_chat_system.app.schemas.ticket_schema import (
    TicketCreateRequest,
    TicketCreateResponse,
    TicketSummaryOut,
    TicketDetailOut,
    SubjectsListResponse
)
from ticket_chat_system.app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["Tickets"],dependencies=[])


# ─────────────────────────────────────────────
# GET /tickets/subjects
# ─────────────────────────────────────────────

@router.get("/subjects", response_model=SubjectsListResponse)
async def get_subjects(current_user: dict = Depends(get_current_user)):
    subjects = ticket_service.get_predefined_subjects()
    return {"subjects": subjects}


# ─────────────────────────────────────────────
# POST /tickets/create
# ─────────────────────────────────────────────

@router.post("/create", response_model=TicketCreateResponse, status_code=201)
async def create_ticket(
    payload: TicketCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    ticket = await ticket_service.create_ticket(
        customer_id=current_user["id"],
        subject=payload.subject,
        description=payload.description
    )
    return {
        "ticket_number": ticket["ticket_number"],
        "subject": ticket["subject"],
        "priority": ticket["priority"],
        "status": ticket["status"],
        "created_at": ticket["created_at"],
    }


# ─────────────────────────────────────────────
# GET /tickets/my
# ─────────────────────────────────────────────

@router.get("/my", response_model=list[TicketSummaryOut])
async def get_my_tickets(current_user: dict = Depends(get_current_user)):
    return await ticket_service.get_my_tickets(customer_id=current_user["id"])


# ─────────────────────────────────────────────
# GET /tickets/open
# ─────────────────────────────────────────────

@router.get("/open", response_model=list[TicketSummaryOut])
async def get_open_tickets(current_user: dict = Depends(get_current_user)):
    return await ticket_service.get_open_tickets()


# ─────────────────────────────────────────────
# GET /tickets/all
# ─────────────────────────────────────────────

@router.get("/all", response_model=list[TicketSummaryOut])
async def get_all_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_engineer_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    return await ticket_service.get_all_tickets(
        status_filter=status,
        priority_filter=priority,
        assigned_engineer_id=assigned_engineer_id
    )


# ─────────────────────────────────────────────
# GET /tickets/{ticket_number}
# ─────────────────────────────────────────────

@router.get("/{ticket_number}", response_model=TicketDetailOut)
async def get_ticket(
    ticket_number: str,
    current_user: dict = Depends(get_current_user)
):
    return await ticket_service.get_ticket_by_number(
        ticket_number=ticket_number,
        current_user=current_user
    )


# ─────────────────────────────────────────────
# POST /tickets/take/{ticket_number}
# ─────────────────────────────────────────────

@router.post("/take/{ticket_number}")
async def take_ticket(
    ticket_number: str,
    current_user: dict = Depends(get_current_user)
):
    ticket = await ticket_service.take_ticket(
        ticket_number=ticket_number,
        engineer=current_user
    )
    return {
        "message": f"Ticket {ticket_number} successfully assigned to you.",
        "ticket_number": ticket["ticket_number"],
        "status": ticket["status"],
        "assigned_engineer_id": ticket["assigned_engineer_id"]
    }


# ─────────────────────────────────────────────
# POST /tickets/resolve/{ticket_number}
# ─────────────────────────────────────────────

@router.post("/resolve/{ticket_number}")
async def resolve_ticket(
    ticket_number: str,
    current_user: dict = Depends(get_current_user)
):
    ticket = await ticket_service.resolve_ticket(
        ticket_number=ticket_number,
        engineer=current_user
    )
    return {
        "message": f"Ticket {ticket_number} marked as resolved.",
        "ticket_number": ticket["ticket_number"],
        "status": ticket["status"]
    }


# ─────────────────────────────────────────────
# POST /tickets/close/{ticket_number}
# ─────────────────────────────────────────────

@router.post("/close/{ticket_number}")
async def close_ticket(
    ticket_number: str,
    current_user: dict = Depends(get_current_user)
):
    ticket = await ticket_service.close_ticket(
        ticket_number=ticket_number,
        engineer=current_user
    )
    return {
        "message": f"Ticket {ticket_number} has been closed.",
        "ticket_number": ticket["ticket_number"],
        "status": ticket["status"],
        "closed_at": ticket["closed_at"]
    }
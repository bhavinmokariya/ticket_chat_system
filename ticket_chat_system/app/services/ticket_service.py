from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from bson import ObjectId

from ticket_chat_system.app.config.db import tickets_collection, support_collection
from ticket_chat_system.app.constants.ticket_status import TicketStatus, SUBJECT_PRIORITY_MAP, PREDEFINED_SUBJECTS
from ticket_chat_system.app.constants.roles import Role
from ticket_chat_system.app.utils.id_generator import generate_ticket_id, generate_ticket_number


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def serialize_ticket(ticket: dict) -> dict:
    """Convert MongoDB ObjectId to string for JSON serialization."""
    if ticket and "_id" in ticket:
        ticket["_id"] = str(ticket["_id"])
    return ticket


# ─────────────────────────────────────────────
# Create Ticket
# ─────────────────────────────────────────────

async def create_ticket(customer_id: int, subject: str, description: str) -> dict:
    """
    Creates a new support ticket for a customer.
    Priority is auto-assigned from SUBJECT_PRIORITY_MAP.
    """
    if subject not in SUBJECT_PRIORITY_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid subject. Choose from predefined subjects: {PREDEFINED_SUBJECTS}"
        )

    priority = SUBJECT_PRIORITY_MAP[subject]
    ticket_id = await generate_ticket_id()
    ticket_number = generate_ticket_number(ticket_id)
    now = utcnow()

    ticket_doc = {
        "ticket_id": ticket_id,
        "ticket_number": ticket_number,
        "customer_id": customer_id,
        "assigned_engineer_id": None,
        "status": TicketStatus.OPEN,
        "priority": priority,
        "subject": subject,
        "description": description,
        "created_at": now,
        "updated_at": now,
        "last_message_at": None,
        "closed_at": None,
        "messages": []
    }

    await tickets_collection.insert_one(ticket_doc)

    # ── PLACEHOLDER: Team-3 notify all online engineers ──────────────────
    # await notify_all_engineers(ticket_doc)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(ticket_doc)


# ─────────────────────────────────────────────
# Get Subjects List (for frontend dropdown)
# ─────────────────────────────────────────────

def get_predefined_subjects() -> list:
    return PREDEFINED_SUBJECTS


# ─────────────────────────────────────────────
# Get My Tickets (Customer)
# ─────────────────────────────────────────────

async def get_my_tickets(customer_id: int) -> list:
    """Returns all tickets belonging to the logged-in customer."""
    cursor = tickets_collection.find(
        {"customer_id": customer_id},
        {"messages": 0}             # Exclude messages for list view (performance)
    ).sort("created_at", -1)

    tickets = []
    async for ticket in cursor:
        tickets.append(serialize_ticket(ticket))
    return tickets


# ─────────────────────────────────────────────
# Get Open Tickets (Support Engineers / Admin)
# ─────────────────────────────────────────────

async def get_open_tickets() -> list:
    """Returns all unassigned open tickets. Visible to support engineers and admin."""
    cursor = tickets_collection.find(
        {
            "status": TicketStatus.OPEN,
            "assigned_engineer_id": None
        },
        {"messages": 0}
    ).sort("created_at", 1)         # Oldest first — fairness for first-come-first-serve

    tickets = []
    async for ticket in cursor:
        tickets.append(serialize_ticket(ticket))
    return tickets


# ─────────────────────────────────────────────
# Get All Tickets with Filters (Support / Admin)
# ─────────────────────────────────────────────

async def get_all_tickets(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    assigned_engineer_id: Optional[int] = None
) -> list:
    """
    Returns all tickets with optional filters.
    Only accessible by support engineers and admin.
    """
    query = {}

    if status_filter:
        valid_statuses = [
            TicketStatus.OPEN,
            TicketStatus.IN_PROGRESS,
            TicketStatus.RESOLVED,
            TicketStatus.CLOSED
        ]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Valid values: {valid_statuses}"
            )
        query["status"] = status_filter

    if priority_filter:
        if priority_filter not in ["low", "medium", "high"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid priority filter. Valid values: low, medium, high"
            )
        query["priority"] = priority_filter

    if assigned_engineer_id is not None:
        query["assigned_engineer_id"] = assigned_engineer_id

    cursor = tickets_collection.find(query, {"messages": 0}).sort("created_at", -1)

    tickets = []
    async for ticket in cursor:
        tickets.append(serialize_ticket(ticket))
    return tickets


# ─────────────────────────────────────────────
# Get Single Ticket
# ─────────────────────────────────────────────

async def get_ticket_by_number(ticket_number: str, current_user: dict) -> dict:
    """
    Fetch full ticket details including messages.
    - Customer: can only view their own ticket (matched by ticket_number + customer_id)
    - Support / Admin: can view any ticket
    """
    ticket = await tickets_collection.find_one({"ticket_number": ticket_number})

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_number} not found."
        )

    # Customers can only view their own tickets
    if current_user["role"] == Role.CUSTOMER:
        if ticket["customer_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket."
            )

    return serialize_ticket(ticket)


# ─────────────────────────────────────────────
# Take Ticket (Support Engineer)
# ─────────────────────────────────────────────

async def take_ticket(ticket_number: str, engineer: dict) -> dict:
    """
    Assigns an open ticket to the requesting support engineer.
    - Engineer must be online
    - Ticket must be open and unassigned (first-come-first-serve)
    """
    # Check engineer is online
    if not engineer.get("is_online", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be online to take a ticket."
        )

    # Atomic update: only succeeds if ticket is still open & unassigned
    result = await tickets_collection.find_one_and_update(
        {
            "ticket_number": ticket_number,
            "status": TicketStatus.OPEN,
            "assigned_engineer_id": None        # Ensures first-come-first-serve
        },
        {
            "$set": {
                "assigned_engineer_id": engineer["id"],
                "status": TicketStatus.IN_PROGRESS,
                "updated_at": utcnow()
            }
        },
        return_document=True
    )

    if not result:
        # Check why it failed — ticket may not exist or already taken
        existing = await tickets_collection.find_one({"ticket_number": ticket_number})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_number} not found."
            )
        if existing["status"] != TicketStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticket is not open. Current status: {existing['status']}"
            )
        if existing["assigned_engineer_id"] is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ticket was already taken by another engineer."
            )

    # ── PLACEHOLDER: Team-3 notify customer that engineer joined ──────────
    # await notify_customer(result["customer_id"], WSEvent.TICKET_TAKEN, result)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(result)


# ─────────────────────────────────────────────
# Resolve Ticket (Support Engineer / Admin)
# ─────────────────────────────────────────────

async def resolve_ticket(ticket_number: str, engineer: dict) -> dict:
    """
    Marks a ticket as resolved.
    Only the assigned engineer or admin can resolve.
    If customer messages again → reopen_ticket() is called by message service (Team-3).
    """
    ticket = await tickets_collection.find_one({"ticket_number": ticket_number})

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_number} not found."
        )

    if ticket["status"] != TicketStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only in-progress tickets can be resolved. Current status: {ticket['status']}"
        )

    # Admin bypasses assignment check; engineer must be the assigned one
    if engineer["role"] != Role.ADMIN:
        if ticket["assigned_engineer_id"] != engineer["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned engineer can resolve this ticket."
            )

    updated = await tickets_collection.find_one_and_update(
        {"ticket_number": ticket_number},
        {"$set": {
            "status": TicketStatus.RESOLVED,
            "updated_at": utcnow()
        }},
        return_document=True
    )

    # ── PLACEHOLDER: Team-3 notify customer ticket is resolved ────────────
    # await notify_customer(ticket["customer_id"], WSEvent.TICKET_RESOLVED, updated)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(updated)


# ─────────────────────────────────────────────
# Close Ticket (Support Engineer / Admin)
# ─────────────────────────────────────────────

async def close_ticket(ticket_number: str, engineer: dict) -> dict:
    """
    Permanently closes a ticket.
    Can close from in_progress or resolved state.
    Cannot close an open ticket (must be assigned first).
    """
    ticket = await tickets_collection.find_one({"ticket_number": ticket_number})

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_number} not found."
        )

    closeable_statuses = [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED]
    if ticket["status"] not in closeable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticket cannot be closed from status: '{ticket['status']}'. "
                   f"Must be in-progress or resolved first."
        )

    # Admin bypasses assignment check
    if engineer["role"] != Role.ADMIN:
        if ticket["assigned_engineer_id"] != engineer["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned engineer can close this ticket."
            )

    now = utcnow()
    updated = await tickets_collection.find_one_and_update(
        {"ticket_number": ticket_number},
        {"$set": {
            "status": TicketStatus.CLOSED,
            "closed_at": now,
            "updated_at": now
        }},
        return_document=True
    )

    # ── PLACEHOLDER: Team-3 notify customer ticket is closed ─────────────
    # await notify_customer(ticket["customer_id"], WSEvent.TICKET_CLOSED, updated)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(updated)


# ─────────────────────────────────────────────
# Reopen Ticket — Called by Team-3 (Message Service)
# ─────────────────────────────────────────────

async def reopen_ticket(ticket_number: str) -> dict:
    """
    Reopens a resolved ticket when customer sends a new message.
    Called externally by Team-3's message service — NOT a direct API endpoint.
    Status goes back to in_progress. Same engineer remains assigned.
    """
    ticket = await tickets_collection.find_one({"ticket_number": ticket_number})

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_number} not found."
        )

    if ticket["status"] != TicketStatus.RESOLVED:
        # Silently ignore if not resolved (already open or closed)
        return serialize_ticket(ticket)

    updated = await tickets_collection.find_one_and_update(
        {"ticket_number": ticket_number},
        {"$set": {
            "status": TicketStatus.IN_PROGRESS,
            "updated_at": utcnow()
        }},
        return_document=True
    )

    # ── PLACEHOLDER: Team-3 notify assigned engineer ticket reopened ──────
    # await notify_engineer(ticket["assigned_engineer_id"], WSEvent.TICKET_REOPENED, updated)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(updated)

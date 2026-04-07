from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status

from app.config.db import get_database
from app.constants.ticket_status import TicketStatus, SUBJECT_PRIORITY_MAP, PREDEFINED_SUBJECTS
from app.constants.roles import Role


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def serialize_ticket(ticket: dict) -> dict:
    """Convert MongoDB ObjectId to string for JSON serialization."""
    if ticket and "_id" in ticket:
        ticket["_id"] = str(ticket["_id"])
    return ticket


async def get_next_ticket_id() -> int:
    """Auto-increment ticket_id using MongoDB counters collection."""
    db = get_database()
    result = await db["counters"].find_one_and_update(
        {"_id": "ticket_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return result["seq"]


def generate_ticket_number(ticket_id: int) -> str:
    return f"TCK-{ticket_id}"


def extract_user_id(current_user: dict) -> int:
    """
    Extract integer ID from auth token's sub field.
    Auth module stores sub as "customer_1" or "support_101".
    """
    sub = current_user.get("sub", "")
    try:
        return int(sub.split("_")[-1])
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user token format."
        )


# ─────────────────────────────────────────────
# Get Predefined Subjects (for frontend dropdown)
# ─────────────────────────────────────────────

def get_predefined_subjects() -> list:
    return PREDEFINED_SUBJECTS


# ─────────────────────────────────────────────
# Create Ticket
# ─────────────────────────────────────────────

async def create_ticket(current_user: dict, subject: str, description: str) -> dict:
    """
    Creates a new support ticket for a customer.
    Priority is auto-assigned from SUBJECT_PRIORITY_MAP.
    customer_id is extracted from the JWT token's sub field.
    """
    if subject not in SUBJECT_PRIORITY_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid subject. Choose from predefined subjects: {PREDEFINED_SUBJECTS}"
        )

    db = get_database()
    customer_id = extract_user_id(current_user)
    priority = SUBJECT_PRIORITY_MAP[subject]
    ticket_id = await get_next_ticket_id()
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

    await db.tickets.insert_one(ticket_doc)

    # ── PLACEHOLDER: Team-3 notify all online engineers ──────────────────
    # await notify_all_engineers(ticket_doc)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(ticket_doc)


# ─────────────────────────────────────────────
# Get My Tickets (Customer)
# ─────────────────────────────────────────────

async def get_my_tickets(current_user: dict) -> list:
    """Returns all tickets belonging to the logged-in customer."""
    db = get_database()
    customer_id = extract_user_id(current_user)

    cursor = db.tickets.find(
        {"customer_id": customer_id},
        {"messages": 0}
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
    db = get_database()
    cursor = db.tickets.find(
        {"status": TicketStatus.OPEN, "assigned_engineer_id": None},
        {"messages": 0}
    ).sort("created_at", 1)  # Oldest first for first-come-first-serve fairness

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
    """Returns all tickets with optional filters. Only for support engineers and admin."""
    db = get_database()
    query = {}

    if status_filter:
        valid_statuses = [
            TicketStatus.OPEN, TicketStatus.IN_PROGRESS,
            TicketStatus.RESOLVED, TicketStatus.CLOSED
        ]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Valid values: {valid_statuses}"
            )
        query["status"] = status_filter

    if priority_filter:
        if priority_filter not in ["low", "medium", "high"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid priority. Valid values: low, medium, high"
            )
        query["priority"] = priority_filter

    if assigned_engineer_id is not None:
        query["assigned_engineer_id"] = assigned_engineer_id

    cursor = db.tickets.find(query, {"messages": 0}).sort("created_at", -1)

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
    Customer: can only view their own ticket.
    Support / Admin: can view any ticket.
    """
    db = get_database()
    ticket = await db.tickets.find_one({"ticket_number": ticket_number})

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_number} not found."
        )

    if current_user.get("role") == Role.CUSTOMER:
        customer_id = extract_user_id(current_user)
        if ticket["customer_id"] != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket."
            )

    return serialize_ticket(ticket)


# ─────────────────────────────────────────────
# Take Ticket (Support Engineer)
# ─────────────────────────────────────────────

async def take_ticket(ticket_number: str, current_user: dict) -> dict:
    """
    Assigns an open ticket to the requesting support engineer.
    Engineer must be online. First-come-first-serve via atomic update.
    """
    if not current_user.get("is_online", False):
        # Fallback: check DB directly since token may not reflect live status
        db = get_database()
        engineer_id = extract_user_id(current_user)
        engineer = await db.support_engineers.find_one({"support_id": engineer_id})
        if not engineer or not engineer.get("is_online", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be online to take a ticket. Please login again."
            )

    db = get_database()
    engineer_id = extract_user_id(current_user)

    # Atomic update: only succeeds if ticket is still open & unassigned
    result = await db.tickets.find_one_and_update(
        {
            "ticket_number": ticket_number,
            "status": TicketStatus.OPEN,
            "assigned_engineer_id": None
        },
        {
            "$set": {
                "assigned_engineer_id": engineer_id,
                "status": TicketStatus.IN_PROGRESS,
                "updated_at": utcnow()
            }
        },
        return_document=True
    )

    if not result:
        existing = await db.tickets.find_one({"ticket_number": ticket_number})
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
# Resolve Ticket
# ─────────────────────────────────────────────

async def resolve_ticket(ticket_number: str, current_user: dict) -> dict:
    """
    Marks a ticket as resolved.
    Only the assigned engineer or admin can resolve.
    Customer messaging again on resolved ticket triggers reopen_ticket() via Team-3.
    """
    db = get_database()
    ticket = await db.tickets.find_one({"ticket_number": ticket_number})

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

    if current_user.get("role") != Role.ADMIN:
        engineer_id = extract_user_id(current_user)
        if ticket["assigned_engineer_id"] != engineer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned engineer can resolve this ticket."
            )

    updated = await db.tickets.find_one_and_update(
        {"ticket_number": ticket_number},
        {"$set": {"status": TicketStatus.RESOLVED, "updated_at": utcnow()}},
        return_document=True
    )

    # ── PLACEHOLDER: Team-3 notify customer ticket is resolved ────────────
    # await notify_customer(ticket["customer_id"], WSEvent.TICKET_RESOLVED, updated)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(updated)


# ─────────────────────────────────────────────
# Close Ticket
# ─────────────────────────────────────────────

async def close_ticket(ticket_number: str, current_user: dict) -> dict:
    """
    Permanently closes a ticket.
    Can close from in_progress or resolved — not from open.
    Only assigned engineer or admin can close.
    """
    db = get_database()
    ticket = await db.tickets.find_one({"ticket_number": ticket_number})

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_number} not found."
        )

    closeable_statuses = [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED]
    if ticket["status"] not in closeable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot close ticket with status '{ticket['status']}'. Must be in_progress or resolved."
        )

    if current_user.get("role") != Role.ADMIN:
        engineer_id = extract_user_id(current_user)
        if ticket["assigned_engineer_id"] != engineer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned engineer can close this ticket."
            )

    now = utcnow()
    updated = await db.tickets.find_one_and_update(
        {"ticket_number": ticket_number},
        {"$set": {"status": TicketStatus.CLOSED, "closed_at": now, "updated_at": now}},
        return_document=True
    )

    # ── PLACEHOLDER: Team-3 notify customer ticket is closed ─────────────
    # await notify_customer(ticket["customer_id"], WSEvent.TICKET_CLOSED, updated)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(updated)


# ─────────────────────────────────────────────
# Reopen Ticket — Called by Team-3 Message Service
# ─────────────────────────────────────────────

async def reopen_ticket(ticket_number: str) -> dict:
    """
    Reopens a resolved ticket when customer sends a new message.
    NOT a direct API endpoint — called by Team-3's message service.
    Same engineer stays assigned. Status goes back to in_progress.
    """
    db = get_database()
    ticket = await db.tickets.find_one({"ticket_number": ticket_number})

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_number} not found."
        )

    if ticket["status"] != TicketStatus.RESOLVED:
        return serialize_ticket(ticket)  # Already open or closed — silently ignore

    updated = await db.tickets.find_one_and_update(
        {"ticket_number": ticket_number},
        {"$set": {"status": TicketStatus.IN_PROGRESS, "updated_at": utcnow()}},
        return_document=True
    )

    # ── PLACEHOLDER: Team-3 notify assigned engineer ticket reopened ──────
    # await notify_engineer(ticket["assigned_engineer_id"], WSEvent.TICKET_REOPENED, updated)
    # ─────────────────────────────────────────────────────────────────────

    return serialize_ticket(updated)
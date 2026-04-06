# ticket_chat_system

```
ticket_support_system/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── config/
│   │     ├── db.py
│   │     ├── settings.py
│   │
│   ├── schemas/                  # Pydantic schemas (DB + API)
│   │     ├── customer_schema.py
│   │     ├── support_schema.py
│   │     ├── auth_schema.py
│   │     ├── ticket_schema.py
│   │     ├── message_schema.py
│   │
│   ├── routes/                  # API endpoints
│   │     ├── auth_routes.py
│   │     ├── ticket_routes.py
│   │     ├── message_routes.py
│   │
│   ├── services/                # Business logic
│   │     ├── auth_service.py
│   │     ├── ticket_service.py
│   │     ├── message_service.py
│   │
│   ├── websocket/               # Real-time system
│   │     ├── manager.py
│   │     ├── websocket_routes.py
│   │
│   ├── dependencies/            # Auth & RBAC
│   │     ├── auth_dependency.py
│   │     ├── role_dependency.py
│   │
│   ├── utils/                   # Helper functions
│   │     ├── jwt.py
│   │     ├── hash.py
│   │     ├── id_generator.py
│   │
│   ├── constants/               # Fixed values
│   │     ├── ticket_status.py
│   │     ├── roles.py
│   │     ├── websocket_events.py
│   │
│   └── database/                # Optional (if you want separation)
│         ├── customer_collection.py
│         ├── support_collection.py
│         ├── ticket_collection.py
│
├── requirements.txt
├── .env
└── README.md

```

steps

->Backend setup

- cd auth-system/backend
- python -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- python scripts/input_data.py
- uvicorn app.main:app --reload

->Customer Frontend

- cd auth-system/frontend-customer
- npm install
- npm run dev

->admin Frontend

- cd auth-system/frontend-admin
- npm install
- npm run dev

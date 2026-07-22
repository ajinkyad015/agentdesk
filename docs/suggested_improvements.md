# 1. When authentication is implemented, don't return only a UUID.

Instead return the full ORM model:

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

Then routes can access:

current_user.id

current_user.email

current_user.is_active

without issuing another database query.



# 2. My proposed implementation sequence
Update the User model with authentication fields.
Generate and apply a new Alembic migration.
Build app/auth/password.py.
Build app/auth/jwt.py.
Build app/auth/service.py.
Build app/auth/dependencies.py.
Replace the temporary CurrentUserID in api/deps.py with a real authenticated CurrentUser.
Implement /auth/register and /auth/login.
Start the conversation and chat routers.

This approach minimizes rework and gives you a secure foundation before exposing the rest of the API.

implement the authentication

# 3. Authentication roadmap

After that, we'll implement the entire authentication module in this order:

app/
├── auth/
│   ├── __init__.py
│   ├── password.py        ← Password hashing
│   ├── jwt.py             ← JWT creation & validation
│   ├── service.py         ← Registration & login
│   ├── dependencies.py    ← Current user dependency
│   └── exceptions.py      ← Auth-specific exceptions

Then:

api/
├── deps.py
└── v1/
    └── routers/
        └── auth.py

# 4. One important improvement

I also want to improve the current architecture before writing auth.

Right now ConversationService directly creates repositories:

self.conversations = ConversationRepository(session)
self.messages = MessageRepository(session)

As the application grows, every service will repeat this pattern.

Instead, I recommend introducing a Unit of Work abstraction:

AgentService
      │
      ▼
UnitOfWork
      │
 ┌────┼────┐
 ▼    ▼    ▼
Users Conversations Messages

Benefits:

One place to manage transactions
Cleaner services
Easier testing
Simpler dependency injection

This is a common production pattern, but it is not required to implement authentication. We can introduce it later if you prefer to keep moving quickly.

My recommendation

Before implementing authentication, let's do these two changes:

Update the User model with the authentication fields.
Create one Alembic migration for those changes


# 5.Future improvements

This implementation is a solid foundation, but production systems often add additional claims:

payload = {
    "sub": str(user.id),
    "email": user.email,
    "role": "admin",
    "jti": str(uuid4()),      # unique token ID
    "iss": "agentdesk",       # issuer
    "aud": "agentdesk-api",   # audience
    "type": "access",
    "iat": now,
    "nbf": now,
    "exp": ...
}

The jti claim is particularly useful if you later implement token revocation
# 6. Improvement to api/deps.py

Once this file exists, replace the placeholder dependency with aliases using Annotated:

from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import (
    get_current_active_user,
    get_current_superuser,
    get_current_user,
)
from app.models.user import User


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

CurrentActiveUser = Annotated[
    User,
    Depends(get_current_active_user),
]

CurrentSuperUser = Annotated[
    User,
    Depends(get_current_superuser),
]

From this point onward, your routers can simply declare:

async def create_conversation(
    current_user: CurrentActiveUser,
    service: ConversationServiceDep,
):
    ...

No UUID extraction or repeated authorization logic is needed.

# 7.Improvement: Inject AuthService

One thing I'd change from the implementation above is to avoid instantiating AuthService inside each route:

service = AuthService(db)

Instead, add a dependency in app/api/deps.py:

from typing import Annotated
from fastapi import Depends

from app.auth.service import AuthService

def get_auth_service(db: DBSession) -> AuthService:
    return AuthService(db)

AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]

Then your routes become:

@router.post("/register")
async def register(
    payload: UserCreate,
    service: AuthServiceDep,
):
    return await service.register(payload)

This keeps the routing layer consistent with the rest of your architecture and makes the service easy to replace or mock in tests.
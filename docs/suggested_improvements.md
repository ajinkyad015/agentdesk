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


# 8. JWT  Remaining (Nice-to-have)

agree. At this point the authentication layer is sufficiently complete to build the rest of the application. We can defer things like email verification, refresh token persistence, password strength policies, etc.

The next milestone is the Conversation Router.

These are improvements rather than blockers.

1. Password strength validation ⭐⭐⭐

Currently:

len(password) >= 8

Better:

✓ uppercase
✓ lowercase
✓ number
✓ symbol
✓ minimum length

This is the biggest missing feature.

2. Automatic password rehash ⭐⭐⭐

During login:

if needs_rehash(user.password_hash):
    user.password_hash = hash_password(password)

Very small addition.

Very worthwhile.

3. JWT Claims ⭐⭐

Current payload probably resembles:

{
    "sub": "...",
    "type": "access",
    "iat": "...",
    "exp": "..."
}

A more production-ready payload would add:

{
    "iss": "agentdesk",
    "aud": "agentdesk-api",
    "jti": "...",
    "nbf": "...",
    "sub": "...",
    "type": "access"
}

Not essential for an MVP.

4. Centralized Security Constants ⭐

Instead of:

ACCESS_TOKEN_TYPE = "access"

Create:

auth/constants.py

Pure cleanup.

5. JWTManager / PasswordManager Classes ⭐

Current:

create_access_token()

verify_access_token()

Future:

jwt_manager.create_access()

jwt_manager.verify()

Mostly an architectural preference.

6. Better Exceptions ⭐⭐

Right now the router probably contains something like:

except InvalidCredentialsError:

You could introduce a global exception handler later, but it's not necessary now.

7. Email Verification Flow ⭐⭐⭐⭐

Currently:

email_verified = False

There is no:

verification token
email
verification endpoint

That's a future feature.

8. Refresh Token Storage ⭐⭐⭐⭐⭐

Right now refresh tokens are stateless JWTs.

A production system often stores them in the database to support:

logout
revoke one device
revoke all devices
device tracking

For a personal project or MVP, stateless refresh tokens are perfectly acceptable.

# 9.service/ conversation improvments ( Related to Exceptions):
I recommend one small improvement

Instead of:

raise ValueError("Conversation not found")

create a service exception.

app/services/exceptions.py

class ConversationNotFoundError(Exception):
    """Conversation was not found."""

Then:

raise ConversationNotFoundError()

The router maps it to:

except ConversationNotFoundError:
    raise HTTPException(
        status_code=404,
        detail="Conversation not found",
    )

This keeps FastAPI-specific concerns out of the service layer and makes the service reusable outside HTTP.

With these two methods in place, ConversationService is ready to support a full CRUD router.


# 10.  recommendation related to exceptions

Instead of wrapping every endpoint with:

try:
    ...
except ConversationNotFoundError:
    raise HTTPException(...)

introduce a global exception handler later:

@app.exception_handler(ConversationNotFoundError)
async def conversation_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Conversation not found"},
    )

Then the router becomes:

return await service.get_conversation(...)

with no try/except blocks. This keeps routers extremely thin and scales much better as you add more domain-specific exceptions.

With this router in place, you now have complete authenticated CRUD operations for conversations. The next router should be chat.py, which will connect AgentService to your LLM and persist the conversation history automatically.
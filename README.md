# Chuks Kitchen - System Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Flow Explanation](#flow-explanation)
3. [Edge Case Handling](#edge-case-handling)
4. [Assumptions](#assumptions)
5. [Scalability Thoughts](#scalability-thoughts)

---

## System Overview

### Purpose

Chuks Kitchen is a FastAPI-based food ordering and delivery platform that enables users to browse food items, add them to a shopping cart, and manage their orders. The system supports admin functionality for managing the food catalog.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Client Layer                               │
│                  (Web/Mobile Apps)                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Application                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              API Routes & Endpoints                     │    │
│  │  ├─ /signup/ (Auth)          ├─ /foods/ (Catalog)     │    │
│  │  ├─ /verify/ (Auth)          ├─ /cart/ (Shopping)     │    │
│  │  └─ HTTP Basic Auth          └─ Pagination Support    │    │
│  └──────────────────────────────▬──────────────────────────┘    │
│                                 │                                │
│  ┌──────────────────────────────▼──────────────────────────┐    │
│  │            Business Logic Layer (Services)              │    │
│  │  ├─ AuthServices      ├─ CartServices                   │    │
│  │  ├─ OTPServices       ├─ EmailServices                  │    │
│  │  └─ Password Hashing  └─ Error Handling                 │    │
│  └──────────────────────────────┬──────────────────────────┘    │
│                                 │                                │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
   ┌────────────▼────────┐ ┌────▼──────────┐ ┌──▼────────────┐
   │  SQLite Database    │ │  Redis Cache  │ │ Email Service │
   │  ├─ Users          │ │  (Sessions)   │ │ (Resend API)  │
   │  ├─ Foods          │ │  ├─ OTP Hash  │ └───────────────┘
   │  ├─ CartItems      │ │  └─ Temp Data │
   │  └─ Orders         │ └───────────────┘
   └────────────────────┘
```

### Core Components

#### 1. **Authentication System**

- **Signup Flow**: Email + Phone verification with OTP
- **Verification**: 6-digit OTP sent via email
- **Session Management**: Temporary sessions stored in Redis
- **Password Security**: Argon2 hashing (industry standard)
- **Authentication Method**: HTTP Basic Authentication (user_id + password)

#### 2. **Food Catalog System**

- **CRUD Operations**: Create, Read, Delete foods
- **Admin-Only Access**: Only admin users can create/modify foods
- **Customizable Items**: Foods can have side proteins and extra sides
- **Inventory Tracking**: Available_quantity field for stock management
- **Categorization**: Foods are organized by category

#### 3. **Shopping Cart System**

- **User-Specific Carts**: Each user has their own cart
- **Customizable Orders**: Support for side proteins and extra sides
- **Special Instructions**: Custom notes per cart item
- **Quantity Management**: Increment existing items or add new ones
- **Cart Operations**: Add to cart, view cart, clear cart

#### 4. **Data Persistence Layer**

- **Primary DB**: SQLite (lightweight, file-based)
- **Relationships**: Well-structured foreign keys and relationships
- **Session Management**: Dependency injection for database sessions
- **Transaction Safety**: Rollback on errors

#### 5. **Caching Layer**

- **Session Storage**: Redis for OTP verification sessions
- **Temporary Data**: Store user data during signup process
- **Session Expiry**: Automatic cleanup with TTL (time-to-live)
- **Attempt Tracking**: Anti-brute-force OTP attempt counting

---

## Flow Explanation

[View my flowchart diagrams on figma](https://www.figma.com/board/vtlMN8dmVoDG2J3JFt5vYc/Chuks-Kitchen-FlowChart?node-id=0-1&p=f&t=TVcphMQp4k1L5Xj9-0)

### Flow 1: User Registration & Email Verification

**Why These Design Decisions?**

1. **Async Email Task**: Email sending is moved to background using FastAPI's `BackgroundTasks`. This prevents blocking the response to the user.

2. **OTP Hash Storage**: The actual OTP is not stored; only its SHA256 hash is stored. This prevents exposure if Redis is compromised.

3. **Session-Based User Storage**: User data is stored temporarily in Redis during verification. This allows the user to complete signup only after email verification.

4. **Attempt Rate Limiting**: Limited to 5 OTP verification attempts with 600-second expiry. This prevents brute force attacks.

5. **HTTP-Only Secure Cookies**: The session_id is stored in HttpOnly cookies, protected in production with Secure and SameSite flags.

---

### Flow 2: Food Browsing & Pagination

**Why This Design?**

1. **Offset-Based Pagination**: Simple to implement and understand. Users specify how many items to skip and take.

2. **Configurable Limits**: Users can request 1-100 items. Default is 10 for balanced behavior.

3. **Navigation Links**: `next` and `prev` URLs are included in the response, allowing clients to easily navigate without manually constructing URLs.

---

### Flow 3: Shopping Cart Management

**Why This Design?**

1. **Upsert Pattern**: If an item already exists, increment quantity instead of creating duplicate entries. This prevents cart bloat.

2. **Foreign Key Constraints**: The database enforces that food_id, side_protein_id, and extra_side_id must exist in the Food table. Invalid references return 409 Conflict.

3. **User Isolation**: Cart queries are filtered by `buyer_id` at the database level. Users cannot access other users' carts.

4. **Lazy Retrieval**: Cart contents are fetched on-demand with full food details via JOIN operations, not cached, to ensure price accuracy.

---

## Edge Case Handling

### 1. **Authentication Edge Cases**

#### 1.1 Duplicate Email/Phone During Signup

```python
# In auth_services.py
def verify_credentials(self, email: EmailStr, phone_number: int):
    is_email_in_use = (
        self.db.exec(select(User.id).where(User.email == email)).first() is not None
    )
    if is_email_in_use:
        raise HTTPException(status_code=409, detail="This email is already in use")
```

**Handling**: Validation occurs BEFORE session creation. User gets immediate feedback if credentials are taken. No race condition because SQLite uses file-level locking.

#### 1.2 OTP Expiry

**Problem**: User takes 10 minutes to receive email and verify OTP, but token expires after 600 seconds (10 min).

**Solution**: Redis TTL is strict. After 600 seconds, the session hash is automatically deleted. When user tries to verify an expired OTP:

```python
async def get_user_verification_session(self, session_id: str):
    session_data = await cache.get_hash(f"signup_session:{session_id}")
    if not session_data:  # Hash doesn't exist (expired)
        raise HTTPException(status_code=404, detail="Session not found")
```

#### 1.3 Brute Force OTP Attacks

**Problem**: Attacker tries many OTP combinations (only 1 million possibilities: 000000-999999).

**Solution**:

- Limited to 5 attempts max
- After 5 failed attempts, the session is deleted
- Client must request a new OTP from signup endpoint
- No permanent account lockout (new signup clears the session)

```python
if no_of_attempts >= OTPServices.MAX_ATTEMPTS:
    await auth_service.delete_user_verification_session(signup_session_id)
    raise OTPValidationAttemptsExceededError()  # 429 Too Many Requests
```

#### 1.4 Invalid User ID in Authentication

**Problem**: Client provides invalid user_id or non-existent user.

**Solution**:

```python
def get_current_user(credentials: CredentialsDep, session: SessionDep):
    try:
        user_id = int(credentials.username)  # Parse as int
    except ValueError:
        raise InvalidCredentialError("user_id")  # 401 if not integer

    user = session.get(User, user_id)
    if user is None:  # 401 if user doesn't exist
        raise AuthFailedError()
```

---

### 2. **Cart Management Edge Cases**

#### 2.1 Adding Non-Existent Food

**Problem**: Client sends `food_id=999` which doesn't exist.

**Solution**: Database foreign key constraint prevents insertion:

```python
# CartItem has:
food_id: int = Field(foreign_key="food.id", primary_key=True)

# If food_id doesn't exist:
# IntegrityError is caught and returns 409
except exc.IntegrityError as e:
    self.db.rollback()
    raise HTTPException(
        status_code=409,
        detail="The new cart item is conflicting with another in the db"
    )
```

#### 2.2 Cart Item with Same Food + Same Side Protein

**Problem**: User tries to add the same item twice (same food, same side protein).

**Current Behavior**: Composite primary key `(food_id, buyer_id)` means duplicates increment quantity instead of creating new records. Side proteins are not part of the primary key, so there could be conflicts.

**Potential Issue**: If user adds Food #1 with Side Protein #2, then adds Food #1 with Side Protein #3, the second request will fail because `(food_id=1, buyer_id=X)` already exists.

**Recommendation** (Not implemented): Primary key should be `(food_id, buyer_id, side_protein_id, extra_side_id)` to allow multiple variations of the same food.

#### 2.3 Invalid Side Protein/Extra Side IDs

**Solution**: Foreign key constraints enforce validity. Invalid IDs cause 409 Conflict.

#### 2.4 Concurrent Cart Modifications

**Problem**: User adds items to cart from two devices simultaneously.

**Current Behavior**:

- Device 1: GET cart, read quantity=1, increment to 2, save
- Device 2: GET cart, read quantity=1, increment to 2, save
- Result: Both devices overwrite each other (last write wins)

**Solution**: SQLite lacks optimistic locking. Mitigations:

1. Accept eventual consistency (cart shows last written value)
2. Add version field and check before update
3. Use pessimistic locking (row-level locks) - requires PostgreSQL
4. Accept as acceptable for this scale (100 users)

---

### 3. **Database Edge Cases**

#### 3.1 Database Connection Failure

**Problem**: SQLite database file is locked or corrupted.

**Current Handling**:

```python
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()  # Creates if doesn't exist
    cache.connect()
```

If the database is inaccessible, the application will crash at startup. No retry logic.

**Recommendation**: Add startup health checks and retry with exponential backoff.

#### 3.2 Transaction Rollback

All service methods include rollback on error:

```python
except exc.SQLAlchemyError:
    self.db.rollback()
    raise HTTPException(status_code=500, detail="Something went wrong...")
```

This prevents partial updates from persisting.

---

### 4. **Email Service Edge Cases**

#### 4.1 Email Delivery Failure

**Problem**: Resend API is down or email bounces.

**Current Handling**: Email is sent as background task. If it fails, only the error is logged:

```python
@classmethod
def send_otp_mail(cls, *, to: EmailStr, otp: str | int):
    try:
        email: resend.Emails.SendResponse = resend.Emails.send(params)
        return email
    except Exception as e:
        print(f"unable to send email due to {e}")  # Silent failure
```

**Problem**: User sees "OTP sent" but never receives the email.

**Recommendation**:

1. Implement retry logic with exponential backoff
2. Queue failed emails in Redis for manual retry
3. Return user notification: "May take up to 5 minutes"

#### 4.2 Invalid Email Address

**Problem**: User enters `user@localhost.localdomain` (invalid public email).

**Current Handling**: Pydantic `EmailStr` validates format, not deliverability. Resend will reject invalid domains.

**Recommendation**: Use email verification service or implement double opt-in during signup.

---

### 5. **Pagination Edge Cases**

#### 5.1 Offset Beyond Total Items

```
GET /foods/?limit=10&offset=1000 (when only 50 foods exist)
```

**Current Behavior**: Returns empty list with `next=null, prev=url`

**Issue**: No indication to client that offset is invalid. Client might think there are zero foods.

**Recommendation**: Include `total_count` in response to inform client of actual data size.

#### 5.2 Negative Offset or Limit

**Protected by validation**:

```python
limit: int = Query(10, ge=1, le=100),  # 1-100
offset: int = Query(0, ge=0),           # ≥0
```

---

### 6. **Redis/Cache Edge Cases**

#### 6.1 Redis Connection Failure

**Problem**: Redis server is down during OTP verification.

```
await cache.connect()  # Startup
```

**Current Handling**: If Redis fails at startup, the app crashes. No fallback.

**Recommendation**:

1. Add in-memory session fallback for development
2. Use Redis sentinel for high availability
3. Implement connection retry logic

#### 6.2 Session Data Corruption

**Problem**: Redis network glitch corrupts session data mid-serialization.

**Current Handling**: None. Malformed data will cause JSON parsing to fail.

**Recommendation**: Implement data validation and checksums for critical session data.

---

## Assumptions

### Product Assumptions

1. **Food Customization Scope**: System assumes each food item can have at most ONE side protein and ONE extra side. Foods like "Jollof Rice with Chicken and Coleslaw" are pre-defined menu items, not dynamically customizable.

2. **No Promotion/Discount System**: No coupon codes or promotional pricing. Assumption: Discounts managed manually by admins through menu prices.

3. **Basic User Profiles**: No address, payment method storage, order history endpoints. Assumption: Minimal user data for MVP.

---

### Technical Assumptions

1. **SQLite Suitable for Scale**: Current choice is SQLite for simplicity. Assumption: System won't exceed single-database capacity (100-1000 concurrent users). At 10,000+ users, PostgreSQL is required.

2. **Redis for Session Only**: Redis only stores temporary OTP sessions, not user carts or orders. Assumption: Critical data persists to SQLite; Redis is ephemeral.

3. **Synchronous Password Hashing**: Argon2 password hashing is CPU-intensive (by design) but runs synchronously in request handler. Assumption: Acceptable for signup endpoint (not on critical path) with typical volume.

4. **No Rate Limiting**: No global rate limit on API endpoints. Users can spam requests. Assumption: Reverse proxy (Nginx/CloudFlare) handles rate limiting in production.

5. **CORS Open**: `allow_origins=["*"]` allows any domain. Assumption: Behind API gateway with proper CORS policy, or intentional open-lab environment.

6. **No Request Validation Limits**: No request size limits. Assumption: Reverse proxy enforces limits.

7. **Synchronous Database Operations**: All DB operations are synchronous, not async. FastAPI overhead from async definition unused. Assumption: Single SQLite connection sufficient; migration to async only needed with PostgreSQL/async driver.

8. **Environment Variables**: All secrets (REDIS_URL, RESEND_API_KEY) loaded from environment. Assumption: Proper secret management in deployment.

9. **Email as Primary Verification**: OTP sent via email. Assumption: Users have email access; no SMS or 2FA alternative.

10. **No Multi-Tenancy**: Single instance serves one restaurant (Chuks Kitchen). Assumption: Future scaling requires architectural changes for multi-restaurant support.

---

### Data Assumptions

2. **Price as Integer**: `price: int` assumes price is stored in whole units (cents). Assumption: No fractional pricing (e.g., $2.99 stored as 299 cents).

3. **Unique Email & Phone**: Both are database-level unique constraints. Assumption: Valid uniqueness checks;

4. **No Soft Deletes**: No `deleted_at` timestamp. Assumption: Users and foods are rarely deleted; historical data less important than simplicity.

5. **No Audit Logging**: No `created_at`, `updated_at` on food items. Assumption: Track changes manually or not required for compliance.

---

### Deployment Assumptions

1. **Single Instance Deployment**: No load balancing, no horizontal scaling. Assumption: Single server handles all traffic initially.

2. **SQLite Single Writer**: SQLite allows only one concurrent writer. Assumption: Acceptable for 100 users; concurrent requests queue sequentially.

3. **Environment File Management**: `.env` or environment variables required for configuration. Assumption: Proper DevOps process for secret rotation.

4. **Startup Migration**: `create_db_and_tables()` runs on every startup. Assumption: Idempotent; safe to call repeatedly.

5. **Health Checks Missing**: No `/health/` endpoint for load balancers. Assumption: Platform-specific health checks (Kubernetes probes) used if containerized.

---

## Scalability Thoughts

### Current State: 100 Users

- **Database**: SQLite file-based, single file shared via disk
- **Caching**: Redis for OTP sessions only
- **Compute**: Single FastAPI process
- **Expectations**: Response times <200ms, 99.9% uptime acceptable

### Target State: 10,000+ Users

#### Database Optimization

- Switch to asynchronous postgresql
- Implement connection pooling
- Add proper db indexes to frequently queried fields
- Detecting slow queries and removing N+1 queries

#### Endpoints Optimization

- Implement rate-limiting endpoints to reduce ddos attacks
- Cache frequently queried GET endpoints response with redis
- Implement load balancer using Nginx

#### Architecture Optimization

- Implement a microservice architecture with isolated API services
- Implementing layered caching with in memory, redis and database respectively

---

## Tech Stack Summary

| Layer              | Current       | Recommended for 10K+ Users |
| ------------------ | ------------- | -------------------------- |
| **Framework**      | FastAPI       | FastAPI + Async/Await      |
| **Database**       | SQLite        | PostgreSQL + Replicas      |
| **Cache**          | Redis         | Redis Cluster              |
| **Authentication** | HTTP Basic    | OAuth2 + OpenID Connect    |
| **Email**          | Resend        | Resend + Queue (SQS)       |
| **Deployment**     | Single Server | Kubernetes                 |

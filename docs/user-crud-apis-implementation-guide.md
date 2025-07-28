# User CRUD APIs Implementation Guide

## Overview

This document provides a comprehensive guide for implementing CRUD (Create, Read, Update, Delete) operations for user management in the Hamilton tracking server.

## Current User Model

Based on the existing codebase, our User model includes:

- **email**: EmailField (unique)
- **first_name**: TextField
- **last_name**: TextField
- **auth_provider_type**: CharField (choices from AuthProvider)
- **auth_provider_user_id**: CharField
- **salt**: UUIDField (for API keys)

## Authentication

All API endpoints require authentication using one of the following methods:

- **Bearer Token**: PropelAuth bearer token
- **API Key**: User-specific API key in headers
- **Local Mode**: x-api-user and x-api-key headers (development only)

## CRUD Operations

### 1. Create User (POST /v1/users)

**Endpoint:** `POST /v1/users`

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "auth_provider_type": "propelauth"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

### 2. Read User (GET /v1/users/{id})

**Endpoint:** `GET /v1/users/{id}`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

### 3. List Users (GET /v1/users)

**Endpoint:** `GET /v1/users`

**Query Parameters:**
- `limit`: Number of users to return (default: 100)
- `offset`: Number of users to skip
- `search`: Search by email or name

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### 4. Update User (PUT /v1/users/{id})

**Endpoint:** `PUT /v1/users/{id}`

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

### 5. Delete User (DELETE /v1/users/{id})

**Endpoint:** `DELETE /v1/users/{id}`

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation errors)
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **500**: Internal Server Error

**Error Response Format:**
```json
{
  "error": "Error message",
  "details": "Additional error details",
  "code": "ERROR_CODE"
}
```

## Implementation Steps

1. **Create Schema Classes** (in `trackingserver_auth/schema.py`):
   - UserIn - for create/update operations
   - UserListOut - for list operations with pagination

2. **Add API Endpoints** (in `trackingserver_auth/api.py`):
   - Implement all CRUD operations
   - Add proper permission decorators
   - Include input validation

3. **Create Permission Functions** (in `trackingserver_base/permissions/permissions.py`):
   - user_can_create_user
   - user_can_read_user
   - user_can_update_user
   - user_can_delete_user

4. **Add Tests** (in `tests/`):
   - Unit tests for each endpoint
   - Permission tests
   - Integration tests

## Security Considerations

- **Email Uniqueness**: Ensure email addresses remain unique
- **Soft Delete**: Consider implementing soft delete instead of hard delete
- **Audit Trail**: Log all user modifications
- **Rate Limiting**: Implement rate limiting for user creation
- **Data Validation**: Validate all input data

## Testing Strategy

1. **Unit Tests**:
   - Test each CRUD operation individually
   - Test validation logic
   - Test error handling

2. **Integration Tests**:
   - Test complete workflows
   - Test authentication integration

3. **API Tests**:
   - Use Django's test client
   - Test with different authentication methods

## Example Implementation

Here's a sample implementation for the create user endpoint:

```python
@router.post("/v1/users", response=UserOut, tags=["users"])
@permission(user_can_create_user)
async def create_user(request, user_data: UserIn) -> UserOut:
    """Create a new user.
    
    @param request: Django request with auth information
    @param user_data: User data to create
    @return: Created user information
    """
    # Validate email uniqueness
    if await User.objects.filter(email=user_data.email).aexists():
        raise HttpError(400, "User with this email already exists")
    
    # Create user
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        auth_provider_type=user_data.auth_provider_type
    )
    await user.asave()
    
    return UserOut.from_orm(user)
```

## Required Schema Additions

Add these schemas to `trackingserver_auth/schema.py`:

```python
class UserIn(Schema):
    """Schema for creating/updating users"""
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    auth_provider_type: str = Field(default="propelauth", description="Authentication provider")

class UserUpdate(Schema):
    """Schema for updating users (partial updates)"""
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")

class UserListOut(Schema):
    """Schema for paginated user list responses"""
    users: List[UserOut]
    total: int
    limit: int
    offset: int
```

## Required Permission Functions

Add these to `trackingserver_base/permissions/permissions.py`:

```python
async def user_can_create_user(request) -> bool:
    """Check if user can create new users"""
    user, teams = request.auth
    # Add your business logic here
    return user is not None

async def user_can_read_user(request, user_id: int = None) -> bool:
    """Check if user can read user information"""
    user, teams = request.auth
    # Add your business logic here
    return user is not None

async def user_can_update_user(request, user_id: int = None) -> bool:
    """Check if user can update user information"""
    user, teams = request.auth
    # Add your business logic here
    return user is not None

async def user_can_delete_user(request, user_id: int = None) -> bool:
    """Check if user can delete users"""
    user, teams = request.auth
    # Add your business logic here
    return user is not None
```

## Complete API Implementation

Add these endpoints to `trackingserver_auth/api.py`:

```python
@router.get("/v1/users", response=UserListOut, tags=["users"])
@permission(user_can_read_user)
async def list_users(
    request,
    limit: int = 100,
    offset: int = 0,
    search: str = None
) -> UserListOut:
    """List users with pagination and search"""
    query = User.objects.all()

    if search:
        query = query.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    total = await query.acount()
    users = [
        UserOut.from_orm(user)
        async for user in query.order_by('email')[offset:offset + limit]
    ]

    return UserListOut(
        users=users,
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/v1/users/{user_id}", response=UserOut, tags=["users"])
@permission(user_can_read_user)
async def get_user(request, user_id: int) -> UserOut:
    """Get a specific user by ID"""
    try:
        user = await User.objects.aget(id=user_id)
        return UserOut.from_orm(user)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

@router.put("/v1/users/{user_id}", response=UserOut, tags=["users"])
@permission(user_can_update_user)
async def update_user(request, user_id: int, user_data: UserUpdate) -> UserOut:
    """Update a user"""
    try:
        user = await User.objects.aget(id=user_id)

        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name

        await user.asave()
        return UserOut.from_orm(user)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")

@router.delete("/v1/users/{user_id}", tags=["users"])
@permission(user_can_delete_user)
async def delete_user(request, user_id: int):
    """Delete a user"""
    try:
        user = await User.objects.aget(id=user_id)
        await user.adelete()
        return {"message": "User deleted successfully"}
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
```

## Testing Examples

Create `tests/test_user_crud_api.py`:

```python
import pytest
from django.test import AsyncClient
from trackingserver_auth.models import User

@pytest.mark.asyncio
async def test_create_user():
    """Test user creation endpoint"""
    client = AsyncClient()
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        },
        headers={"x-api-user": "admin@example.com"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_list_users():
    """Test user listing endpoint"""
    # Create test user first
    await User.objects.acreate(
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )

    client = AsyncClient()
    response = await client.get(
        "/api/v1/users",
        headers={"x-api-user": "admin@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) >= 1
```

---
*Co-authored by Augment Code*

# User CRUD APIs Implementation Guide

This document outlines the implementation of Create, Read, Update, and Delete (CRUD) operations for user management in our Hamilton-based application.

## Overview

This guide covers the implementation of RESTful APIs for user management, including:
- User creation and registration
- User profile retrieval
- User profile updates
- User account deletion
- Authentication and authorization

## API Endpoints

### 1. Create User (POST /api/users)

**Purpose:** Register a new user in the system

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "password": "securePassword123",
  "country": "US",
  "signup_source": "web",
  "subscription_level": "free"
}
```

**Response (201 Created):**
```json
{
  "id": "user_123",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "country": "US",
  "signup_source": "web",
  "subscription_level": "free",
  "email_verified": false,
  "enabled": true,
  "registered_at": "2025-01-07T10:30:00Z"
}
```

### 2. Get User (GET /api/users/{user_id})

**Purpose:** Retrieve user information by ID

**Path Parameters:**
- `user_id` (string): Unique identifier for the user

**Response (200 OK):**
```json
{
  "id": "user_123",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "country": "US",
  "signup_source": "web",
  "subscription_level": "premium",
  "email_verified": true,
  "enabled": true,
  "registered_at": "2025-01-07T10:30:00Z",
  "last_login": "2025-01-07T15:45:00Z"
}
```

### 3. Update User (PUT /api/users/{user_id})

**Purpose:** Update user profile information

**Path Parameters:**
- `user_id` (string): Unique identifier for the user

**Request Body:**
```json
{
  "name": "John Smith",
  "country": "CA",
  "subscription_level": "premium"
}
```

**Response (200 OK):**
```json
{
  "id": "user_123",
  "name": "John Smith",
  "email": "john.doe@example.com",
  "country": "CA",
  "subscription_level": "premium",
  "updated_at": "2025-01-07T16:00:00Z"
}
```

### 4. Delete User (DELETE /api/users/{user_id})

**Purpose:** Soft delete or deactivate a user account

**Path Parameters:**
- `user_id` (string): Unique identifier for the user

**Response:** 204 No Content

### 5. List Users (GET /api/users)

**Purpose:** Retrieve a paginated list of users

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Number of users per page (default: 20, max: 100)
- `country` (string, optional): Filter by country
- `subscription_level` (string, optional): Filter by subscription level

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": "user_123",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "country": "US",
      "subscription_level": "premium",
      "registered_at": "2025-01-07T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

## Data Model

Based on the Hamilton project structure, here's the recommended User data model:

```python
@dataclass
class User:
    id: str
    name: str
    email: str
    password_hash: str  # Never store plain text passwords
    country: str
    signup_source: str
    referral: Optional[str]
    signup_purpose: Optional[str]
    subscription_level: str
    payment_method: Optional[str]
    sso_id: Optional[str]
    email_verified: bool
    enabled: bool
    registered_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    
    def to_dict(self) -> dict:
        """Convert user object to dictionary for API responses"""
        props = {k: v for k, v in asdict(self).items() 
                if not k.startswith("_") and k != "password_hash"}
        props["registered_at"] = self.registered_at.isoformat()
        if self.updated_at:
            props["updated_at"] = self.updated_at.isoformat()
        if self.last_login:
            props["last_login"] = self.last_login.isoformat()
        return props
```

## Implementation with FastAPI

Since the Hamilton project uses FastAPI, here's the recommended API implementation structure:

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

app = FastAPI(title="User Management API")
security = HTTPBearer()

# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    country: str
    signup_source: str = "api"
    subscription_level: str = "free"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    subscription_level: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    country: str
    signup_source: str
    subscription_level: str
    email_verified: bool
    enabled: bool
    registered_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    # Implementation here
    pass

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    # Implementation here
    pass

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate):
    """Update user information"""
    # Implementation here
    pass

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """Delete/deactivate user"""
    # Implementation here
    pass

@app.get("/api/users", response_model=List[UserResponse])
async def list_users(
    page: int = 1,
    limit: int = 20,
    country: Optional[str] = None,
    subscription_level: Optional[str] = None
):
    """List users with pagination and filtering"""
    # Implementation here
    pass
```

## Security Considerations

### Authentication & Authorization
- **JWT Tokens:** Use JSON Web Tokens for stateless authentication
- **Password Hashing:** Use bcrypt or similar for password hashing
- **Rate Limiting:** Implement rate limiting to prevent abuse
- **Input Validation:** Validate all input data using Pydantic models

### Data Protection
- **HTTPS Only:** Ensure all API calls are made over HTTPS
- **Sensitive Data:** Never return password hashes in API responses
- **GDPR Compliance:** Implement proper data deletion for GDPR compliance

## Database Integration

For Hamilton-based applications, consider using:
- **SQLAlchemy:** For ORM-based database operations
- **Alembic:** For database migrations
- **PostgreSQL/MySQL:** For production databases
- **Redis:** For caching and session management

## Error Handling

Implement consistent error responses:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 'user_123' not found",
    "details": {
      "user_id": "user_123"
    }
  }
}
```

## Testing Strategy

- **Unit Tests:** Test individual API endpoints
- **Integration Tests:** Test database interactions
- **Load Tests:** Test API performance under load
- **Security Tests:** Test authentication and authorization

## Monitoring & Logging

- **API Metrics:** Track response times, error rates
- **User Activity:** Log user registration, login, updates
- **Security Events:** Log failed authentication attempts
- **Performance:** Monitor database query performance

## Next Steps

1. Set up the database schema and models
2. Implement the FastAPI endpoints
3. Add authentication and authorization middleware
4. Write comprehensive tests
5. Set up monitoring and logging
6. Deploy to staging environment for testing

---
*Co-authored by [Augment Code](https://www.augmentcode.com/?utm_source=atlassian&utm_medium=confluence_page&utm_campaign=confluence)*

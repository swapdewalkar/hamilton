"""Marshmallow schemas for request/response validation."""
from marshmallow import Schema, fields, validate, ValidationError


class UserCreateSchema(Schema):
    """Schema for creating a new user."""
    
    email = fields.Email(required=True, validate=validate.Length(max=120))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    age = fields.Int(validate=validate.Range(min=0, max=150), allow_none=True)


class UserUpdateSchema(Schema):
    """Schema for updating a user."""
    
    email = fields.Email(validate=validate.Length(max=120))
    first_name = fields.Str(validate=validate.Length(min=1, max=50))
    last_name = fields.Str(validate=validate.Length(min=1, max=50))
    age = fields.Int(validate=validate.Range(min=0, max=150), allow_none=True)


class UserResponseSchema(Schema):
    """Schema for user response."""
    
    id = fields.Int(dump_only=True)
    email = fields.Email()
    first_name = fields.Str()
    last_name = fields.Str()
    age = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserListResponseSchema(Schema):
    """Schema for user list response with pagination."""
    
    users = fields.List(fields.Nested(UserResponseSchema))
    total = fields.Int()
    page = fields.Int()
    per_page = fields.Int()
    pages = fields.Int()


class ErrorResponseSchema(Schema):
    """Schema for error responses."""
    
    error = fields.Str()
    message = fields.Str()
    details = fields.Dict(missing=dict)


# Schema instances
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema()
user_response_schema = UserResponseSchema()
user_list_response_schema = UserListResponseSchema()
error_response_schema = ErrorResponseSchema()

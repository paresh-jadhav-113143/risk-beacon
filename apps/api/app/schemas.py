from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    token: str
    user: dict


class SupplierCreate(BaseModel):
    legal_name: str
    country: str
    supplier_contact_email: Optional[EmailStr] = None
    supplier_contact_name: Optional[str] = None
    commodity_category: Optional[str] = None
    supplier_tier: Optional[str] = None


class SupplierUpdate(BaseModel):
    legal_name: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    commodity_category: Optional[str] = None
    supplier_tier: Optional[str] = None


class DocumentCreate(BaseModel):
    document_type: str
    file_name: str


class DecisionCreate(BaseModel):
    decision: str
    reason: str = Field(min_length=3)

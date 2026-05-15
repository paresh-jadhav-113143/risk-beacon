from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

CountryCode = Literal["IN", "US", "GB", "DE", "SG", "AE"]
Industry = Literal[
    "Electronic Components",
    "Manufacturing",
    "Packaging",
    "Information Technology",
    "Logistics",
    "Professional Services",
    "Raw Materials",
    "Pharmaceuticals",
]
CommodityCategory = Literal[
    "Electronic assemblies",
    "Semiconductors",
    "Packaging",
    "IT services",
    "Raw materials",
    "Logistics",
    "Professional services",
]
SupplierTier = Literal["Tier 1", "Tier 2", "Tier 3", "Strategic"]
DocumentType = Literal[
    "business_registration",
    "tax_certificate",
    "bank_letter",
    "financial_statement",
    "sustainability_certificate",
    "insurance_certificate",
    "quality_certificate",
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    token: str
    user: dict


class SupplierCreate(BaseModel):
    legal_name: str
    country: CountryCode
    supplier_contact_email: Optional[EmailStr] = None
    supplier_contact_name: Optional[str] = None
    commodity_category: Optional[CommodityCategory] = None
    supplier_tier: Optional[SupplierTier] = None


class SupplierUpdate(BaseModel):
    legal_name: Optional[str] = None
    country: Optional[CountryCode] = None
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[Industry] = None
    commodity_category: Optional[CommodityCategory] = None
    supplier_tier: Optional[SupplierTier] = None


class DocumentCreate(BaseModel):
    document_type: DocumentType
    file_name: str


class DecisionCreate(BaseModel):
    decision: str
    reason: str = Field(min_length=3)

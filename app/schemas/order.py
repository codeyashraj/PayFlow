from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderItemCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    quantity: int = Field(gt=0, le=10000)
    unit_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)

    @field_validator("product_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("product_name cannot be blank")
        return v


class OrderCreateRequest(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, v: str) -> str:
        return v.upper()


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime | None
    items: list[OrderItemResponse]


class PaginatedOrdersResponse(BaseModel):
    items: list[OrderResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

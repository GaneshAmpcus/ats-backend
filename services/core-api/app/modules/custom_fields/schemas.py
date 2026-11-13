from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.modules.custom_fields.enums import CustomFieldEntity, CustomFieldType


class CustomFieldDefinitionCreate(BaseModel):
    entity_type: CustomFieldEntity
    field_key: str
    field_label: str
    field_type: CustomFieldType
    is_required: bool = False
    is_active: bool = True
    display_order: int = 0
    options: dict[str, Any] | None = None


class CustomFieldDefinitionUpdate(BaseModel):
    field_label: str | None = None
    is_required: bool | None = None
    is_active: bool | None = None
    display_order: int | None = None
    options: dict[str, Any] | None = None


class CustomFieldDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: CustomFieldEntity
    field_key: str
    field_label: str
    field_type: CustomFieldType
    is_required: bool
    is_active: bool
    display_order: int
    options: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class CustomFieldValueBase(BaseModel):
    definition_id: UUID
    entity_id: UUID
    value_text: str | None = None
    value_number: Decimal | None = None
    value_date: date | None = None
    value_boolean: bool | None = None
    value_json: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _only_one_value(self) -> "CustomFieldValueBase":
        values = (
            self.value_text,
            self.value_number,
            self.value_date,
            self.value_boolean,
            self.value_json,
        )
        if sum(value is not None for value in values) > 1:
            raise ValueError(
                "Only one of value_text, value_number, value_date, "
                "value_boolean, value_json may be set."
            )
        return self


class CustomFieldValueCreate(CustomFieldValueBase):
    pass


class CustomFieldValueRead(CustomFieldValueBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

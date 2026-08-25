from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConstructionSiteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ConstructionSiteCreate(ConstructionSiteBase):
    pass


class ConstructionSiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ConstructionSiteResponse(ConstructionSiteBase):
    id: int
    owner_id: int
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


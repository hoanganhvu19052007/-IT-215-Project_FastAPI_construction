from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConstructionSiteBase(BaseModel):
    name: str
    description: Optional[str] = None


class ConstructionSiteCreate(ConstructionSiteBase):
    pass


class ConstructionSiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ConstructionSiteResponse(ConstructionSiteBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

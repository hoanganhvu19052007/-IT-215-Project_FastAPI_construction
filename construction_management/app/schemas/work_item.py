from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH)$")
    due_date: Optional[datetime] = None


class WorkItemCreate(WorkItemBase):
    site_id: int
    assignee_id: Optional[int] = None


class WorkItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(TODO|IN_PROGRESS|DONE)$")
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH)$")
    due_date: Optional[datetime] = None


class WorkItemResponse(WorkItemBase):
    id: int
    site_id: int
    assignee_id: Optional[int]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

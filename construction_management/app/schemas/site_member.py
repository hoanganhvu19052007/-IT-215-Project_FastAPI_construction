from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SiteMemberBase(BaseModel):
    site_id: int
    user_id: int
    role: str


class SiteMemberResponse(SiteMemberBase):
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

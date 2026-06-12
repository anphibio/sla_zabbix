from datetime import datetime

from pydantic import BaseModel


class MaintenanceWindowCreate(BaseModel):
    service_key: str
    name: str
    description: str
    start_at: datetime
    end_at: datetime


class MaintenanceWindowResponse(BaseModel):
    service_key: str
    name: str
    description: str
    start_at: datetime
    end_at: datetime
    is_active: bool

import uuid
from dataclasses import dataclass, field
from typing import Literal


ServiceSourceType = Literal["tag", "hostgroup"]


@dataclass(frozen=True)
class ServiceCatalogItem:
    name: str
    key: str
    source_type: ServiceSourceType
    source_value: str
    is_active: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)

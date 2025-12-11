from typing import List
from pydantic import BaseModel
from .entity_model import Entity
from .relation_model import Relationship


class UploadResponse(BaseModel):
    message: str
    pdf_name: str
    entities_count: int
    relationships_count: int
    entities: List[Entity]
    relationships: List[Relationship]
    source_note: str

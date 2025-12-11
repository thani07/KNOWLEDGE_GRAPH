from typing import List, Optional
from pydantic import BaseModel, Field


class Relationship(BaseModel):
    source_id: str = Field(..., description="ID of source entity, e.g. E1")
    target_id: str = Field(..., description="ID of target entity, e.g. E2")
    type: str = Field(..., description="Relationship type, e.g. TREATS, CAUSES, IS_PART_OF")

    description: Optional[str] = None

    source_pdf: Optional[str] = None
    source_pages: Optional[List[int]] = None
    source_text: Optional[str] = None

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0",
    )

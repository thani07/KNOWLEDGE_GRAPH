from typing import List, Optional
from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: str = Field(..., description="Unique ID within the PDF or chunk, e.g. E1")
    name: str
    type: str
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

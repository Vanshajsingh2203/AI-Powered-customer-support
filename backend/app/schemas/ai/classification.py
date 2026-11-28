from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class TicketClassification(BaseModel):
    """
    AI classification result for a support ticket.

    Reusable by other AI components. All fields are validated by Pydantic.
    """

    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The support category for the ticket (e.g. billing, technical, account).",
    )
    priority: Literal["LOW", "MEDIUM", "HIGH", "URGENT"] = Field(
        ...,
        description="Urgency priority. Must match the ticket system's priority check constraint.",
    )
    sentiment: Literal["POSITIVE", "NEUTRAL", "NEGATIVE", "FRUSTRATED"] = Field(
        ...,
        description="Customer sentiment detected in the ticket content.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1 for the classification.",
    )
    reasoning: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Brief explanation of why this classification was chosen.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "billing",
                "priority": "HIGH",
                "sentiment": "FRUSTRATED",
                "confidence": 0.85,
                "reasoning": "Customer reports being charged twice and is upset about the duplicate charge.",
            }
        }
    )


class ClassificationInput(BaseModel):
    """
    Input data for ticket classification.
    """

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Duplicate charge on my account",
                "description": "I was charged twice for the same subscription this month.",
            }
        }
    )

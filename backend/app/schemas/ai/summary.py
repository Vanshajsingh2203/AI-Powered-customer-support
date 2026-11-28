from pydantic import BaseModel, Field, ConfigDict
from typing import List


class TicketSummary(BaseModel):
    """AI-generated summary of a ticket's conversation.

    Provides a human-readable summary of the ticket title, description,
    and conversation messages for agent review.
    """

    issue_summary: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Brief explanation of the reported issue.",
    )
    key_points: List[str] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="Important points extracted from the conversation.",
    )
    troubleshooting_steps: List[str] = Field(
        ...,
        min_items=0,
        max_items=10,
        description="Troubleshooting steps already attempted.",
    )
    current_situation: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Current state of the issue.",
    )
    unresolved_questions: List[str] = Field(
        ...,
        min_items=0,
        max_items=10,
        description="Unresolved questions or open issues.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issue_summary": "Customer reports duplicate charge on their account.",
                "key_points": [
                    "Customer charged twice for same subscription",
                    "Subscription activated 3 months ago",
                ],
                "troubleshooting_steps": [
                    "Checked billing cycle dates",
                    "Verified payment method on file",
                ],
                "current_situation": "Customer is frustrated about the duplicate charge.",
                "unresolved_questions": [
                    "Is the second charge a system error?",
                    "Does the customer need a refund?",
                ],
            }
        }
    )
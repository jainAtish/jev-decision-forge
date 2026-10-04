from typing import Literal
from pydantic import BaseModel, Field

class TicketDecision(BaseModel):
    department: Literal[
        "billing",
        "technical",
        "sales",
        "account",
    ]
    urgency: int = Field(
        ge=1,
        le=10,
        description="Urgency level of the support ticket",
    )
    needs_human: bool = Field(
        description="Whether the ticket needs human intervention",
    )
    refund_request: bool = Field(
        description="Whether the customer is requesting a refund",
    )

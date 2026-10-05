from laya import Router
from typing import Tuple

from app.models import TicketDecision


router = Router()


def classify_with_laya(
    subject: str,
    message: str,
) -> Tuple[TicketDecision, dict]:

    state = f"""
    Analyze the following customer support ticket.
    Subject:
    {subject}
    Message:
    {message}
    Determine:
    1. Which department should handle the ticket.
    2. How urgent the ticket is from 1 to 10.
    3. Whether a human should review it.
    4. Whether the customer is asking for a refund.
    """

    questions = {
        "department": {
            "type": "choice",
            "instructions": "Which department should handle this ticket?",
            "criteria": [
                "billing",
                "technical",
                "sales",
                "account",
            ],
        },

        "urgency": {
            "type": "score",
            "instructions": "Rate the urgency of this ticket.",
            "criteria": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        },

        "needs_human": {
            "type": "noul",
            "instructions": "Does this ticket require human intervention?",
        },

        "refund_request": {
            "type": "noul",
            "instructions": "Is the customer asking for a refund?",
        },
    }

    result = router.predict(
        state,
        questions,
    )
    
    answers = result["answers"]
    decision = TicketDecision(
        department=answers["department"]["choice"],
        urgency=int(round(answers["urgency"]["score"])) + 1,  # Adding 1 because it's 0-indexed in Laya legend (or just use round)
        needs_human=answers["needs_human"]["noul"] > 0.5,
        refund_request=answers["refund_request"]["noul"] > 0.5,
    )
    return decision, result.get("usage", {})
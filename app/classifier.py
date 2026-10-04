import jev
from app.models import TicketDecision

@jev.fn
def classify_ticket(
    subject: str,
    message: str,
) -> TicketDecision:
    """
    Analyze the following customer support ticket.
    Subject:
    {{ subject }}
    Message:
    {{ message }}
    Determine:
    1. Which department should handle the ticket.
    2. How urgent the ticket is from 1 to 10.
    3. Whether a human should review it.
    4. Whether the customer is asking for a refund.
    """
    return classify_ticket.state()

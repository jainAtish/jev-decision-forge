from dotenv import load_dotenv
from typesafe_sdk import TypeSafeClient
from app.classifier import classify_ticket
from app.models import TicketDecision

load_dotenv()

def main():
    subject = "Charged twice"
    message = """
    I was charged twice for my subscription.
    Please refund the duplicate charge as soon as possible.
    """
    
    print("=== APPROACH 1: Using @jev.fn Decorator ===")
    # This approach is elegant and clean, but hides the raw token usage
    result_decorator = classify_ticket(
        subject=subject,
        message=message,
    )
    print(result_decorator)
    
    print("\n\n=== APPROACH 2: Using TypeSafeClient Manually ===")
    # This approach is verbose, but lets us inspect the raw API usage tokens
    client = TypeSafeClient()
    
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
    
    response = client.system_one(
        model="jev-latest",
        state=state,
        questions={
            "department": {
                "type": "choice",
                "instructions": "Which department should handle the ticket?",
                "criteria": {"billing": "", "technical": "", "sales": "", "account": ""}
            },
            "urgency": {
                "type": "score",
                "instructions": "How urgent the ticket is from 1 to 10?",
                "criteria": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
            },
            "needs_human": {
                "type": "noul",
                "instructions": "Whether a human should review it."
            },
            "refund_request": {
                "type": "noul",
                "instructions": "Whether the customer is asking for a refund."
            }
        }
    )
    
    # Manually map the result to our Pydantic model
    answers = response.answers
    decision_manual = TicketDecision(
        department=answers["department"].choice,
        urgency=int(round(answers["urgency"].score)),
        needs_human=answers["needs_human"].noul > 0.5,
        refund_request=answers["refund_request"].noul > 0.5,
    )
    
    print("--- DECISION ---")
    print(decision_manual)
    
    print("\n--- TOKEN USAGE ---")
    print(f"Input tokens:  {response.usage.input_tokens}")
    print(f"Output tokens: {response.usage.output_tokens}")


if __name__ == "__main__":
    main()
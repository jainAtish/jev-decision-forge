# Jev Decision Forge

This project demonstrates how to use the Jev Python SDK to create a strictly typed AI agent that categorizes customer support tickets. 

Instead of using a paid cloud API, this project is configured to run entirely locally for free using a `jev-local` Docker server.

## System Architecture & End-to-End Flow

```text
+-------------------------------------------------------------------------+
|                           1. TICKET INGESTION                           |
|   Incoming customer support ticket (Subject + Message body)             |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     2. TYPE-SAFE SCHEMA DECOMPOSITION                   |
|   @jev.fn inspects the Pydantic 'TicketDecision' model and converts it  |
|   into 4 discrete questions:                                            |
|     * department     --> Choice   ('billing' | 'technical' | ...)       |
|     * urgency        --> Score    (1 to 10 scale)                       |
|     * needs_human    --> Noul     (Probability 0.0 - 1.0)               |
|     * refund_request --> Noul     (Probability 0.0 - 1.0)               |
+------------------------------------+------------------------------------+
                                     |
                                     |  HTTP POST /system_one
                                     v
+-------------------------------------------------------------------------+
|                   3. LOCAL JEV INFERENCE ENGINE (jev-local)             |
|   - Runs locally on Docker at port 8000 (100% free, private)            |
|   - Extracts token logprobs directly over candidate vocabulary          |
|   - Generates NO verbose JSON text -> EXACTLY 4 OUTPUT TOKENS           |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  4. VALIDATED PYDANTIC OBJECT RECONSTRUCTION            |
|   TicketDecision(                                                       |
|       department="billing",                                             |
|       urgency=4,                                                        |
|       needs_human=False,                                                |
|       refund_request=True                                               |
|   )                                                                     |
+------------------------------------+------------------------------------+
                                     |
         +---------------------------+---------------------------+
         |                           |                           |
         v                           v                           v
+------------------+       +-------------------+       +-------------------+
| DEPARTMENT ROUTE |       |  SLA & ESCALATION |       |  REFUND AUTOMATION|
| Route to Billing |       | If urgency >= 8:  |       | If refund requested|
| Agent Queue      |       | PagerDuty / Slack |       | Trigger payment API|
+------------------+       +-------------------+       +-------------------+
```

### Detailed Flow Explanation

1. **Ticket Ingestion**: Raw ticket data (e.g., from an email, Zendesk webhook, or web form) arrives at the application.
2. **Schema & Question Decomposition**: The Jev decorator inspects the target Pydantic model (`TicketDecision`). Each field is mapped into a statistical decision question:
   - **Choice** questions select the most probable label (e.g. `billing`, `technical`, `sales`, `account`).
   - **Score** questions assign a calibrated numeric scale (1 to 10).
   - **Noul (Boolean)** questions compute direct Bernoulli probabilities ($0.0 \dots 1.0$) for yes/no conditions (`needs_human`, `refund_request`).
3. **Probability-Based Local Inference**: Instead of generating a long JSON string and consuming tens or hundreds of tokens, the local server calculates the probability of each decision token directly over the vocabulary.
4. **Strict Typing & Assembly**: The SDK validates responses against Pydantic validators, ensuring the returned object is always well-formed without regex or JSON parsing errors.
5. **Downstream Routing & Automation**: Your service executes immediate business actions based on the structured decision.

## Setup Instructions

### 1. Start the Local Jev Server
First, you need to run the `jev-local` server side-by-side with this project using Docker.

Open a terminal outside of this project folder and run:
```bash
git clone https://github.com/us/jev-local.git
cd jev-local
docker compose up -d
```
The server will now be running at `http://127.0.0.1:8000`.

### 2. Configure Environment Variables
Inside the `jev-decision-forge` project folder, ensure you have a `.env` file containing:

```env
TYPESAFE_API_KEY=dummy_key_for_local_testing
TYPESAFE_BASE_URL=http://127.0.0.1:8000
```
*(Note: A dummy API key is strictly required by the SDK to initialize, even when using a local server).*

### 3. Install Python Dependencies
Create a virtual environment and install the required packages:

```bash
python -m venv .venv

# On Windows:
.venv\Scripts\Activate.ps1
# On Mac/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Run the Classifier
Run the test script to see the ticket classifier in action! We run it as a module (`-m`) so Python treats the `app/` folder as a package.

```bash
python -m app.main
```

## How It Works

This project showcases two approaches in `app/main.py`:
1. **The `@jev.fn` approach**: The most elegant way to build AI functions natively in Python. The Jev decorator abstracts the API call and perfectly returns your typed `TicketDecision` model.
2. **The Manual `TypeSafeClient` approach**: Bypasses the decorator so you can access raw API metadata, such as the exact input and output tokens used by the local LLM.

Because Jev extracts token probabilities directly instead of streaming raw text, you will notice that classifying a complex ticket only takes exactly **4 output tokens**!

## Practical Use Cases

### 1. Multi-Queue Triage & Dispatch (Zendesk / Freshdesk / Slack)
Instead of relying on keyword rules or human triage leads, tickets are instantly categorized into departmental queues (`billing`, `technical`, `sales`, `account`) with 100% schema consistency.

### 2. Intelligent SLA & Escalation Engine
By extracting a normalized urgency score (`urgency: 1-10`), high-priority issues (e.g. `urgency >= 8`) automatically bypass tier-1 support to trigger on-call alerts via PagerDuty or an `#urgent-incidents` Slack channel.

### 3. Automated Refund & Self-Service Workflows
When `refund_request` is detected with high confidence along with `department == "billing"`, the router can directly trigger an automated Stripe/billing check to see if the customer qualifies for an instant refund before an agent touches the ticket.

### 4. Human-in-the-Loop Quality Assurance
The `needs_human` flag identifies tickets containing ambiguity, subtle nuance, or high-risk sentiment, ensuring sensitive interactions receive human scrutiny while standard repetitive requests flow to automated bots.

### 5. High-Throughput, Low-Cost AI Pipeline
Conventional LLM JSON generation (OpenAI/Anthropic tool calling) generates 50–150 output tokens of repetitive boilerplate JSON strings (`{"department": "billing", ...}`) per ticket. With Jev's direct probability scoring:
- **Cost**: Output token cost drops by over 95%.
- **Latency**: Single forward-pass evaluation means near-instant responses without streaming overhead.
- **Reliability**: Zero hallucinated formatting, missing commas, or JSON schema violations.


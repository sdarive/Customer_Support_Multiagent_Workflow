from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from agents.coordinator import TicketCoordinator, TicketClassifierAgent, KnowledgeRetrieverAgent, RouterAgent

app = FastAPI()

class TicketRequest(BaseModel):
    description: str

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
# In Vercel, this will come from environment variables
API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY")

# Initialize coordinator lazily to handle build-time environments where secrets might be missing
coordinator = None

def get_coordinator():
    global coordinator
    if coordinator is None:
        if not PROJECT_ID:
            raise HTTPException(status_code=500, detail="GCP_PROJECT_ID environment variable not set")
        coordinator = TicketCoordinator(PROJECT_ID, api_key=API_KEY)
    return coordinator

@app.get("/")
def read_root():
    return {"status": "Support Ticket Router API is running", "version": "1.0.0"}

@app.post("/api/process-ticket")
async def process_ticket_endpoint(ticket: TicketRequest):
    try:
        agent = get_coordinator()
        result = agent.process_ticket(ticket.description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

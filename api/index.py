from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
from google.oauth2 import service_account
from agents.coordinator import TicketCoordinator, TicketClassifierAgent, KnowledgeRetrieverAgent, RouterAgent

app = FastAPI()

class TicketRequest(BaseModel):
    description: str

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY")

# Vercel-specific: Parse Service Account Key from env var
GCP_SA_KEY = os.environ.get("GCP_SA_KEY")
credentials = None
if GCP_SA_KEY:
    try:
        service_account_info = json.loads(GCP_SA_KEY)
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
    except Exception as e:
        print(f"Error parsing GCP_SA_KEY: {e}")

# Initialize coordinator lazily
coordinator = None

def get_coordinator():
    global coordinator
    if coordinator is None:
        if not PROJECT_ID:
            raise HTTPException(status_code=500, detail="GCP_PROJECT_ID environment variable not set")
        
        # Pass credentials explicitly if available (requires updating agent classes to accept them)
        # For simplicity in this demo, we'll set the environment variable for ADC to work if possible,
        # or we rely on the agent code picking up the credentials if we pass them.
        
        # Strategy: Save the key to a temporary file for libraries that expect a file path
        if GCP_SA_KEY:
            with open("/tmp/gcp_key.json", "w") as f:
                f.write(GCP_SA_KEY)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/gcp_key.json"
            
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

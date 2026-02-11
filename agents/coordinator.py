import os
import sys
import json
import uuid
from datetime import datetime, timezone
from agents.classifier_agent import TicketClassifierAgent
from agents.knowledge_retriever_agent import KnowledgeRetrieverAgent
from agents.router_agent import RouterAgent

class TicketCoordinator:
    def __init__(self, project_id, api_key=None):
        self.project_id = project_id
        self.api_key = api_key
        self.classifier = TicketClassifierAgent(project_id, api_key=api_key)
        self.retriever = KnowledgeRetrieverAgent(project_id, api_key=api_key)
        self.router = RouterAgent(project_id)

    def process_ticket(self, ticket_description: str, ticket_id: str = None) -> dict:
        """
        Orchestrates the full ticket processing workflow.
        """
        if not ticket_id:
            ticket_id = str(uuid.uuid4())
            
        print(f"\n--- Processing Ticket: {ticket_id} ---")
        
        # 1. Classify
        print("Classifying ticket...")
        classification = self.classifier.classify(ticket_description, ticket_id)
        category = classification.get("category", "technical")
        priority = classification.get("priority", "medium")
        
        # 2. Retrieve solutions
        print(f"Retrieving solutions for {category}...")
        solutions = self.retriever.retrieve_solutions(ticket_description, category)
        
        # 3. Route
        print(f"Routing ticket with priority {priority}...")
        routing = self.router.route_ticket(category, priority)
        
        result = {
            "ticket_id": ticket_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticket_description": ticket_description,
            "classification": classification,
            "suggested_solutions": solutions,
            "routing": routing,
            "status": "processed"
        }
        
        return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python coordinator.py <project_id>")
        sys.exit(1)
        
    api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
    if not api_key and os.path.exists("../.env"):
        with open("../.env") as f:
            for line in f:
                if line.startswith("GOOGLE_GENAI_API_KEY="):
                    api_key = line.split("=")[1].strip()

    project_id = sys.argv[1]
    coordinator = TicketCoordinator(project_id, api_key=api_key)
    
    test_tickets = [
        "My credit card payment failed but I was still charged. Need refund immediately!",
        "The app crashes every time I try to export my data. Been happening for 3 days.",
        "I forgot my password and the reset link isn't working.",
        "Would love to see a dark mode feature in the mobile app!"
    ]
    
    for desc in test_tickets:
        res = coordinator.process_ticket(desc)
        print(json.dumps(res, indent=2))

import os
import sys
import json
import uuid
import time
from datetime import datetime, timezone
import google.generativeai as genai
from google.cloud import bigquery

class TicketClassifierAgent:
    def __init__(self, project_id, api_key=None, credentials=None):
        self.project_id = project_id
        if not api_key:
            # Try to get from environment or handle appropriately
            api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
        
        if api_key:
            genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel("gemini-2.0-flash")

        if credentials:
            self.bq_client = bigquery.Client(project=project_id, credentials=credentials)
        else:
            self.bq_client = bigquery.Client(project=project_id)
        self.dataset_id = "support_tickets_staging"
        self.agent_version = "v1.0.0"

    def classify(self, ticket_description: str, ticket_id: str = None) -> dict:
        """
        Classifies a support ticket into category and priority using Gemini.
        """
        if not ticket_id:
            ticket_id = str(uuid.uuid4())
            
        start_time = time.time()
        
        prompt = f"""
        Classify the following support ticket description into:
        - category: one of [billing, technical, account, feature_request]
        - priority: one of [low, medium, high, critical]
        - reasoning: brief explanation

        Rules:
        - billing: payment, charges, invoices, refunds
        - technical: bugs, errors, performance issues
        - account: login, password, settings, permissions
        - feature_request: new features, improvements

        Priority rules:
        - critical: service down, data loss, security issue
        - high: major feature broken, multiple users affected
        - medium: single user issue, workaround available
        - low: cosmetic, enhancement, question

        Return ONLY a JSON object.

        Ticket Description: {ticket_description}
        """

        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response text
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            token_count = response.usage_metadata.total_token_count
            cost_usd = (token_count * 0.0001 / 1000)
            
            self._log_telemetry(ticket_id, execution_time_ms, token_count, cost_usd)
            
            return result
        except Exception as e:
            print(f"Error in classification: {e}")
            return {
                "category": "technical",
                "priority": "medium",
                "reasoning": "Fallback due to error in classification."
            }

    def _log_telemetry(self, ticket_id, execution_time_ms, token_count, cost_usd):
        table_id = f"{self.project_id}.{self.dataset_id}.agent_telemetry"
        rows_to_insert = [
            {
                "run_id": str(uuid.uuid4()),
                "agent_name": "classifier",
                "ticket_id": ticket_id,
                "execution_time_ms": execution_time_ms,
                "token_count": token_count,
                "cost_usd": cost_usd,
                "agent_version": self.agent_version,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            print(f"Telemetry logging errors: {errors}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python classifier_agent.py <project_id>")
        sys.exit(1)
    
    # Load API key from .env if it exists
    api_key = None
    if os.path.exists("../.env"):
        with open("../.env") as f:
            for line in f:
                if line.startswith("GOOGLE_GENAI_API_KEY="):
                    api_key = line.split("=")[1].strip()
    
    project_id = sys.argv[1]
    agent = TicketClassifierAgent(project_id, api_key=api_key)
    test_description = "My payment was declined but I was still charged twice!"
    result = agent.classify(test_description)
    print(json.dumps(result, indent=2))

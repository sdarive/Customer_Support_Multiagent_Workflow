import os
import sys
import json
from google.cloud import bigquery

class RouterAgent:
    def __init__(self, project_id):
        self.project_id = project_id
        self.bq_client = bigquery.Client(project=project_id)
        self.dataset_id = "support_tickets_staging"

    def route_ticket(self, category: str, priority: str) -> dict:
        """
        Routes tickets to teams using BigQuery routing rules.
        """
        query = f"""
            SELECT assigned_team, sla_hours
            FROM `{self.project_id}.{self.dataset_id}.routing_rules`
            WHERE category = @category AND priority = @priority
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("category", "STRING", category),
                bigquery.ScalarQueryParameter("priority", "STRING", priority),
            ]
        )
        
        try:
            query_job = self.bq_client.query(query, job_config=job_config)
            results = list(query_job)
            
            if not results:
                return {
                    "assigned_team": "general_support",
                    "sla_hours": 24,
                    "routing_reason": "No specific rule found, falling back to general support."
                }
            
            row = results[0]
            return {
                "assigned_team": row.assigned_team,
                "sla_hours": row.sla_hours,
                "routing_reason": f"Matched routing rule for category '{category}' and priority '{priority}'."
            }
        except Exception as e:
            print(f"Error in routing: {e}")
            return {
                "assigned_team": "general_support",
                "sla_hours": 24,
                "routing_reason": "Error during routing lookup."
            }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python router_agent.py <project_id>")
        sys.exit(1)
        
    project_id = sys.argv[1]
    agent = RouterAgent(project_id)
    result = agent.route_ticket("billing", "critical")
    print(json.dumps(result, indent=2))

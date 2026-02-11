import sys
import uuid
import random
from datetime import datetime, timedelta
from google.cloud import bigquery

def generate_sample_data(project_id):
    client = bigquery.Client(project=project_id)
    dataset_id = "support_tickets_staging"

    categories = ["billing", "technical", "account", "feature_request"]
    priorities = ["low", "medium", "high", "critical"]
    teams = {
        "billing": "billing_team",
        "technical": "engineering_team",
        "account": "account_management",
        "feature_request": "product_team"
    }
    
    # 1. Generate Routing Rules
    print("Generating routing rules...")
    routing_rules = []
    sla_matrix = {
        "critical": 2,
        "high": 8,
        "medium": 24,
        "low": 48
    }
    
    for cat in categories:
        for prio in priorities:
            routing_rules.append({
                "category": cat,
                "priority": prio,
                "assigned_team": teams[cat],
                "sla_hours": sla_matrix[prio]
            })
    
    table_id = f"{project_id}.{dataset_id}.routing_rules"
    errors = client.insert_rows_json(table_id, routing_rules)
    if errors:
        print(f"Errors inserting routing rules: {errors}")
    else:
        print(f"Inserted {len(routing_rules)} routing rules.")

    # 2. Generate Knowledge Base
    print("Generating knowledge base...")
    kb_data = []
    problems = {
        "billing": ["payment declined", "double charged", "invoice issues", "subscription", "refunds"],
        "technical": ["login failure", "feature broken", "API timeout", "data sync", "performance"],
        "account": ["password reset", "email change", "account locked", "username update", "delete account"],
        "feature_request": ["export functionality", "mobile app", "integrations", "bulk operations", "reporting"]
    }
    
    for cat, issues in problems.items():
        for issue in issues:
            kb_data.append({
                "solution_id": str(uuid.uuid4()),
                "category": cat,
                "problem_description": f"User experiencing {issue}",
                "solution_text": f"Standard operating procedure for {issue}: verify details, check logs, and apply fix.",
                "success_rate": round(random.uniform(0.75, 0.98), 2),
                "embedding": None,
                "last_updated": datetime.utcnow().isoformat()
            })
            
    table_id = f"{project_id}.{dataset_id}.knowledge_base"
    errors = client.insert_rows_json(table_id, kb_data)
    if errors:
        print(f"Errors inserting KB data: {errors}")
    else:
        print(f"Inserted {len(kb_data)} knowledge base entries.")

    # 3. Generate Ticket History
    print("Generating ticket history...")
    tickets = []
    for _ in range(100):
        cat = random.choice(categories)
        prio = random.choice(priorities)
        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        
        resolved = random.choice([True, False])
        resolved_at = None
        resolution = None
        if resolved:
            resolved_at = (created_at + timedelta(hours=random.randint(1, 72))).isoformat()
            resolution = "Issue resolved by following standard SOP."

        tickets.append({
            "ticket_id": str(uuid.uuid4()),
            "category": cat,
            "priority": prio,
            "description": f"Sample {cat} issue: {random.choice(problems[cat])} reported by user.",
            "resolution": resolution,
            "assigned_team": teams[cat],
            "created_at": created_at.isoformat(),
            "resolved_at": resolved_at
        })
        
    table_id = f"{project_id}.{dataset_id}.ticket_history"
    errors = client.insert_rows_json(table_id, tickets)
    if errors:
        print(f"Errors inserting ticket history: {errors}")
    else:
        print(f"Inserted {len(tickets)} sample tickets.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_sample_data.py <project_id>")
        sys.exit(1)
    
    generate_sample_data(sys.argv[1])

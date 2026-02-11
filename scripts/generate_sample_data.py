import sys
import uuid
import random
from datetime import datetime, timedelta
from google.cloud import bigquery

from datetime import datetime, timedelta, timezone

def generate_sample_data(project_id, ticket_count=100):
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
    print("Checking routing rules...")
    # Skip if rules already exist to avoid duplicates
    rules_table = f"{project_id}.{dataset_id}.routing_rules"
    rules_query = client.query(f"SELECT COUNT(*) FROM `{rules_table}`")
    rules_check = list(rules_query)[0][0]
    
    if rules_check == 0:
        print("Generating routing rules...")
        routing_rules = []
        sla_matrix = {"critical": 2, "high": 8, "medium": 24, "low": 48}
        for cat in categories:
            for prio in priorities:
                routing_rules.append({
                    "category": cat,
                    "priority": prio,
                    "assigned_team": teams[cat],
                    "sla_hours": sla_matrix[prio]
                })
        client.insert_rows_json(rules_table, routing_rules)
        print(f"Inserted {len(routing_rules)} routing rules.")
    else:
        print("Routing rules already exist, skipping.")

    # 2. Generate Knowledge Base
    print("Checking knowledge base...")
    kb_table = f"{project_id}.{dataset_id}.knowledge_base"
    kb_query = client.query(f"SELECT COUNT(*) FROM `{kb_table}`")
    kb_check = list(kb_query)[0][0]
    
    if kb_check == 0:

        print("Generating knowledge base...")
        kb_data = []
        problems = {
            "billing": [
                "payment declined", "double charged", "invoice issues", "subscription renewal failure", 
                "refund request", "incorrect tax calculation", "promo code not working", "payment method expired"
            ],
            "technical": [
                "login failure", "feature broken", "API timeout", "data sync error", "performance slowdown",
                "app crash on startup", "security vulnerability report", "integration sync failed", "UI rendering issue"
            ],
            "account": [
                "password reset", "email change", "account locked", "username update", "delete account request",
                "2FA setup issue", "permissions mismatch", "profile details not saving", "invited user cant join"
            ],
            "feature_request": [
                "export functionality", "mobile app support", "dark mode", "bulk operations", "reporting dashboard",
                "webhook support", "custom themes", "offline mode", "AI suggestions", "multi-language support"
            ]
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
                    "last_updated": datetime.now(timezone.utc).isoformat()
                })
        client.insert_rows_json(kb_table, kb_data)
        print(f"Inserted {len(kb_data)} knowledge base entries.")
    else:
        print("Knowledge base already exist, skipping.")

    # 3. Generate Ticket History
    print(f"Generating {ticket_count} additional tickets...")
    problems_expanded = {
        "billing": ["payment declined", "double charged", "invoice issues", "subscription", "refunds", "tax issue", "billing cycle error"],
        "technical": ["login failure", "feature broken", "API timeout", "data sync", "performance", "memory leak", "UI bug", "server 500"],
        "account": ["password reset", "email change", "account locked", "username update", "delete account", "MFA error", "audit logs"],
        "feature_request": ["export tools", "mobile app", "integrations", "bulk operations", "reporting", "API access", "customization"]
    }
    
    tickets = []
    base_time = datetime.now(timezone.utc)
    for _ in range(ticket_count):
        cat = random.choice(categories)
        prio = random.choice(priorities)
        created_at = base_time - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        
        resolved = random.choice([True, False])
        resolved_at = None
        resolution = None
        if resolved:
            resolved_at = (created_at + timedelta(hours=random.randint(1, 72))).isoformat()
            resolution = f"Issue {random.choice(problems_expanded[cat])} resolved by support agent."

        tickets.append({
            "ticket_id": str(uuid.uuid4()),
            "category": cat,
            "priority": prio,
            "description": f"Customer reported: {random.choice(problems_expanded[cat])}. Requesting help with {cat} issue.",
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
        print(f"Successfully inserted {len(tickets)} sample tickets.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_sample_data.py <project_id> [count]")
        sys.exit(1)
    
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    generate_sample_data(sys.argv[1], count)


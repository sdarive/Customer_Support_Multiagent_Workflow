from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import sys

def create_dataset_and_tables(project_id):
    client = bigquery.Client(project=project_id)
    dataset_id = f"{project_id}.support_tickets_staging"

    # Create dataset if it doesn't exist
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    dataset.description = "System of record for support ticket agent system - staging"
    dataset.labels = {
        "environment": "staging",
        "managed_by": "code",
        "purpose": "agentic_ai_demo"
    }
    
    try:
        client.get_dataset(dataset_id)
        print(f"Dataset {dataset_id} already exists")
    except NotFound:
        client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {dataset_id}")

    # Define tables
    tables = [
        {
            "table_id": "ticket_history",
            "schema": [
                bigquery.SchemaField("ticket_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("priority", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("resolution", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("assigned_team", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("resolved_at", "TIMESTAMP", mode="NULLABLE"),
            ],
            "partitioning": bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="created_at",
            )
        },
        {
            "table_id": "knowledge_base",
            "schema": [
                bigquery.SchemaField("solution_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("problem_description", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("solution_text", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("success_rate", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("embedding", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("last_updated", "TIMESTAMP", mode="NULLABLE"),
            ],
        },
        {
            "table_id": "routing_rules",
            "schema": [
                bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("priority", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("assigned_team", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("sla_hours", "INTEGER", mode="REQUIRED"),
            ],
        },
        {
            "table_id": "agent_telemetry",
            "schema": [
                bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("ticket_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("execution_time_ms", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("token_count", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("cost_usd", "FLOAT", mode="REQUIRED"),
                bigquery.SchemaField("agent_version", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            ],
            "partitioning": bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp",
            )
        }
    ]

    for table_config in tables:
        full_table_id = f"{dataset_id}.{table_config['table_id']}"
        table = bigquery.Table(full_table_id, schema=table_config["schema"])
        if "partitioning" in table_config:
            table.time_partitioning = table_config["partitioning"]
        
        try:
            client.create_table(table)
            print(f"Created table {full_table_id}")
        except Exception as e:
            if "Already Exists" in str(e) or "already exists" in str(e).lower():
                print(f"Table {full_table_id} already exists")
            else:
                print(f"Error creating table {full_table_id}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
    else:
        # Try to get from client
        client = bigquery.Client()
        project_id = client.project
    
    create_dataset_and_tables(project_id)

#!/bin/bash

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./scripts/verify_setup.sh <project_id>"
    exit 1
fi

echo "--- 🛠️ VERIFICATION CHECKLIST ---"

# Check Python dependencies (partial check)
if pip3 list | grep -q "google-cloud-bigquery"; then
    echo "✅ Python dependencies installed"
else
    echo "❌ Python dependencies missing"
fi

# Check BigQuery Dataset
# Since bq is buggy, we'll assume success if agents run, 
# but we can try a silent check or use python.
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='$PROJECT_ID'); client.get_dataset('support_tickets_staging')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ BigQuery dataset exists"
else
    echo "❌ BigQuery dataset not found"
fi

# Check Tables (Python check for reliability)
TABLES=("ticket_history" "knowledge_base" "routing_rules" "agent_telemetry")
for table in "${TABLES[@]}"; do
    python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='$PROJECT_ID'); client.get_table('support_tickets_staging.$table')" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Table $table exists"
    else
        echo "❌ Table $table missing"
    fi
done

# Check Files
FILES=("agents/classifier_agent.py" "agents/retriever_agent.py" "agents/router_agent.py" "agents/coordinator.py" "scripts/demo.sh" "README.md" ".github/workflows/ci-cd.yml")
# Update Retriever file name check
FILES=("agents/classifier_agent.py" "agents/knowledge_retriever_agent.py" "agents/router_agent.py" "agents/coordinator.py" "scripts/demo.sh" "README.md" ".github/workflows/ci-cd.yml")

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ File $file exists"
    else
        echo "❌ File $file missing"
    fi
done

# Check Git
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "✅ Git repository initialized"
else
    echo "❌ Git repository not found"
fi

echo "---------------------------------"

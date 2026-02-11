#!/bin/bash

PROJECT_ID=$1
ENVIRONMENT=${2:-staging}

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./scripts/demo.sh <project_id> [environment]"
    exit 1
fi

export GCP_PROJECT_ID=$PROJECT_ID
# Export PYTHONPATH to include the current directory for agent imports
export PYTHONPATH=$PYTHONPATH:.

# Set the API key for the shell session
# In a real environment, this would be a secret
export GOOGLE_GENAI_API_KEY="AIzaSyAHrI05sDHBa1LVO0ETC0crc3A5GCvXEP4"

echo "=========================================================="
echo "   🚀 SUPPORT TICKET ROUTER - MULTI-AGENT DEMO 🚀"
echo "=========================================================="
echo "Project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"
echo "=========================================================="

echo -e "\n🔍 TEST 1: Classifier Agent"
python3 agents/classifier_agent.py "$PROJECT_ID"

echo -e "\n📚 TEST 2: Knowledge Retriever Agent"
python3 agents/knowledge_retriever_agent.py "$PROJECT_ID"

echo -e "\n🚦 TEST 3: Router Agent"
python3 agents/router_agent.py "$PROJECT_ID"

echo -e "\n🎭 TEST 4: Full Multi-Agent Workflow (Coordinator)"
python3 agents/coordinator.py "$PROJECT_ID"

echo -e "\n📊 AGENT TELEMETRY & COSTS (BigQuery)"
bq query --project_id="$PROJECT_ID" --use_legacy_sql=false \
  "SELECT 
     agent_name, 
     COUNT(*) as executions,
     SUM(token_count) as total_tokens,
     ROUND(SUM(cost_usd), 4) as total_cost_usd,
     ROUND(AVG(execution_time_ms), 2) as avg_latency_ms
   FROM support_tickets_staging.agent_telemetry
   WHERE DATE(timestamp) = CURRENT_DATE()
   GROUP BY agent_name
   ORDER BY total_cost_usd DESC"

echo -e "\n✅ Demo Complete!"

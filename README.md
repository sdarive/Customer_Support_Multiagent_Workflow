# 🤖 Support Ticket Router - Agentic AI CI/CD

This project demonstrates a production-grade multi-agent system for routing support tickets, built with **Gemini 2.0 Flash**, **BigQuery**, and **GitHub Actions**.

## 📊 Overview

The system uses a collaborative multi-agent architecture to process incoming support tickets:
1. **Classifier Agent**: Categorizes the ticket and assigns a priority.
2. **Knowledge Retriever Agent**: Finds relevant solutions from a historical knowledge base using RAG-lite patterns.
3. **Router Agent**: Assigns the ticket to the correct team based on SQL routing rules.
4. **Coordinator**: Orchestrates the workflow and ensures observability.

### Architecture

```text
      [ Support Ticket ]
              |
              V
    +-------------------+
    |   Coordinator     | <---- [ BigQuery Telemetry ]
    +-------------------+
      /        |        \
     V         V         V
+----------+ +----------+ +----------+
|Classifier| |Retriever | |  Router  |
+----------+ +----------+ +----------+
     |             |             |
     V             V             V
 [ Gemini ]   [BigQuery KB] [BigQuery Rules]
```

## 🚀 Quick Start

### Prerequisites
- GCP Project with BigQuery and Vertex AI APIs enabled.
- Python 3.11+
- `GOOGLE_GENAI_API_KEY` (for Gemini access)

### Installation
```bash
git clone https://github.com/sdarive/Customer_Support_Multiagent_Workflow.git
cd support-ticket-router
pip install -r requirements.txt
```

### Setup Infrastructure
```bash
python scripts/create_tables.py YOUR_PROJECT_ID
python scripts/generate_sample_data.py YOUR_PROJECT_ID
```

### Run Demo
```bash
./scripts/demo.sh YOUR_PROJECT_ID
```

## 🛠️ Testing
The project includes a comprehensive suite of integration tests.
```bash
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export GOOGLE_GENAI_API_KEY=YOUR_KEY
pytest tests/ -v --cov=agents
```

## 📈 Observability & Cost Tracking
Every agent execution logs telemetry to BigQuery, allowing for real-time cost analysis and performance monitoring.

Example Telemetry Schema:
- `execution_time_ms`: Latency tracking
- `token_count`: Usage tracking
- `cost_usd`: Real-time cost estimation
- `agent_version`: CI/CD version tracking

## 🤖 Featured Tech
- **Gemini 2.0 Flash**: High-speed, low-cost LLM for classification and ranking.
- **BigQuery**: System of record for knowledge, rules, and telemetry.
- **GitHub Actions**: Automated testing and multi-stage deployment.
- **Python**: Core implementation and orchestration.

## 🏗️ Future Enhancements
- [ ] Vector Embeddings for KB Retrieval (true RAG)
- [ ] Canary Deployments for New Agent Versions
- [ ] Slack/Email Integration for Notifications

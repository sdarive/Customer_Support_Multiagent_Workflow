# 🎤 Client Demo Guide - v1.0

This document provides a step-by-step walkthrough for demonstrating the **Support Ticket Router** to potential clients.

---

## 🎯 Demo Objectives
1. **Show Business Value**: Demonstrate how AI reduces operational overhead and human error.
2. **Prove Scalability**: Show BigQuery handling hundreds of tickets and solutions instantly.
3. **Demonstrate Governance**: Highlight the cost tracking (telemetry) and deterministic routing.
4. **Exhibit Speed**: Prove how fast a production-grade AI system can be deployed.

---

## 🗺️ Demonstration Flow

### 1. Introduction (The Problem)
> "In high-growth companies, support teams are often buried under a mountain of tickets. 30% of their day is spent on 'triage'—classifying tickets and identifying existing solutions. Our system automates this triage 100%."

### 2. The Data Core
Explain that this isn't just a "chatbot"; it’s integrated with a massive data warehouse.
- **System of Record**: BigQuery dataset `support_tickets_staging`.
- **Knowledge Assets**: 20+ expert-verified solutions for RAG.
- **SLA Engine**: Deterministic rules that ensure critical issues get instant eyes.

### 3. Live Execution
Run the demo script to show real-time processing of diverse scenarios (Billing, Technical, Feature Requests).
```bash
./scripts/demo.sh acn-demo-487122
```
**Talk Tracks during execution:**
- *Classifier*: "The AI understands context. If a user says 'urgent refund,' it knows that's Billing+Critical."
- *Retriever*: "Instead of searching manually, the agent pulls the exact SOP from our Knowledge Base."
- *Router*: "This is the 'guardrail.' We use SQL-based rules to ensure the ticket goes to the exact right team with the correct SLA."

### 4. Enterprise Observability
Highlight the **Telemetry Table** at the end of the script.
- **Cost Analysis**: "We track every cent. You can see the total cost for processing a ticket is less than a tenth of a penny."
- **Latency Monitoring**: "Average response time is ~2-3 seconds, replacing minutes of human work."

### 5. Deployment Readiness
Show the **GitHub Repository** and the `ci-cd.yml` file.
- **CI/CD**: "The system is fully automated. Every time we improve an agent, it goes through a rigorous testing pipeline before hitting production."

---

## 🛠️ Prerequisites for Presenter
- Ensure `GCP_PROJECT_ID` is set.
- Ensure `GOOGLE_GENAI_API_KEY` is exported.
- Verify 500+ tickets are in BigQuery (`scripts/verify_setup.sh`).

---

## 💎 Value Propositions to Close
- **ROI**: Triage automation typically reduces support costs by 40-60%.
- **Retention**: Faster SLAs lead to higher CSAT (Customer Satisfaction).
- **Control**: 100% audit trail of every AI decision in BigQuery.

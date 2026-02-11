# Agentic AI CI/CD Project - Antigravity Build Guide

**Building with Antigravity (Claude Code) - No Terraform Install Required**

This guide breaks down the project into Antigravity-friendly prompts you can give step-by-step. Antigravity already has your GCP credentials, so we'll skip Terraform and use `gcloud` commands + Python scripts directly.

---

## 📋 Prerequisites Check

**Before starting, verify in Antigravity:**

```
Check my GCP setup:
1. What's my active GCP project?
2. Do I have BigQuery API enabled?
3. Do I have Vertex AI API enabled?
4. What's my default region?
```

**If APIs aren't enabled, ask Antigravity:**
```
Enable these GCP APIs for my project:
- aiplatform.googleapis.com
- bigquery.googleapis.com
- cloudbuild.googleapis.com
```

---

## 🏗️ Build Phases

### **PHASE 1: Project Setup (15 minutes)**

#### Step 1.1: Create Project Structure

**Prompt for Antigravity:**
```
Create a new project directory called "support-ticket-router" with this structure:

support-ticket-router/
├── agents/
│   └── __init__.py
├── scripts/
├── tests/
│   └── __init__.py
├── .github/
│   └── workflows/
├── .gitignore
├── README.md
└── requirements.txt

Initialize it as a git repository with 'main' branch.

For .gitignore, include:
- Python cache files (__pycache__, *.pyc)
- Environment files (.env)
- IDE files (.vscode/, .idea/)
- Coverage reports (.coverage, htmlcov/)

For requirements.txt, include:
- google-cloud-aiplatform>=1.38.0
- google-cloud-bigquery>=3.14.0
- pytest>=7.4.0
- pytest-cov>=4.1.0
```

**Verify:** Check that all directories and files exist

---

#### Step 1.2: Install Dependencies

**Prompt for Antigravity:**
```
Install the Python dependencies from requirements.txt in the support-ticket-router directory.
Use pip install -r requirements.txt
```

**Verify:** Run `pip list | grep google-cloud` to confirm packages installed

---

### **PHASE 2: BigQuery Setup (30 minutes)**

#### Step 2.1: Create BigQuery Dataset

**Prompt for Antigravity:**
```
Using gcloud CLI or Python BigQuery client, create a BigQuery dataset called "support_tickets_staging" in my GCP project.

Set:
- Location: US
- Description: "System of record for support ticket agent system - staging"
- Labels: environment=staging, managed_by=code, purpose=agentic_ai_demo
```

**Verify:** Run `bq ls` to see the dataset

---

#### Step 2.2: Create BigQuery Tables

**Prompt for Antigravity:**
```
Create 4 BigQuery tables in the support_tickets_staging dataset:

1. TABLE: ticket_history
   - ticket_id (STRING, REQUIRED)
   - category (STRING, REQUIRED) 
   - priority (STRING, REQUIRED)
   - description (STRING, REQUIRED)
   - resolution (STRING, NULLABLE)
   - assigned_team (STRING, REQUIRED)
   - created_at (TIMESTAMP, REQUIRED)
   - resolved_at (TIMESTAMP, NULLABLE)
   - Partition by: created_at (DAY)

2. TABLE: knowledge_base
   - solution_id (STRING, REQUIRED)
   - category (STRING, REQUIRED)
   - problem_description (STRING, REQUIRED)
   - solution_text (STRING, REQUIRED)
   - success_rate (FLOAT, REQUIRED)
   - embedding (STRING, NULLABLE)
   - last_updated (TIMESTAMP, NULLABLE)

3. TABLE: routing_rules
   - category (STRING, REQUIRED)
   - priority (STRING, REQUIRED)
   - assigned_team (STRING, REQUIRED)
   - sla_hours (INTEGER, REQUIRED)

4. TABLE: agent_telemetry
   - run_id (STRING, REQUIRED)
   - agent_name (STRING, REQUIRED)
   - ticket_id (STRING, REQUIRED)
   - execution_time_ms (INTEGER, REQUIRED)
   - token_count (INTEGER, REQUIRED)
   - cost_usd (FLOAT, REQUIRED)
   - agent_version (STRING, REQUIRED)
   - timestamp (TIMESTAMP, REQUIRED)
   - Partition by: timestamp (DAY)

Use Python with google.cloud.bigquery library.
Create a script in scripts/create_tables.py that I can run.
```

**Verify:** 
```
bq ls support_tickets_staging
# Should show all 4 tables
```

---

#### Step 2.3: Generate Sample Data

**Prompt for Antigravity:**
```
Create a Python script at scripts/generate_sample_data.py that:

1. Generates 100 sample support tickets with:
   - Random categories: billing, technical, account, feature_request
   - Random priorities: low, medium, high, critical
   - Realistic descriptions
   - Some with resolutions, some without
   - Created dates over past 90 days

2. Generates 20 knowledge base entries (5 per category) with:
   - Sample problems for each category:
     * billing: payment declined, double charged, invoice issues, subscription, refunds
     * technical: login failure, feature broken, API timeout, data sync, performance
     * account: password reset, email change, account locked, username update, delete account
     * feature_request: export functionality, mobile app, integrations, bulk operations, reporting
   - Solutions for each problem
   - Success rates between 0.75-0.98

3. Generates routing rules for all category+priority combinations:
   - SLA matrix: critical=2hrs, high=8hrs, medium=24hrs, low=48hrs
   - Teams: billing_team, engineering_team, account_management, product_team

The script should:
- Take project_id as command line argument
- Insert data into BigQuery tables
- Print confirmation of rows inserted

Make it executable with: python scripts/generate_sample_data.py <project_id>
```

**Run the script:**
```
python scripts/generate_sample_data.py YOUR_PROJECT_ID
```

**Verify:**
```
bq query --project_id=YOUR_PROJECT_ID \
  'SELECT COUNT(*) as count FROM support_tickets_staging.ticket_history'

bq query --project_id=YOUR_PROJECT_ID \
  'SELECT COUNT(*) as count FROM support_tickets_staging.knowledge_base'

bq query --project_id=YOUR_PROJECT_ID \
  'SELECT COUNT(*) as count FROM support_tickets_staging.routing_rules'
```

---

### **PHASE 3: Agent Implementation (90 minutes)**

#### Step 3.1: Classifier Agent

**Prompt for Antigravity:**
```
Create agents/classifier_agent.py:

This agent classifies support tickets using Vertex AI Gemini Flash.

Requirements:
- Class: TicketClassifierAgent
- Model: gemini-1.5-flash-002
- Method: classify(ticket_description: str, ticket_id: str) -> dict

The classify method should:
1. Create a prompt that asks Gemini to classify the ticket into:
   - category: one of [billing, technical, account, feature_request]
   - priority: one of [low, medium, high, critical]
   - reasoning: brief explanation

2. Use these classification rules:
   - billing: payment, charges, invoices, refunds
   - technical: bugs, errors, performance issues
   - account: login, password, settings, permissions
   - feature_request: new features, improvements

3. Priority rules:
   - critical: service down, data loss, security issue
   - high: major feature broken, multiple users affected
   - medium: single user issue, workaround available
   - low: cosmetic, enhancement, question

4. Return JSON with category, priority, reasoning

5. Log telemetry to BigQuery agent_telemetry table:
   - run_id (UUID)
   - agent_name = "classifier"
   - ticket_id
   - execution_time_ms
   - token_count (from response.usage_metadata)
   - cost_usd (token_count * 0.0001 / 1000)  # Gemini Flash pricing
   - agent_version = "v1.0.0"
   - timestamp

6. Handle errors gracefully with fallback to default values

Include:
- Docstrings
- Type hints
- Error handling
- Cost calculation
- A main block that tests with: "My payment was declined but I was still charged twice!"

Project ID and environment should be constructor parameters.
```

**Test it:**
```
cd agents
python classifier_agent.py YOUR_PROJECT_ID
```

**Verify:** Should print classification result with category, priority, reasoning

---

#### Step 3.2: Knowledge Retriever Agent

**Prompt for Antigravity:**
```
Create agents/knowledge_retriever_agent.py:

This agent retrieves relevant solutions from BigQuery knowledge base using RAG pattern.

Requirements:
- Class: KnowledgeRetrieverAgent
- Model: gemini-1.5-flash-002 (for ranking)
- Method: retrieve_solutions(ticket_description: str, category: str, top_k: int = 3) -> list

The retrieve_solutions method should:
1. Query BigQuery knowledge_base table filtered by category
2. Get candidate solutions ordered by success_rate DESC
3. Use Gemini to rank candidates by relevance to ticket_description
4. Return top_k most relevant solutions

Return format: list of dicts with:
- solution_id
- problem_description
- solution_text
- success_rate

BigQuery query should:
```sql
SELECT solution_id, problem_description, solution_text, success_rate
FROM support_tickets_staging.knowledge_base
WHERE category = @category
ORDER BY success_rate DESC
LIMIT {top_k * 3}
```

Then use Gemini to rank by relevance and return top_k.

Include:
- Docstrings
- Error handling
- A main block that tests with: "My payment was declined", category "billing"

Use parameterized queries for SQL injection protection.
```

**Test it:**
```
python knowledge_retriever_agent.py YOUR_PROJECT_ID
```

**Verify:** Should print 2-3 relevant billing solutions

---

#### Step 3.3: Router Agent

**Prompt for Antigravity:**
```
Create agents/router_agent.py:

This agent routes tickets to teams using BigQuery routing rules.

Requirements:
- Class: RouterAgent
- Method: route_ticket(category: str, priority: str) -> dict

The route_ticket method should:
1. Query BigQuery routing_rules table
2. Find matching rule for category + priority
3. Return assigned_team and sla_hours

BigQuery query:
```sql
SELECT assigned_team, sla_hours
FROM support_tickets_staging.routing_rules
WHERE category = @category AND priority = @priority
LIMIT 1
```

Return format: dict with:
- assigned_team
- sla_hours
- routing_reason (explanation)

Include fallback if no rule found:
- assigned_team = "general_support"
- sla_hours = 24

Include:
- Docstrings
- Error handling
- A main block that tests with: category="billing", priority="critical"
```

**Test it:**
```
python router_agent.py YOUR_PROJECT_ID
```

**Verify:** Should print team assignment and SLA hours

---

#### Step 3.4: Coordinator (Orchestrator)

**Prompt for Antigravity:**
```
Create agents/coordinator.py:

This orchestrates all 3 agents into a complete workflow.

Requirements:
- Class: TicketCoordinator
- Method: process_ticket(ticket_description: str, ticket_id: str = None) -> dict

The process_ticket method should:
1. Generate ticket_id if not provided (UUID)
2. Call classifier.classify() → get category, priority
3. Call retriever.retrieve_solutions() → get relevant solutions
4. Call router.route_ticket() → get team assignment
5. Combine all results into final dict

Return format:
{
  "ticket_id": "...",
  "timestamp": "...",
  "ticket_description": "...",
  "classification": {...},
  "suggested_solutions": [...],
  "routing": {...},
  "status": "processed"
}

The main block should test with 4 sample tickets:
1. "My credit card payment failed but I was still charged. Need refund immediately!"
2. "The app crashes every time I try to export my data. Been happening for 3 days."
3. "I forgot my password and the reset link isn't working."
4. "Would love to see a dark mode feature in the mobile app!"

Print results for each ticket with clear formatting.
```

**Test it:**
```
python coordinator.py YOUR_PROJECT_ID
```

**Verify:** Should process all 4 tickets and show complete results

---

### **PHASE 4: Testing (60 minutes)**

#### Step 4.1: Create Test Suite

**Prompt for Antigravity:**
```
Create tests/test_agents.py with pytest tests:

Test classes needed:

1. TestTicketClassifier:
   - test_classifier_returns_valid_structure
     * Verify result has category, priority, reasoning
     * Verify values are in valid lists
   
   - test_classifier_billing_detection
     * Test with: "My credit card was charged twice"
     * Assert category == "billing"
   
   - test_classifier_critical_priority_detection
     * Test with: "URGENT: System is down, all users affected!"
     * Assert priority in ["high", "critical"]

2. TestKnowledgeRetriever:
   - test_retriever_returns_list
     * Verify return type is list
     * Verify length <= top_k
   
   - test_retriever_solution_structure
     * Verify each solution has required fields
     * Verify success_rate is float between 0-1

3. TestRouter:
   - test_router_returns_required_fields
     * Verify assigned_team and sla_hours present
   
   - test_router_critical_priority_short_sla
     * Verify critical < high < medium < low for SLA

4. TestCoordinator:
   - test_coordinator_full_workflow
     * Test complete ticket processing
     * Verify all result fields present

Use pytest fixtures for agent instances.
Set PROJECT_ID from environment variable with default "test-project-12345".

Important: These are integration tests that require real GCP access.
Mark them with @pytest.mark.integration decorator.
```

**Run tests:**
```
# Set your project ID
export GCP_PROJECT_ID=YOUR_PROJECT_ID

# Run tests
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/test_agents.py -v --cov=agents --cov-report=term
```

**Verify:** All tests should pass (green)

---

### **PHASE 5: CI/CD Pipeline (30 minutes)**

#### Step 5.1: GitHub Actions Workflow

**Prompt for Antigravity:**
```
Create .github/workflows/ci-cd.yml:

This workflow should run on:
- Pull requests to main
- Pushes to main

Jobs needed:

1. test-agents:
   - runs-on: ubuntu-latest
   - Setup Python 3.11
   - Install requirements.txt
   - Install pytest, pytest-cov
   - Run: pytest tests/ -v --cov=agents --cov-report=xml
   - Upload coverage to codecov (optional)

2. deploy-staging:
   - needs: test-agents
   - only on: push to main
   - environment: staging
   - Steps:
     * Checkout code
     * Echo "Would deploy to staging"
     * Echo "In production: gcloud commands or Terraform"

3. deploy-production:
   - needs: deploy-staging
   - only on: push to main
   - environment: production (requires manual approval)
   - Steps:
     * Checkout code
     * Echo "Would deploy to production"

Use environment variable: PROJECT_ID from secrets.GCP_PROJECT_ID

Keep it simple - focus on test automation and deployment structure.
```

---

#### Step 5.2: Create Demo Script

**Prompt for Antigravity:**
```
Create scripts/demo.sh bash script:

This script should:
1. Take PROJECT_ID as first argument (required)
2. Take ENVIRONMENT as second argument (default: staging)
3. Print formatted header with project info
4. Run each agent test individually with clear labels:
   - Test 1: Classifier
   - Test 2: Knowledge Retriever
   - Test 3: Router
   - Test 4: Full Workflow (coordinator)
5. Print telemetry query at the end to show agent costs

Make it executable: chmod +x scripts/demo.sh

Use nice formatting with emoji and box-drawing characters for visual appeal.
```

**Test it:**
```
chmod +x scripts/demo.sh
./scripts/demo.sh YOUR_PROJECT_ID staging
```

**Verify:** Should run all 4 tests and show results

---

### **PHASE 6: Documentation (30 minutes)**

#### Step 6.1: Comprehensive README

**Prompt for Antigravity:**
```
Create a comprehensive README.md for the project:

Sections needed:
1. Title and Purpose
   - What this demonstrates (CI/CD for agentic AI)
   - Why it matters (POC to production gap)

2. Architecture
   - ASCII diagram of multi-agent flow
   - Explanation of each agent
   - BigQuery as system of record

3. Quick Start
   - Prerequisites (GCP project, APIs enabled)
   - Clone repo
   - Install dependencies
   - Set PROJECT_ID
   - Run demo

4. What This Demonstrates
   - CI/CD for non-deterministic AI
   - Testing strategies
   - BigQuery data architecture
   - Cost tracking and observability
   - Production patterns

5. Project Structure
   - agents/ - Agent implementations
   - scripts/ - Utilities and demo
   - tests/ - Test suite
   - .github/ - CI/CD pipeline

6. Running Tests
   - pytest commands
   - Coverage reports

7. Observability
   - BigQuery telemetry queries
   - Cost analysis examples

8. Key Learnings
   - POC vs Production gap
   - Testing non-deterministic systems
   - BigQuery as system of record
   - Cost tracking from day 1

9. Future Enhancements
   - Vector embeddings
   - Canary deployments
   - Real-time monitoring
   - Multi-region

10. Resources
    - Links to Vertex AI, BigQuery, GitHub Actions docs

Keep it professional but conversational.
Use code blocks, emoji for visual appeal.
Make architecture diagram with ASCII art.
```

---

### **PHASE 7: Git & GitHub (15 minutes)**

#### Step 7.1: Initialize Git and Create Repo

**Prompt for Antigravity:**
```
Help me set up Git and GitHub for this project:

1. Initialize git repository (if not already done)
2. Create .gitignore with Python, environment, IDE files
3. Make initial commit with all files
4. Create meaningful commit messages for each phase:
   - "Initial project structure"
   - "Add BigQuery infrastructure and sample data"
   - "Implement multi-agent system (classifier, retriever, router)"
   - "Add test suite with pytest"
   - "Add CI/CD pipeline and demo script"
   - "Complete documentation"

5. Guide me to create GitHub repository (I'll do this manually):
   - Repository name: support-ticket-router
   - Public repository
   - No template

6. After I create the repo, show me the commands to push:
   ```
   git remote add origin <my-repo-url>
   git branch -M main
   git push -u origin main
   ```
```

**Manual steps:**
1. Go to GitHub.com
2. Click "New Repository"
3. Name: support-ticket-router
4. Public
5. Don't initialize with README (we have one)
6. Create repository
7. Copy the repository URL
8. Run the push commands Antigravity provided

---

#### Step 7.2: Set GitHub Secrets

**Prompt for Antigravity:**
```
Guide me to set up GitHub secrets for CI/CD:

I need to add these secrets in GitHub repository settings:
- GCP_PROJECT_ID = <my project ID>

Show me:
1. Where to find repository settings (Settings → Secrets and variables → Actions)
2. Click "New repository secret"
3. Name: GCP_PROJECT_ID
4. Value: <my actual project ID>
5. Click "Add secret"

Note: For real production, I'd also need GCP service account credentials,
but for this demo, the secret is just for the workflow to reference.
```

---

### **PHASE 8: Final Testing (15 minutes)**

#### Step 8.1: End-to-End Verification

**Prompt for Antigravity:**
```
Create a verification checklist script at scripts/verify_setup.sh:

This script should check:
1. ✅ BigQuery dataset exists
2. ✅ All 4 tables exist
3. ✅ Sample data loaded (count rows in each table)
4. ✅ Python dependencies installed
5. ✅ All agent files exist
6. ✅ Tests can run
7. ✅ Demo script is executable
8. ✅ Git repository initialized
9. ✅ README exists

Print status for each check with emoji (✅ or ❌).

Usage: ./scripts/verify_setup.sh <project_id>
```

**Run verification:**
```
chmod +x scripts/verify_setup.sh
./scripts/verify_setup.sh YOUR_PROJECT_ID
```

**Verify:** All checks should pass ✅

---

#### Step 8.2: Run Complete Demo

**Prompt for Antigravity:**
```
Now run the complete demo:

./scripts/demo.sh YOUR_PROJECT_ID staging
```

**Expected output:**
- All 4 agent tests run successfully
- Tickets are classified, solutions retrieved, teams assigned
- Telemetry query shows agent costs

---

#### Step 8.3: Check BigQuery Telemetry

**Run this query to see agent execution data:**
```
bq query --project_id=YOUR_PROJECT_ID \
  'SELECT 
     agent_name, 
     COUNT(*) as executions,
     SUM(token_count) as total_tokens,
     ROUND(SUM(cost_usd), 4) as total_cost_usd,
     ROUND(AVG(execution_time_ms), 2) as avg_latency_ms
   FROM support_tickets_staging.agent_telemetry
   WHERE DATE(timestamp) = CURRENT_DATE()
   GROUP BY agent_name
   ORDER BY total_cost_usd DESC'
```

**Verify:** Should see classifier agent with token counts and costs

---

## 📊 Project Checklist

Before showing to Maudrit:

- [ ] BigQuery dataset and tables created
- [ ] Sample data loaded (100 tickets, 20 solutions, routing rules)
- [ ] All 3 agents implemented and tested individually
- [ ] Coordinator orchestrates full workflow
- [ ] Test suite passes (pytest)
- [ ] Demo script runs end-to-end
- [ ] GitHub repository created and pushed
- [ ] GitHub Actions workflow visible
- [ ] README is comprehensive and professional
- [ ] Agent telemetry visible in BigQuery
- [ ] All commits have meaningful messages

---

## 🎤 Presentation to Maudrit

### If You Get a Follow-Up Call

**Opening (30 seconds):**
"After our conversation, I realized my CI/CD experience for agentic AI was more prototype-focused than production-grade. So I spent the weekend building a reference implementation using Antigravity to better understand the patterns you asked about."

**Show GitHub Repo (2 minutes):**
- Share screen → GitHub repository
- Scroll through README (architecture diagram)
- Show agents/ directory structure
- Show .github/workflows/ci-cd.yml
- Show tests/ directory

**Live Demo (3 minutes):**
```bash
# Clone the repo (to show it's real)
git clone <your-repo-url>
cd support-ticket-router

# Run the demo
./scripts/demo.sh YOUR_PROJECT_ID staging

# Show telemetry
bq query --project_id=YOUR_PROJECT_ID \
  'SELECT agent_name, COUNT(*) as calls, SUM(cost_usd) as cost
   FROM support_tickets_staging.agent_telemetry
   WHERE DATE(timestamp) = CURRENT_DATE()
   GROUP BY agent_name'
```

**Key Points (1 minute):**
1. "BigQuery as system of record - data staging, routing rules, telemetry"
2. "Testing non-deterministic systems - structure validation, quality checks"
3. "Multi-agent orchestration - classifier, retriever, router pattern"
4. "Cost tracking from day 1 - every agent execution logged"
5. "This is the POC to production journey I'd bring to clients"

**Close (30 seconds):**
"Building this taught me more in one weekend than weeks of reading docs. I'm a builder - this is how I learn. This is the hands-on, product-minded approach I'd bring to your team."

---

## 🔧 Troubleshooting

### Common Issues

**Issue: "Permission denied" errors**
```
# Check GCP authentication
gcloud auth list
gcloud auth application-default login
```

**Issue: BigQuery API not enabled**
```
gcloud services enable bigquery.googleapis.com
```

**Issue: Vertex AI API not enabled**
```
gcloud services enable aiplatform.googleapis.com
```

**Issue: Agent tests fail with "Model not found"**
```
# Verify Vertex AI is available in your region
gcloud config set ai/region us-central1
```

**Issue: Pytest not finding modules**
```
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue: Sample data script fails**
```
# Check table exists
bq ls support_tickets_staging

# Check data
bq query 'SELECT COUNT(*) FROM support_tickets_staging.ticket_history'
```

---

## ⏱️ Time Breakdown

**Saturday (4-5 hours):**
- Phase 1: Project Setup (15 min)
- Phase 2: BigQuery Setup (30 min)
- Phase 3: Agent Implementation (90 min)
- Phase 4: Testing (60 min)
- Break/troubleshooting buffer (30 min)

**Sunday (3-4 hours):**
- Phase 5: CI/CD Pipeline (30 min)
- Phase 6: Documentation (30 min)
- Phase 7: Git & GitHub (15 min)
- Phase 8: Final Testing (15 min)
- Polish and prepare presentation (60 min)

**Total: 7-9 hours** (very doable in a weekend with Antigravity's help)

---

## ✅ Success Criteria

You'll know you're done when:

1. ✅ GitHub repo is live and accessible
2. ✅ README has clear architecture and instructions
3. ✅ Demo script runs without errors
4. ✅ All tests pass with pytest
5. ✅ BigQuery has telemetry data showing agent costs
6. ✅ You can explain each component in 30 seconds
7. ✅ Repository looks professional (not "test commit" × 50)

---

## 🎯 What This Shows Maudrit

**Technical Depth:**
✅ Hands-on GCP (BigQuery, Vertex AI)
✅ Multi-agent orchestration
✅ Production CI/CD patterns
✅ Testing non-deterministic systems

**Product Thinking:**
✅ BigQuery as system of record (not just data storage)
✅ Cost tracking built in from day 1
✅ Observability and telemetry
✅ Staged deployment strategy

**Builder Mentality:**
✅ Didn't just read about it - built it
✅ Working code, not slides
✅ Real GitHub repo, not local files
✅ Professional documentation

**Gap Addressed:**
✅ You acknowledged partial CI/CD experience
✅ You built something to learn deeply
✅ You can now speak from experience
✅ Shows learning agility and ownership

---

**You've got this! Start with Phase 1 and work through sequentially. Antigravity will handle the heavy lifting - you just guide it step by step.**

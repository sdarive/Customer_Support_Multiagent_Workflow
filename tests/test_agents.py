import os
import pytest
import json
from agents.classifier_agent import TicketClassifierAgent
from agents.knowledge_retriever_agent import KnowledgeRetrieverAgent
from agents.router_agent import RouterAgent
from agents.coordinator import TicketCoordinator

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "acn-demo-487122")
API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY")

@pytest.fixture
def classifier():
    return TicketClassifierAgent(PROJECT_ID, API_KEY)

@pytest.fixture
def retriever():
    return KnowledgeRetrieverAgent(PROJECT_ID, API_KEY)

@pytest.fixture
def router():
    return RouterAgent(PROJECT_ID)

@pytest.fixture
def coordinator():
    return TicketCoordinator(PROJECT_ID, API_KEY)

@pytest.mark.integration
def test_classifier_returns_valid_structure(classifier):
    result = classifier.classify("My payment was declined")
    assert "category" in result
    assert "priority" in result
    assert "reasoning" in result
    assert result["category"] in ["billing", "technical", "account", "feature_request"]
    assert result["priority"] in ["low", "medium", "high", "critical"]

@pytest.mark.integration
def test_classifier_billing_detection(classifier):
    result = classifier.classify("My credit card was charged twice")
    assert result["category"] == "billing"

@pytest.mark.integration
def test_classifier_critical_priority_detection(classifier):
    result = classifier.classify("URGENT: System is down, all users affected!")
    assert result["priority"] in ["high", "critical"]

@pytest.mark.integration
def test_retriever_returns_list(retriever):
    result = retriever.retrieve_solutions("My payment was declined", "billing", top_k=2)
    assert isinstance(result, list)
    assert len(result) <= 2

@pytest.mark.integration
def test_retriever_solution_structure(retriever):
    result = retriever.retrieve_solutions("My payment was declined", "billing", top_k=1)
    if result:
        sol = result[0]
        assert "solution_id" in sol
        assert "problem_description" in sol
        assert "solution_text" in sol
        assert "success_rate" in sol
        assert isinstance(sol["success_rate"], float)

@pytest.mark.integration
def test_router_returns_required_fields(router):
    result = router.route_ticket("billing", "critical")
    assert "assigned_team" in result
    assert "sla_hours" in result
    assert result["assigned_team"] == "billing_team"

@pytest.mark.integration
def test_router_priority_sla(router):
    critical = router.route_ticket("billing", "critical")["sla_hours"]
    high = router.route_ticket("billing", "high")["sla_hours"]
    medium = router.route_ticket("billing", "medium")["sla_hours"]
    low = router.route_ticket("billing", "low")["sla_hours"]
    assert critical < high < medium < low

@pytest.mark.integration
def test_coordinator_full_workflow(coordinator):
    result = coordinator.process_ticket("I need to reset my password")
    assert result["status"] == "processed"
    assert "classification" in result
    assert "suggested_solutions" in result
    assert "routing" in result
    assert result["classification"]["category"] == "account"

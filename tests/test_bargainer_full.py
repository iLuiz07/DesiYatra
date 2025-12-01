"""
Full Integration Tests for Bargainer Agent (Logic & Flow)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from agents.adk_agents.bargainer.negotiation_brain import NegotiationBrain
from agents.adk_agents.shared.custom_planners import NegotiationPlanner
from agents.adk_agents.bargainer.agent import negotiation_loop
from google.genai import types

# --- 1. Test Negotiation Brain (Prompting Logic) ---

@patch('google.generativeai.GenerativeModel')
def test_negotiation_brain_prompt_construction(mock_genai_model):
    """Test that the brain constructs the prompt with correct context variables."""
    mock_model_instance = mock_genai_model.return_value
    mock_response = MagicMock()
    mock_response.text = "Haan ji, teen hazar mein final."
    mock_model_instance.generate_content.return_value = mock_response
    
    brain = NegotiationBrain()
    
    history = [{"role": "user", "content": "Kitna loge?"}]
    trip_context = {
        "destination": "Goa",
        "market_rate": 1500,
        "budget_max": 1800,
        "vendor_type": "Taxi",
        "requirements": "Airport drop"
    }
    
    response = brain.generate_negotiation_response(history, trip_context, "Bhaiya rate batao")
    
    assert response == "Haan ji, teen hazar mein final."
    
    # Verify prompt contains key variables
    call_args = mock_model_instance.generate_content.call_args
    prompt_sent = call_args[0][0]
    
    assert "Goa" in prompt_sent
    assert "1500" in prompt_sent
    assert "1800" in prompt_sent
    assert "Taxi" in prompt_sent
    assert "Airport drop" in prompt_sent
    assert "Bhaiya rate batao" in prompt_sent

# --- 2. Test Negotiation Planner (Decision Logic) ---

@pytest.mark.asyncio
async def test_planner_ask_price_if_missing():
    """Planner should ask for price if not yet quoted."""
    planner = NegotiationPlanner()
    context = {
        "current_quote": None,
        "market_rate": 2000,
        "budget_max": 2500
    }
    plan = await planner.plan(context)
    assert plan["action"] == "ask_price"

@pytest.mark.asyncio
async def test_planner_accept_deal():
    """Planner should accept if quote is within budget."""
    planner = NegotiationPlanner()
    context = {
        "current_quote": 2400,
        "market_rate": 2000,
        "budget_max": 2500
    }
    plan = await planner.plan(context)
    assert plan["action"] == "accept"
    assert "2400" in plan["message"]

@pytest.mark.asyncio
async def test_planner_counter_offer_stubborn():
    """Planner should make small counter-offer for stubborn vendors."""
    planner = NegotiationPlanner()
    context = {
        "current_quote": 3000,
        "market_rate": 2000,
        "budget_max": 2500,
        "vendor_profile": {"negotiation_style": "stubborn"}
    }
    plan = await planner.plan(context)
    
    assert plan["action"] == "counter"
    # 3000 * 0.95 = 2850
    assert plan["offer"] == 2850.0 

@pytest.mark.asyncio
async def test_planner_end_call_max_rounds():
    """Planner should end call if max rounds reached."""
    planner = NegotiationPlanner(max_rounds=5)
    context = {
        "current_quote": 3000,
        "budget_max": 2500,
        "round": 5
    }
    plan = await planner.plan(context)
    assert plan["action"] == "end_call"

# --- 3. Test Negotiation Loop Agent (Integration) ---

@pytest.mark.asyncio
@patch('agents.adk_agents.bargainer.atomic_tools.send_message')
@patch('agents.adk_agents.bargainer.atomic_tools._get_call_state')
async def test_negotiation_loop_flow(mock_get_state, mock_send_message):
    """
    Test the loop agent flow. 
    Note: Testing ADK loop execution requires mocking the runner or engine, 
    which is complex. Here we verify the agent configuration and tool chain.
    """
    # Verify sub-agent
    turn_agent = negotiation_loop.sub_agents[0]
    assert turn_agent.name == "NegotiationTurnAgent"
    
    # Verify tools are attached
    tool_names = [t.__name__ for t in turn_agent.tools]
    assert "send_message" in tool_names
    assert "accept_deal" in tool_names
    
    # Verify loop config
    assert negotiation_loop.max_iterations == 6

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

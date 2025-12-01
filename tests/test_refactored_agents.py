"""
Tests for the refactored ADK agents (Parallel-Sequential Scout and Loop-Based Bargainer)
"""
import pytest
from unittest.mock import patch, MagicMock
from agents.adk_agents.scout.agent import scout_agent, parallel_search_agent
from agents.adk_agents.bargainer.agent import bargainer_agent, negotiation_loop, negotiation_turn_agent
from agents.adk_agents.bargainer import atomic_tools

def test_scout_agent_structure():
    """Test that ScoutAgent has the correct Parallel-Sequential structure."""
    assert scout_agent.name == "ScoutAgent"
    assert len(scout_agent.sub_agents) == 3  # Parallel, Processing, MarketRate
    
    # First sub-agent should be ParallelSearchAgent
    assert scout_agent.sub_agents[0].name == "ParallelSearchAgent"
    assert len(scout_agent.sub_agents[0].sub_agents) == 4  # 4 search agents
    
    # Second sub-agent should be ProcessingAgent
    assert scout_agent.sub_agents[1].name == "ProcessingAgent"
    
    # Third sub-agent should be MarketRateAgent
    assert scout_agent.sub_agents[2].name == "MarketRateAgent"

def test_parallel_search_agent_structure():
    """Test that ParallelSearchAgent has all 4 search sub-agents."""
    search_agent_names = [agent.name for agent in parallel_search_agent.sub_agents]
    
    assert "GoogleSearchAgent" in search_agent_names
    assert "GoogleMapsAgent" in search_agent_names
    assert "JustDialAgent" in search_agent_names
    assert "IndiaMartAgent" in search_agent_names

def test_bargainer_agent_structure():
    """Test that BargainerAgent has the correct Loop-Based structure."""
    assert bargainer_agent.name == "BargainerAgent"
    assert len(bargainer_agent.sub_agents) == 2
    
    # First sub-agent should be VendorIteratorAgent
    assert bargainer_agent.sub_agents[0].name == "VendorIteratorAgent"
    
    # Second sub-agent should be NegotiationLoop
    assert bargainer_agent.sub_agents[1].name == "NegotiationLoop"

def test_negotiation_loop_structure():
    """Test that NegotiationLoop has correct configuration."""
    assert negotiation_loop.name == "NegotiationLoop"
    assert negotiation_loop.max_iterations == 6
    assert len(negotiation_loop.sub_agents) == 1
    assert negotiation_loop.sub_agents[0].name == "NegotiationTurnAgent"

def test_negotiation_turn_agent_tools():
    """Test that NegotiationTurnAgent has all atomic tools."""
    tool_names = [tool.__name__ for tool in negotiation_turn_agent.tools]
    
    assert "send_message" in tool_names
    assert "accept_deal" in tool_names
    assert "end_call" in tool_names

# --- Atomic Tool Tests with Mocks ---

@patch('agents.adk_agents.bargainer.atomic_tools._save_call_state')
@patch('agents.adk_agents.bargainer.atomic_tools._push_to_redis_queue_sync')
@patch('agents.adk_agents.bargainer.atomic_tools.generate_and_store_sarvam_audio')
@patch('agents.adk_agents.bargainer.atomic_tools._get_twilio_client')
def test_atomic_tool_initiate_call(mock_twilio, mock_sarvam, mock_redis, mock_save_state):
    """Test the initiate_call atomic tool with mocks."""
    mock_sarvam.return_value = "http://mock/audio.wav"
    
    mock_call = MagicMock()
    mock_call.sid = "CA12345"
    mock_twilio.return_value.calls.create.return_value = mock_call
    
    vendor = {
        "name": "Test Vendor",
        "phone": "+919876543210",
        "category": "taxi"
    }
    trip_context = {
        "market_rate": 2800.0,
        "budget_max": 3000.0,
        "party_size": 4
    }
    
    result = atomic_tools.initiate_call(vendor, trip_context, use_real_twilio=True)
    
    assert "call_id" in result
    assert result["vendor_name"] == "Test Vendor"
    assert result["status"] == "CALL_INITIATED"
    assert result["twilio_call_sid"] == "CA12345"
    
    mock_save_state.assert_called()
    mock_sarvam.assert_called()

@patch('agents.adk_agents.bargainer.atomic_tools._get_call_state')
@patch('agents.adk_agents.bargainer.atomic_tools._save_call_state')
def test_atomic_tool_send_message(mock_save_state, mock_get_state):
    """Test the send_message atomic tool."""
    # Mock state return
    call_id = "call_+919876543210"
    mock_state = {
        "round": 0,
        "history": [],
        "current_quote": None
    }
    mock_get_state.return_value = mock_state
    
    # Send a message
    result = atomic_tools.send_message(call_id, "Thoda kam kar dijiye", offer=2800.0)
    
    assert result["call_id"] == call_id
    assert "vendor_response" in result
    assert "current_quote" in result
    assert result["round"] == 1
    assert mock_save_state.called

@patch('agents.adk_agents.bargainer.atomic_tools._get_call_state')
@patch('agents.adk_agents.bargainer.atomic_tools._delete_call_state')
def test_atomic_tool_accept_deal(mock_delete_state, mock_get_state):
    """Test the accept_deal atomic tool."""
    call_id = "call_+919876543210"
    mock_state = {
        "vendor": {"name": "Test Vendor", "phone": "+91...", "category": "taxi"},
        "round": 3
    }
    mock_get_state.return_value = mock_state
    
    # Accept the deal
    result = atomic_tools.accept_deal(call_id, 2900.0)
    
    assert result["vendor_name"] == "Test Vendor"
    assert result["negotiated_price"] == 2900.0
    assert result["status"] == "DEAL_SUCCESS"
    assert mock_delete_state.called

@patch('agents.adk_agents.bargainer.atomic_tools._get_call_state')
@patch('agents.adk_agents.bargainer.atomic_tools._delete_call_state')
def test_atomic_tool_end_call(mock_delete_state, mock_get_state):
    """Test the end_call atomic tool with escalation."""
    call_id = "call_+919876543210"
    mock_state = {
        "vendor": {"name": "Test Vendor", "phone": "+91...", "category": "taxi"},
    }
    mock_get_state.return_value = mock_state
    
    # Mock tool context
    mock_context = MagicMock()
    mock_context.actions = MagicMock()
    
    # End the call
    result = atomic_tools.end_call(mock_context, call_id, "max_rounds_reached")
    
    assert result["status"] == "CALL_ENDED"
    assert result["reason"] == "max_rounds_reached"
    assert mock_context.actions.escalate == True
    assert mock_delete_state.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
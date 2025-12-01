"""
Tests for the Custom Negotiation Planner logic.
"""
import pytest
from agents.adk_agents.shared.custom_planners import NegotiationPlanner

@pytest.mark.asyncio
async def test_initial_inquiry():
    """Test planner asks for price when no quote exists."""
    planner = NegotiationPlanner()
    context = {
        "current_quote": None,
        "market_rate": 2500,
        "budget_max": 3000,
        "round": 0
    }
    
    plan = await planner.plan(context)
    
    assert plan["action"] == "ask_price"
    assert "रेट क्या लगेगा" in plan["message"]

@pytest.mark.asyncio
async def test_accept_deal_within_budget():
    """Test planner accepts deal when quote is within budget."""
    planner = NegotiationPlanner()
    context = {
        "current_quote": 2800,
        "market_rate": 2500,
        "budget_max": 3000,
        "round": 1
    }
    
    plan = await planner.plan(context)
    
    assert plan["action"] == "accept"
    assert "डील पक्की" in plan["message"]

@pytest.mark.asyncio
async def test_counter_offer_stubborn_vendor():
    """Test small counter-offer for stubborn vendor."""
    planner = NegotiationPlanner()
    context = {
        "current_quote": 4000,
        "market_rate": 2500,
        "budget_max": 3000,
        "round": 1,
        "vendor_profile": {"negotiation_style": "stubborn"}
    }
    
    plan = await planner.plan(context)
    
    assert plan["action"] == "counter"
    # Stubborn: 5% reduction = 4000 * 0.95 = 3800
    assert plan["offer"] == 3800
    assert "stubborn" in plan["reasoning"].lower()

@pytest.mark.asyncio
async def test_counter_offer_flexible_vendor():
    """Test larger counter-offer for flexible vendor."""
    planner = NegotiationPlanner()
    context = {
        "current_quote": 4000,
        "market_rate": 2500,
        "budget_max": 3000,
        "round": 1,
        "vendor_profile": {"negotiation_style": "flexible"}
    }
    
    plan = await planner.plan(context)
    
    assert plan["action"] == "counter"
    # Flexible: 10% reduction = 4000 * 0.90 = 3600
    assert plan["offer"] == 3600
    assert "flexible" in plan["reasoning"].lower()

@pytest.mark.asyncio
async def test_end_call_max_rounds():
    """Test planner ends call when max rounds reached."""
    planner = NegotiationPlanner(max_rounds=6)
    context = {
        "current_quote": 3500,
        "market_rate": 2500,
        "budget_max": 3000,
        "round": 6
    }
    
    plan = await planner.plan(context)
    
    assert plan["action"] == "end_call"
    assert "Max rounds" in plan["reasoning"]

@pytest.mark.asyncio
async def test_floor_price_protection():
    """Test counter-offer never goes below market rate."""
    planner = NegotiationPlanner()
    context = {
        "current_quote": 2600,
        "market_rate": 2500,
        "budget_max": 2400, # Budget lower than market
        "round": 1,
        "vendor_profile": {"negotiation_style": "flexible"}
    }
    
    # Flexible 10% off 2600 is 2340, which is < market_rate (2500)
    # Planner should floor it at 2500
    
    plan = await planner.plan(context)
    
    assert plan["action"] == "counter"
    assert plan["offer"] == 2500

# ------------------------------------------------------------------------------
# --- File: tests/test_waterfall.py ---
# ------------------------------------------------------------------------------

import pytest
import numpy as np
from parameters import (
    FundParameters, Scenario, ProRata, ReservePolicy, StageAllocEntry,
    DistParams, StageParams, DynamicFollowOn
)
from waterfall import apply_fund_structure # Make sure to import the function to test

@pytest.fixture
def waterfall_params():
    """
    Creates a simplified but valid FundParameters object specifically for testing
    the waterfall distribution logic.
    """
    # Many parameters are not used by apply_fund_structure, so we can use placeholders
    return FundParameters(
        scenario=Scenario(name="test", date="2025-01-01", notes=""),
        schema_version=1.0,
        num_investments=0,
        investment_period_months=60,
        max_deals_per_year=0,
        max_company_lifespan_months=120,
        # --- FIX IS HERE ---
        pro_rata=ProRata(participation_rate=1.0),
        deal_hit_rate={},
        committed_capital=50_000_000,
        fund_lifespan_months=120,
        fund_lifespan_extensions_months=0,
        mgmt_fee_commitment_period_rate=0.02,
        mgmt_fee_post_commitment_period_rate=0.0175,
        mgmt_fee_extension_period_rate=0.01,
        carried_interest_rate=0.20,
        preferred_return_rate=0.08,
        gp_catch_up_proportion=1.0, # 100% catch-up
        waterfall_style="European",
        reinvestment_rate=0.0,
        reserve_policy=ReservePolicy(min_reserve_ratio=0.0),
        dynamic_stage_allocation=[],
        dynamic_follow_on=DynamicFollowOn(enabled=False, failure_rate_threshold=0.5, strategy_review_month=36, super_pro_rata_rate=1.5),
        initial_post_money_valuation_dist={},
        initial_ownership_targets={},
        stage_stepup_pre_money={},
        option_pool_expansion={},
        stage_parameters={}
    )

def test_waterfall_no_profit(waterfall_params):
    """
    Tests that if gross proceeds are zero, LP net cash flows are just negative fees.
    """
    gross_cash_flows = [(-1_000_000, 12, -1), (-875_000, 24, -1)] # Only fees
    rng = np.random.default_rng(seed=123)
    
    net_lp_flows, _, _ = apply_fund_structure(gross_cash_flows, waterfall_params, rng)
    
    total_net_lp = sum(amount for amount, _ in net_lp_flows)
    
    assert total_net_lp == -1_875_000, "With no profit, LPs should only lose their fee payments"

def test_waterfall_with_pref_only(waterfall_params):
    """
    Tests that LPs get their capital back plus preferred return before the GP gets carry.
    """
    # Total investment = 10M. Pref @ 8% for ~5 years = ~4M. Proceeds = 15M.
    gross_cash_flows = [
        (-10_000_000, 6, 1), 
        (-1_000_000, 12, -1),
        (15_000_000, 60, 1)
    ]
    rng = np.random.default_rng(seed=123)
    
    net_lp_flows, _, _ = apply_fund_structure(gross_cash_flows, waterfall_params, rng)
    
    total_lp_contributions = abs(sum(amt for amt, _, id in gross_cash_flows if id != -1 and amt < 0))
    total_lp_distributions = sum(amt for amt, _ in net_lp_flows if amt > 0)
    
    assert total_lp_distributions > total_lp_contributions
    assert total_lp_distributions < 15_000_000, "GP should not receive carry yet"

def test_waterfall_with_full_carry_and_catch_up(waterfall_params):
    """
    Tests that the GP receives the correct carried interest after all distributions.
    """
    # Total investment = 10M. Proceeds = 100M.
    gross_cash_flows = [
        (-10_000_000, 6, 1),
        (-1_000_000, 12, -1),
        (100_000_000, 72, 1)
    ]
    rng = np.random.default_rng(seed=123)
    
    net_lp_flows, _, _ = apply_fund_structure(gross_cash_flows, waterfall_params, rng)
    
    total_profit = 100_000_000 - 10_000_000
    expected_carry = total_profit * waterfall_params.carried_interest_rate
    
    lp_contributed = 10_000_000
    lp_distributed = sum(amt for amt, _ in net_lp_flows if amt > 0)
    
    # Calculate LP profit
    lp_profit = lp_distributed - lp_contributed
    
    # Calculate GP share
    gp_share = total_profit - lp_profit
    
    # The GP's share should be very close to the expected carried interest
    assert np.isclose(gp_share, expected_carry), "GP share should equal the fund's carried interest percentage of total profit"
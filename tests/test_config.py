# ------------------------------------------------------------------------------
# --- File: tests/test_config.py ---
# ------------------------------------------------------------------------------
# Replace the entire contents of this file with the following:

import pytest
import numpy as np
from parameters import (
    FundParameters, Scenario, ProRata, ReservePolicy, StageAllocEntry,
    DistParams, StageParams, DynamicFollowOn
)
# We need to import the engine to test it
from engine import _run_one_event_driven_simulation

@pytest.fixture
def base_test_params():
    """Creates a minimal but valid set of FundParameters for testing."""
    return FundParameters(
        scenario=None,
        schema_version=1.0,
        num_investments=2,
        investment_period_months=24,
        max_deals_per_year=2,
        max_company_lifespan_months=60,
        pro_rata=ProRata(participation_rate=1.0),
        ownership_cap=0.29,
        committed_capital=100_000_000,
        fund_lifespan_months=60,
        fund_lifespan_extensions_months=0,
        prob_of_1yr_extension=0.0,
        mgmt_fee_commitment_period_rate=0.02,
        mgmt_fee_post_commitment_period_rate=0.0175,
        mgmt_fee_extension_period_rate=0.01,
        carried_interest_rate=0.20,
        preferred_return_rate=0.08,
        gp_catch_up_proportion=1.0,
        waterfall_style="European",
        reserve_policy=ReservePolicy(enabled=True, min_reserve_ratio=0.3),
        follow_on_round_size_pct=0.2,
        dynamic_stage_allocation=[StageAllocEntry(year=1, allocation={"TestStage": 1.0})],
        dynamic_follow_on=DynamicFollowOn(enabled=False, failure_rate_threshold=0.5, strategy_review_month=36, super_pro_rata_rate=1.5),
        initial_post_money_valuation_dist={
            "TestStage": DistParams(type='lognormal', mu_log=np.log(10_000_000), sigma_log=0.1)
        },
        initial_ownership_targets={"TestStage": 0.15},
        option_pool_expansion={},
        stage_parameters={
            "TestStage": StageParams(
                prob_to_exit=0.0,
                prob_to_fail=0.0,
                prob_to_NextStage=1.0,
                time_in_stage_months=12,
                stage_stepup_pre_money_dist=DistParams(type='lognormal', mu_log=np.log(20_000_000), sigma_log=0.2),
                exit_valuation_dist=DistParams(type='lognormal', mu_log=np.log(50_000_000), sigma_log=0.2)
            ),
             "NextStage": StageParams(
                prob_to_exit=1.0,
                prob_to_fail=0.0,
                time_in_stage_months=12,
                stage_stepup_pre_money_dist=None,
                exit_valuation_dist=DistParams(type='lognormal', mu_log=np.log(50_000_000), sigma_log=0.2)
            )
        }
    )

def test_no_capital_constraint(base_test_params):
    """
    Tests that the simulation is NOT capital constrained when committed capital is very large.
    """
    rng = np.random.default_rng(seed=123)
    base_test_params.committed_capital = 1_000_000_000
    
    # --- FIX: Unpack the two return values from the simulation ---
    result, _ = _run_one_event_driven_simulation(base_test_params, rng)
    
    assert result is not None
    assert result.capital_constrained is False, "Should not be capital constrained with a large fund size"

def test_capital_constraint_is_applied(base_test_params):
    """
    Tests that the simulation IS capital constrained when committed capital is very small.
    """
    rng = np.random.default_rng(seed=123)
    # Set capital low enough that it can make the first investment but not the follow-on
    base_test_params.committed_capital = 2_000_000 

    # --- FIX: Unpack the two return values from the simulation ---
    result, _ = _run_one_event_driven_simulation(base_test_params, rng)

    print(f"Type of result: {type(result)}")

    assert result is not None
    assert result.capital_constrained is True, "Should be capital constrained with a small fund size"

# ------------------------------------------------------------------------------
# --- File: tests/test_waterfall.py ---
# ------------------------------------------------------------------------------
# This section remains unchanged.

import pytest
from parameters import FundParameters, Scenario, ProRata, ReservePolicy, DynamicFollowOn

@pytest.fixture
def waterfall_params():
    """
    Creates a simplified but valid FundParameters object specifically for testing
    the waterfall distribution logic.
    """
    return FundParameters(
        scenario=Scenario(name="test", date="2025-01-01", notes=""),
        schema_version=1.0,
        num_investments=0,
        investment_period_months=60,
        max_deals_per_year=0,
        max_company_lifespan_months=120,
        pro_rata=ProRata(participation_rate=1.0),
        ownership_cap=0.29, # Assuming a default cap for tests
        committed_capital=50_000_000,
        fund_lifespan_months=120,
        fund_lifespan_extensions_months=0,
        prob_of_1yr_extension=0.0,
        mgmt_fee_commitment_period_rate=0.02,
        mgmt_fee_post_commitment_period_rate=0.0175,
        mgmt_fee_extension_period_rate=0.01,
        carried_interest_rate=0.20,
        preferred_return_rate=0.08,
        gp_catch_up_proportion=1.0,
        waterfall_style="European",
        reserve_policy=ReservePolicy(enabled=False, min_reserve_ratio=0.0),
        follow_on_round_size_pct=0.2,
        dynamic_stage_allocation=[],
        dynamic_follow_on=DynamicFollowOn(enabled=False, failure_rate_threshold=0.5, strategy_review_month=36, super_pro_rata_rate=1.5),
        initial_post_money_valuation_dist={},
        initial_ownership_targets={},
        option_pool_expansion={},
        stage_parameters={}
    )

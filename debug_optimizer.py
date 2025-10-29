import numpy as np
import math
from typing import Dict, List
from parameters import FundParameters
from parameters_loader import load_parameters_from_yaml

def debug_parameters(params: FundParameters):
    """Debug function to check if all required attributes exist"""
    print("=== DEBUGGING FUND PARAMETERS ===")
    
    # Check core attributes
    print(f"Committed capital: {getattr(params, 'committed_capital', 'MISSING')}")
    print(f"Target investable %: {getattr(params, 'target_investable_capital_pct', 'MISSING')}")
    print(f"Num investments: {getattr(params, 'num_investments', 'MISSING')}")
    
    # Check stages
    print(f"Stages order: {getattr(params, 'stages_order', 'MISSING')}")
    print(f"Stages dict keys: {list(getattr(params, 'stages', {}).keys())}")
    
    # Check follow-on strategy
    follow_on = getattr(params, 'follow_on_strategy', None)
    if follow_on:
        print(f"Follow-on strategy type: {getattr(follow_on, 'type', 'MISSING')}")
    else:
        print("Follow-on strategy: MISSING")
    
    # Check dynamic allocation
    dynamic_alloc = getattr(params, 'dynamic_stage_allocation', None)
    if dynamic_alloc:
        print(f"Dynamic allocation entries: {len(dynamic_alloc)}")
        for i, entry in enumerate(dynamic_alloc):
            print(f"  Entry {i}: {getattr(entry, 'allocation', 'MISSING')}")
    else:
        print("Dynamic stage allocation: MISSING")
    
    # Check initial ownership targets
    ownership_targets = getattr(params, 'initial_ownership_targets', None)
    if ownership_targets:
        print(f"Initial ownership targets: {ownership_targets}")
    else:
        print("Initial ownership targets: MISSING")

def test_calculation(params: FundParameters):
    """Test the calculation step by step"""
    print("\n=== TESTING CALCULATION ===")
    
    try:
        # Test 1: Check stages
        stages = params.stages_order
        print(f"Stages order: {stages}")
        
        # Test 2: Check first stage
        if stages:
            first_stage = stages[0]
            print(f"First stage: {first_stage}")
            
            stage_params = params.stages[first_stage]
            print(f"Stage params: {stage_params}")
            
            # Test 3: Check distribution
            dist = stage_params.post_money_valuation_dist
            print(f"Distribution mu_log: {dist.mu_log}")
            
            # Test 4: Calculate expected valuation
            expected_val = math.exp(dist.mu_log)
            print(f"Expected valuation: {expected_val}")
            
            # Test 5: Check ownership target
            ownership_target = params.initial_ownership_targets[first_stage]
            print(f"Ownership target: {ownership_target}")
            
            # Test 6: Calculate initial investment
            initial_investment = expected_val * ownership_target
            print(f"Initial investment: {initial_investment}")
            
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        # Try to load parameters
        params = load_parameters_from_yaml("config.yaml")
        debug_parameters(params)
        test_calculation(params)
    except Exception as e:
        print(f"Error loading parameters: {e}")
        import traceback
        traceback.print_exc()

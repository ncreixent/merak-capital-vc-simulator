# ==============================================================================
# --- VC Fund Model: Parameter Loader & Validator (v2.0) ---
# ==============================================================================

import yaml
import numpy as np
import json
import jsonschema
from scipy.stats import norm
from typing import Any, Dict

# Import all required dataclasses from parameters.py
from parameters import (
    FundParameters, Scenario, CapitalCallSettings, StageAllocEntry,
    DistParams, StageParams, FollowOnStrategy, Waterfall
)

def calculate_lognormal_params(dist_data: Dict) -> Dict:
    """Calculates lognormal mu and sigma from median/percentiles if needed."""
    dist_type = dist_data.get('type', 'lognormal')
    
    if dist_type == 'lognormal_from_percentiles':
        p50 = dist_data['p50_valuation']
        if 'p90_valuation' in dist_data:
            p_val, z_score = dist_data['p90_valuation'], norm.ppf(0.90)
        elif 'p95_valuation' in dist_data:
            p_val, z_score = dist_data['p95_valuation'], norm.ppf(0.95)
        else:
            raise ValueError("Lognormal dist from percentiles requires 'p90_valuation' or 'p95_valuation'.")

        mu_log = np.log(p50)
        sigma_log = (np.log(p_val) - mu_log) / z_score
        return {'mu_log': mu_log, 'sigma_log': sigma_log, 'type': 'lognormal'}

    elif dist_type == 'lognormal':
        if dist_data['median_valuation'] <= 0:
            raise ValueError("median_valuation for lognormal distribution must be positive.")
        mu_log = np.log(dist_data['median_valuation'])
        sigma_log = dist_data['sigma_log']
        return {'mu_log': mu_log, 'sigma_log': sigma_log, 'type': 'lognormal'}
        
    raise ValueError(f"Unsupported distribution type: {dist_type}")


def load_parameters(config_path: str, schema_path: str = 'config.schema.json') -> FundParameters:
    """Loads, validates (schema and logic), and processes parameters from a YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # --- 1. Schema Validation ---
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        jsonschema.validate(instance=config, schema=schema)
        print("✅ Configuration file successfully validated against schema.")
    except FileNotFoundError:
        print(f"⚠️ WARNING: Schema file not found at {schema_path}. Skipping validation.")
    except Exception as e:
        print(f"❌ ERROR: Configuration file failed validation against {schema_path}.")
        raise e

    # --- 2. Logical Validation ---
    stages_order = config['stages_order']
    stages_config = config['stages']
    final_stage_name = stages_order[-1]

    for stage_name in stages_order:
        if stage_name not in stages_config:
            raise ValueError(f"Logical Error: Stage '{stage_name}' from 'stages_order' is not defined in 'stages'.")
        
        stage_data = stages_config[stage_name]
        is_final_stage = (stage_name == final_stage_name)
        
        # For final stages without prob_to_next_stage, don't include it in the sum
        prob_to_next = stage_data.get('prob_to_next_stage', 0) if not is_final_stage else 0
        prob_to_exit = stage_data.get('prob_to_exit', 0)
        prob_to_fail = stage_data.get('prob_to_fail', 0)
        
        probs_to_sum = [prob_to_next, prob_to_exit, prob_to_fail]
        if not np.isclose(sum(probs_to_sum), 1.0):
            raise ValueError(f"Logical Error: Probabilities for stage '{stage_name}' do not sum to 1. Got: {sum(probs_to_sum)}")
            
        if is_final_stage and 'prob_to_next_stage' in stage_data and stage_data['prob_to_next_stage'] > 0:
            raise ValueError(f"Logical Error: Final stage '{stage_name}' must not have positive 'prob_to_next_stage'.")

    print("✅ Configuration file successfully passed logical validation.")

    # --- 3. Parse Data into Dataclasses ---

    # CORRECTED: Create the new, simpler FollowOnStrategy object
    fos_config = config['follow_on_strategy']
    follow_on_strategy = FollowOnStrategy(
        type=fos_config.get('type'),
        passive_participation_rate=fos_config.get('passive_participation_rate', 1.0) # Default to 1.0
    )

    # Process Stage-Specific Parameters
    processed_stages = {}
    for stage_name, params in stages_config.items():
        processed_stages[stage_name] = StageParams(
            prob_to_next_stage=params.get('prob_to_next_stage'),
            prob_to_exit=params['prob_to_exit'], 
            prob_to_fail=params['prob_to_fail'],
            time_in_stage_months=params['time_in_stage_months'],
            post_money_valuation_dist=DistParams(**calculate_lognormal_params(params['post_money_valuation_dist'])),
            multiple_to_next_dist=DistParams(**calculate_lognormal_params(params['multiple_to_next_dist'])),
            target_dilution_pct=params.get('target_dilution_pct'),
            min_valuation = params.get('min_valuation'),
            max_valuation = params.get('max_valuation')
        )

    # Process Dynamic Stage Allocation
    dynamic_stage_allocation = [
        StageAllocEntry(**entry) for entry in config['dynamic_stage_allocation']
    ]

    # CORRECTED: Create the final FundParameters object with all new and corrected fields
    params = FundParameters(
        scenario=Scenario(**config['scenario']),
        schema_version=config['schema_version'],
        num_investments=config['num_investments'],
        investment_period_months=config['investment_period_months'],
        max_deals_per_year=config['max_deals_per_year'],
        max_company_lifespan_months=config['max_company_lifespan_months'],
        prob_of_extensions=config['prob_of_extensions'],
        committed_capital=config['committed_capital'],
        fund_lifespan_months=config['fund_lifespan_months'],
        fund_lifespan_extensions_months=config['fund_lifespan_extensions_months'],
        ownership_cap=config['ownership_cap'],
        target_investable_capital_pct=config['target_investable_capital_pct'],
        mgmt_fee_commitment_period_rate=config['mgmt_fee_commitment_period_rate'],
        mgmt_fee_post_commitment_period_rate=config['mgmt_fee_post_commitment_period_rate'],
        mgmt_fee_extension_period_rate=config.get('mgmt_fee_extension_period_rate', 0.01),
        waterfall=Waterfall(**config['waterfall']),
        allow_recycling=config['allow_recycling'],
        recycling_limit_pct_of_commitment=config['recycling_limit_pct_of_commitment'],
        capital_calls=CapitalCallSettings(**config['capital_calls']),
        follow_on_strategy=follow_on_strategy,
        dynamic_stage_allocation=dynamic_stage_allocation,
        initial_ownership_targets=config['initial_ownership_targets'],
        stages_order=stages_order,
        stages=processed_stages
    )

    print("✅ FundParameters object created successfully.")
    return params


# Create a globally accessible instance of the parameters
# This will be imported by your notebook
if __name__ == "__main__":
    fund_params = load_parameters('config.yaml')
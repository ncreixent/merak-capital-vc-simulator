# sensitivity.py (Corrected with proper median scaling)
import numpy as np
import copy
import logging
from typing import Dict, Any

import engine as vcm
from parameters import FundParameters
from utils import get_nested_value, set_nested_value

def run_sensitivity_suite(
    base_params_obj: FundParameters, 
    sensitivity_suite_config: Dict,
    sims_per_run: int
) -> Dict:
    """
    Reads a configuration dictionary and runs a full sensitivity analysis suite.
    """
    all_sensitivity_results = {}
    
    base_params_for_run = copy.deepcopy(base_params_obj)

    for test_name, config in sensitivity_suite_config.items():
        logging.info(f"--- Running Sensitivity Test: {test_name} ---")
        
        test_results_for_this_param = []
        variation_values = config['variation']
        path_list = config['path']

        for test_value in variation_values:
            logging.info(f"  Testing value/factor: {test_value:.4f}")
            params_copy = copy.deepcopy(base_params_for_run)
            
            param_type = config.get('type', 'absolute')
            original_param_value = get_nested_value(vars(params_copy), path_list)

            # --- FIX: New logic to correctly handle scaling of mu_log ---
            if param_type == 'multiplicative' and 'mu_log' in path_list:
                # To multiply the median by a factor, we must ADD ln(factor) to mu_log.
                # new_mu = ln(median) + ln(factor) = old_mu + ln(factor)
                new_value = original_param_value + np.log(test_value)
            elif param_type == 'multiplicative':
                new_value = original_param_value * test_value
            else: # 'absolute'
                new_value = test_value
            
            set_nested_value(vars(params_copy), path_list, new_value)

            # Handle adjustments (e.g., for failure probabilities)
            if config.get('adjustment_path'):
                 # This part is for absolute changes, not multiplicative ones
                 adjustment_amount = get_nested_value(vars(base_params_obj), path_list) - test_value
                 original_adjustment_val = get_nested_value(vars(params_copy), config['adjustment_path'])
                 set_nested_value(vars(params_copy), config['adjustment_path'], original_adjustment_val + adjustment_amount)

            all_results = vcm.run_monte_carlo(
                params=params_copy, 
                num_simulations=sims_per_run, 
                seed=42
            )
            
            if all_results:
                net_irrs = [res.net_irr for res in all_results if res.net_irr is not None]
                test_results_for_this_param.append(np.median(net_irrs) if net_irrs else np.nan)
            else:
                test_results_for_this_param.append(np.nan)

        all_sensitivity_results[test_name] = (variation_values, test_results_for_this_param)
        
    return all_sensitivity_results
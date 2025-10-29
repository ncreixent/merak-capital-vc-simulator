# precompute_default.py

import pickle
import yaml
from pathlib import Path
from parameters_loader import load_parameters
from engine import run_monte_carlo

def precompute_default_scenario():
    """Precompute default scenario results and save to disk"""
    
    print("Loading default configuration...")
    
    # Fix: Open with UTF-8 encoding
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    # Create temp config file with UTF-8 encoding for parameters_loader
    temp_config = Path('temp_config.yaml')
    with open(temp_config, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f)
    
    params = load_parameters(str(temp_config))
    
    print("Running Monte Carlo simulation (1000 runs)...")
    print("This may take a few minutes...")
    
    results, gross_flows, waterfall_log, net_lp_flows = run_monte_carlo(
        params=params,
        num_simulations=1000,
        seed=421,
        verbose=False
    )
    
    print("Simulation complete. Saving results...")
    
    # Create directory
    default_path = Path("default_scenario")
    default_path.mkdir(exist_ok=True)
    
    # Save config
    with open(default_path / "config.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f)
    
    # Save results
    results_dict = {
        'all_results': results,
        'all_gross_flows': gross_flows,
        'waterfall_log': waterfall_log,
        'net_lp_flows_log': net_lp_flows
    }
    
    with open(default_path / "results.pkl", 'wb') as f:
        pickle.dump(results_dict, f)
    
    # Generate and save Excel file
    print("Generating Excel report...")
    from engine import convert_multiple_simulations_to_excel_with_flows
    
    excel_filename = default_path / "results.xlsx"
    convert_multiple_simulations_to_excel_with_flows(
        results,
        gross_flows,
        waterfall_log=waterfall_log,
        net_lp_flows_log=net_lp_flows,
        filename=str(excel_filename)
    )
    print(f"✅ Excel report saved to {excel_filename}")
    
    # Save metadata
    from datetime import datetime
    import json
    
    metadata = {
        'name': 'Base Case - Institutional Realism',
        'timestamp': datetime.now().isoformat(),
        'has_results': True,
        'num_simulations': 1000,
        'seed': 421
    }
    
    with open(default_path / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    # Clean up temp file
    temp_config.unlink()
    
    print(f"✅ Default scenario saved to {default_path}")
    print("You can now run the Streamlit app with pre-loaded results")

if __name__ == "__main__":
    precompute_default_scenario()
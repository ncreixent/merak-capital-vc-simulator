# scenario_manager.py

import pandas as pd
import numpy as np
import yaml
import pickle
import json
from datetime import datetime
from pathlib import Path

from parameters_loader import load_parameters
from engine import run_monte_carlo, convert_multiple_simulations_to_excel_with_flows

class ScenarioManager:
    """Manages scenario creation, storage, and comparison"""
    
    @staticmethod
    def create_scenario(name, config_dict, params=None):
        """Create a new scenario from configuration"""
        return {
            'name': name,
            'timestamp': datetime.now(),
            'config': config_dict,
            'results': None,
            'gross_flows': None,
            'waterfall_log': None,
            'net_lp_flows': None,
            'params': params,
            'cached_metrics': None  # Cache for calculated metrics
        }
    
    @staticmethod
    def run_scenario(scenario, num_simulations=1000, seed=None):
        """Execute Monte Carlo simulation for a scenario"""
        try:
            # Save config to temporary file
            temp_config_path = Path("temp_config.yaml")
            with open(temp_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(scenario['config'], f)
            
            # Load parameters and run simulation
            params = load_parameters(str(temp_config_path))
            results, gross_flows, waterfall_log, net_lp_flows = run_monte_carlo(
                params=params,
                num_simulations=num_simulations,
                seed=seed,
                verbose=False
            )
            
            # Update scenario with results
            scenario['results'] = results
            scenario['gross_flows'] = gross_flows
            scenario['waterfall_log'] = waterfall_log
            scenario['net_lp_flows'] = net_lp_flows
            scenario['params'] = params
            scenario['cached_metrics'] = None  # Clear cache when new results are added
            
            # Clean up temp file
            temp_config_path.unlink()
            
            return True, "Simulation completed successfully"
        
        except Exception as e:
            return False, f"Error running simulation: {str(e)}"
    
    @staticmethod
    def calculate_metrics(scenario, force_recalculate=False):
        """Calculate summary metrics from scenario results with caching"""
        if scenario['results'] is None:
            return None
        
        # Return cached metrics if available and not forcing recalculation
        if not force_recalculate and scenario.get('cached_metrics') is not None:
            # Debug: Uncomment the line below to see when cache is being used
            # print(f"Using cached metrics for scenario: {scenario['name']}")
            return scenario['cached_metrics']
        
        results = scenario['results']
        df_results = pd.DataFrame([vars(res) for res in results])
        
        metrics = {
            'median_net_irr': df_results['net_irr'].median(),
            'mean_net_irr': df_results['net_irr'].mean(),
            'median_net_multiple': df_results['net_multiple'].median(),
            'mean_net_multiple': df_results['net_multiple'].mean(),
            'median_gross_irr': df_results['gross_irr'].median(),
            'mean_gross_irr': df_results['gross_irr'].mean(),
            'median_gross_multiple': df_results['gross_multiple'].median(),
            'mean_gross_multiple': df_results['gross_multiple'].mean(),
            'var_5': df_results['net_irr'].quantile(0.05),
            'var_10': df_results['net_irr'].quantile(0.10),
            'avg_portfolio_size': np.mean([len(res.company_results) for res in results]),
            'avg_initial_investment': None,  # Will calculate from company results
            'avg_cumulative_investment': None  # Will calculate from company results
        }
        
        # Calculate investment metrics from company results
        all_initial_investments = []
        all_cumulative_investments = []
        
        for res in results:
            for company in res.company_results:
                if company.history:
                    initial_inv = company.history[0].get('round_investment', 0)
                    all_initial_investments.append(initial_inv)
                    all_cumulative_investments.append(company.total_invested)
        
        if all_initial_investments:
            metrics['avg_initial_investment'] = np.mean(all_initial_investments)
        if all_cumulative_investments:
            metrics['avg_cumulative_investment'] = np.mean(all_cumulative_investments)
        
        # Cache the calculated metrics
        scenario['cached_metrics'] = metrics
        
        # Debug: Uncomment the line below to see when metrics are being calculated
        # print(f"Calculated new metrics for scenario: {scenario['name']}")
        
        return metrics
    
    @staticmethod
    def export_scenario(scenario, export_path):
        """Export scenario to disk"""
        export_path = Path(export_path)
        export_path.mkdir(parents=True, exist_ok=True)
        
        # Save config
        with open(export_path / "config.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(scenario['config'], f)
        
        # Save results if available
        if scenario['results'] is not None:
            results_dict = {
                'all_results': scenario['results'],
                'all_gross_flows': scenario['gross_flows'],
                'waterfall_log': scenario['waterfall_log'],
                'net_lp_flows_log': scenario['net_lp_flows']
            }
            
            with open(export_path / "results.pkl", 'wb') as f:
                pickle.dump(results_dict, f)
            
            # Save Excel file if pre-generated, otherwise generate it
            if 'excel_buffer' in scenario and scenario['excel_buffer'] is not None:
                with open(export_path / "results.xlsx", 'wb') as f:
                    f.write(scenario['excel_buffer'])
            else:
                # Generate Excel export
                convert_multiple_simulations_to_excel_with_flows(
                    scenario['results'],
                    scenario['gross_flows'],
                    waterfall_log=scenario['waterfall_log'],
                    net_lp_flows_log=scenario['net_lp_flows'],
                    filename=str(export_path / "results.xlsx")
                )
        
        # Save metadata
        metadata = {
            'name': scenario['name'],
            'timestamp': scenario['timestamp'].isoformat(),
            'has_results': scenario['results'] is not None,
            'has_excel': ('excel_buffer' in scenario and scenario['excel_buffer'] is not None) or scenario['results'] is not None
        }
        
        with open(export_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    @staticmethod
    def import_scenario(import_path):
        """Import scenario from disk"""
        import_path = Path(import_path)
        
        # Load config
        with open(import_path / "config.yaml", 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        # Load metadata
        with open(import_path / "metadata.json", 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        scenario = {
            'name': metadata['name'],
            'timestamp': datetime.fromisoformat(metadata['timestamp']),
            'config': config_dict,
            'results': None,
            'gross_flows': None,
            'waterfall_log': None,
            'net_lp_flows': None,
            'params': None,
            'cached_metrics': None,
            'excel_buffer': None
        }
        
        # Load results if available
        results_path = import_path / "results.pkl"
        if results_path.exists():
            with open(results_path, 'rb') as f:
                results_dict = pickle.load(f)
                scenario['results'] = results_dict['all_results']
                scenario['gross_flows'] = results_dict['all_gross_flows']
                scenario['waterfall_log'] = results_dict['waterfall_log']
                scenario['net_lp_flows'] = results_dict['net_lp_flows_log']
        
        # Load Excel file if available
        excel_path = import_path / "results.xlsx"
        if excel_path.exists():
            with open(excel_path, 'rb') as f:
                scenario['excel_buffer'] = f.read()
        
        return scenario

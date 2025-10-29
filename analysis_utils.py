# analysis_utils.py (Updated)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List
from parameters import PortfolioResult, CompanyResult

def display_portfolio_deep_dive(results: List[PortfolioResult]):
    """
    Displays a detailed summary of the portfolio results, including IRR, multiples,
    and outcomes of individual companies.
    """
    if not results:
        print("No simulation results to display.")
        return

    # Assuming we are deep-diving into the first simulation run for this example
    # In a real scenario, you might want to select a specific run (e.g., by seed)
    result = results[0]

    print("--- Portfolio Deep Dive ---")
    print(f"Net IRR: {result.net_irr:.2%}")
    print(f"Net Multiple: {result.net_multiple:.2f}x")
    print(f"Gross IRR: {result.gross_irr:.2%}")
    print(f"Gross Multiple: {result.gross_multiple:.2f}x")
    print(f"Capital Constrained: {'Yes' if result.capital_constrained else 'No'}")
    print(f"Final Fund Life: {result.final_fund_life_years} years")
    print("-" * 25)

    company_data = []
    for cr in result.company_results:
        company_data.append({
            "ID": cr.company_id,
            "Start Stage": cr.start_stage,
            "End Stage": cr.end_stage,
            "Total Invested": cr.total_invested,
            "Proceeds": cr.proceeds_to_fund,
            "MOIC": cr.multiple_on_invested
        })
    
    df = pd.DataFrame(company_data)
    if not df.empty:
        df['Total Invested'] = df['Total Invested'].apply(lambda x: f"${x:,.0f}")
        df['Proceeds'] = df['Proceeds'].apply(lambda x: f"${x:,.0f}")
        df['MOIC'] = df['MOIC'].apply(lambda x: f"{x:.2f}x")
        print("Individual Company Outcomes:")
        display(df)
    else:
        print("No companies were invested in during this simulation run.")


# --- NEW: Function to visualize company journeys ---
def display_company_journeys(result: PortfolioResult):
    """
    Generates plots for each company in a simulation result, showing the
    evolution of its valuation and the fund's investment over time.
    
    Args:
        result: A single PortfolioResult object from a simulation run.
    """
    print(f"\n--- Company Journeys Visualization ---")
    
    successful_companies = [c for c in result.company_results if c.total_invested > 0 and len(c.journey) > 1]
    
    if not successful_companies:
        print("No company journeys with follow-on investments to display for this run.")
        return

    num_companies = len(successful_companies)
    # Adjust subplot grid size for better readability
    cols = min(3, num_companies)
    rows = int(np.ceil(num_companies / cols))
    
    fig, axes = plt.subplots(rows, cols, figsize=(7 * cols, 5 * rows), squeeze=False)
    axes = axes.flatten()

    for i, company_result in enumerate(successful_companies):
        ax = axes[i]
        
        # Prepare data for plotting
        journey_data = []
        for stage_prog in company_result.journey:
            journey_data.append({
                "month": stage_prog.month,
                "valuation": stage_prog.valuation,
                "investment": stage_prog.investment,
                "stage": stage_prog.stage
            })
        
        df = pd.DataFrame(journey_data)
        
        # Plot valuation trend
        ax.plot(df['month'], df['valuation'], marker='o', linestyle='-', color='b', label='Post-Money Valuation')
        ax.set_ylabel("Valuation ($)", color='b')
        ax.tick_params(axis='y', labelcolor='b')
        ax.set_title(f"Company {company_result.company_id} ({company_result.start_stage} -> {company_result.end_stage})")
        ax.set_xlabel("Time (Months)")
        
        # Create a second y-axis for investment amounts
        ax2 = ax.twinx()
        ax2.bar(df['month'], df['investment'], width=2, alpha=0.6, color='g', label='Investment Amount')
        ax2.set_ylabel("Investment ($)", color='g')
        ax2.tick_params(axis='y', labelcolor='g')
        
        # Add labels for stages
        for _, row in df.iterrows():
            ax.text(row['month'], row['valuation'], f" {row['stage']}", verticalalignment='bottom', fontsize=9)
            
        # Formatting
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        fig.tight_layout()

    # Hide any unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
        
    plt.show()
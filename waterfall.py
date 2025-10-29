"""
# waterfall.py (v2.0.0)
# Enhanced European whole-fund waterfall with improved documentation and optional debug output"""

import numpy as np
import pandas as pd
from typing import List, Tuple
from parameters import FundParameters


def apply_fund_structure(
    gross_fund_flows_tagged: List[Tuple[float, float, int]],
    params: FundParameters,
    actual_fund_lifespan_months: float,
    verbose: bool = False
) -> Tuple[List[Tuple[float, float]], int, pd.DataFrame]:
    """
    Applies a standard European-style, whole-fund waterfall structure to gross fund cash flows
    and returns detailed annual breakdown of distributions.
    
    This function processes all fund transactions through a four-tier waterfall:
    1. Return of Capital (ROC) - Return invested capital to LPs and GP pro-rata
    2. Preferred Return - Pay accumulated preferred return to LPs 
    3. GP Catch-up - Allow GP to catch up to target carried interest percentage
    4. Final Split - Remaining proceeds split according to carried interest terms
    
    Args:
        gross_fund_flows_tagged: List of (amount, time_months, transaction_id) tuples
        params: Fund parameters including waterfall terms
        actual_fund_lifespan_months: Total duration of fund in months
        verbose: If True, prints detailed calculation steps for debugging
        
    Returns:
        Tuple containing:
        - LP net cash flows for IRR calculation
        - Total fund life in years  
        - DataFrame with detailed annual waterfall breakdown
    """
    
    # Calculate total fund duration in complete years
    total_fund_life_years = int(np.ceil(actual_fund_lifespan_months / 12.0))
    
    # Handle edge case of empty transaction list
    if not gross_fund_flows_tagged:
        if verbose:
            print("No transactions found - returning empty results")
        return [], total_fund_life_years, pd.DataFrame()

    # --- DATA PREPARATION SECTION ---
    # Convert transaction list to structured DataFrame for easier analysis
    df_gross = pd.DataFrame(gross_fund_flows_tagged, columns=['amount', 'time_months', 'id'])
    
    # Assign transactions to calendar years with robust boundary handling
    # Uses floor division to correctly assign transactions at year boundaries
    # (e.g., month 12.0 = Year 1, month 12.001 = Year 2)
    df_gross['year'] = (np.floor((df_gross['time_months'] - 1e-9) / 12.0) + 1).astype(int)
    df_gross['year'] = np.clip(df_gross['year'], 1, total_fund_life_years)
    
    if verbose:
        print("=== TRANSACTION DATA PREPARATION ===")
        print("All transactions with year assignments:")
        print(df_gross)
    
    # Create master year index for consistent reporting across all years
    all_years_index = pd.RangeIndex(start=1, stop=total_fund_life_years + 1, name='year')
    
    # Group and aggregate transactions by type and year
    # Capital calls (id = -2): Money called from investors
    annual_capital_calls = (df_gross[df_gross['id'] == -2]['amount'].abs()
                           .groupby(df_gross['year']).sum()
                           .reindex(all_years_index, fill_value=0.0))
    
    # Investment proceeds (id > 0, < 9999): Returns from successful investments  
    annual_gross_proceeds = (df_gross[(df_gross['id'] > 0) & (df_gross['id'] < 9999) & (df_gross['amount'] > 0)]['amount']
                            .groupby(df_gross['year']).sum()
                            .reindex(all_years_index, fill_value=0.0))
    
    # Cash distributions from fund reserves (id = 9999)
    annual_cash_back = (df_gross[df_gross['id'] == 9999]['amount'].abs()
                       .groupby(df_gross['year']).sum()
                       .reindex(all_years_index, fill_value=0.0))
    
    # Investment outflows (negative amounts for id > 0): Money deployed into investments
    annual_investment = (df_gross[(df_gross['id'] > 0) & (df_gross['amount'] < 0)]['amount']
                        .groupby(df_gross['year']).sum()
                        .reindex(all_years_index, fill_value=0.0))
    
    # Management fees and expenses (id = -1)
    annual_fees = (df_gross[df_gross['id'] == -1]['amount']
                  .groupby(df_gross['year']).sum()
                  .reindex(all_years_index, fill_value=0.0))
    
    # Calculate net cash flow position by converting capital calls to positive values
    cash_flow = df_gross.copy()
    cash_flow.loc[cash_flow['id'] == -2, 'amount'] = cash_flow.loc[cash_flow['id'] == -2, 'amount'].abs()
    
    if verbose:
        print("\nNet cash flow calculation (capital calls converted to positive):")
        print(cash_flow)
    
    # Aggregate net cash flows by year
    cash_flow = (cash_flow['amount'].groupby(cash_flow['year']).sum()
                .reindex(all_years_index, fill_value=0.0))
    
    if verbose:
        print(f"\nAnnual net cash flows by year: \n{cash_flow}")

    # --- WATERFALL STATE VARIABLES INITIALIZATION ---
    # Set up all tracking variables for the four-tier waterfall calculation
    
    # Commitment ownership percentages
    gp_commit_pct = params.waterfall.gp_capital_contribution_pct
    lp_commit_pct = 1 - gp_commit_pct
    
    # Running totals of capital contributions
    lp_contributions_total = 0.0    # Total capital called from LPs
    gp_contributions_total = 0.0    # Total capital called from GP
    
    # Running totals of capital returned (Tier 1 - Return of Capital)
    lp_distributions_total = 0.0    # LP capital returned
    gp_distributions_total = 0.0    # GP capital returned
    
    # Preferred return tracking (Tier 2)
    lp_preference_basis = 0.0       # Base amount on which preferred return accrues
    cum_pref_payments = 0.0         # Cumulative preferred return paid to LPs
    lp_pref_balance = 0.0          # Outstanding preferred return owed to LPs
    
    # Carried interest tracking (Tiers 3 & 4) 
    lp_carry_total = 0.0           # Cumulative profit distributions to LPs
    gp_carry_total = 0.0           # Cumulative carried interest to GP
    
    # Output tracking
    net_lp_flows_by_year = {year: 0.0 for year in range(1, total_fund_life_years + 1)}
    waterfall_details_log = []      # Detailed annual breakdown for reporting
    lp_net_flows_for_net_irr = pd.DataFrame(columns=['amount', 'time_months', 'id', 'year'])

    # --- MAIN WATERFALL CALCULATION LOOP ---
    # Process each year of the fund's life through the four-tier waterfall
    
    for year in range(1, total_fund_life_years + 1):
        if verbose:
            print(f'\n{"="*50}')
            print(f'PROCESSING YEAR {year} WATERFALL CALCULATIONS')
            print(f'{"="*50}')
        
        # Store starting positions for this year's calculations
        lp_preference_basis_start = lp_preference_basis
        starting_unreturned_lp_capital = lp_contributions_total - lp_distributions_total
        starting_unreturned_gp_capital = gp_contributions_total - gp_distributions_total
        starting_total_unreturned_capital = starting_unreturned_lp_capital + starting_unreturned_gp_capital
        
        # Calculate outstanding preferred return balance at start of year
        lp_pref_balance = lp_preference_basis - starting_unreturned_lp_capital
        lp_pref_balance_start = lp_pref_balance
        
        if verbose:
            print(f'\nSTARTING POSITIONS FOR YEAR {year}:')
            print(f'  LP unreturned capital: ${starting_unreturned_lp_capital:,.0f}')
            print(f'  GP unreturned capital: ${starting_unreturned_gp_capital:,.0f}')
            print(f'  LP preference balance owed: ${lp_pref_balance:,.0f}')
        
        # PREFERRED RETURN ACCRUAL ON EXISTING CAPITAL
        # Add preferred return on the preference basis (unreturned capital + accrued pref)
        carry_over_preference_increase = 0
        current_year_preference_increase = 0
        
        if lp_preference_basis > 0:
            carry_over_preference_increase = lp_preference_basis * params.waterfall.preferred_return_pct
            lp_pref_balance += carry_over_preference_increase
            
            if verbose:
                print(f'\nPREFERRED RETURN ACCRUAL:')
                print(f'  Preference basis at start: ${lp_preference_basis:,.0f}')
                print(f'  Annual preferred rate: {params.waterfall.preferred_return_pct:.1%}')
                print(f'  Accrued preferred return: ${carry_over_preference_increase:,.0f}')

        # CAPITAL CONTRIBUTIONS PROCESSING
        # Handle new capital calls and apply pro-rata preferred return for partial year
        capital_called_this_year = annual_capital_calls.get(year, 0.0)
        capital_calls_detailed = df_gross[(df_gross['year'] == year) & (df_gross['id'] == -2)].copy()
        
        # Calculate additional data for reporting
        investments_this_year = annual_investment.get(year, 0.0)
        cumulative_investments = annual_investment.loc[1:year].sum()
        fees_this_year = annual_fees.get(year, 0.0)
        cumulative_fees = annual_fees.loc[1:year].sum()
        
        # Apply preferred return to mid-year capital contributions
        # Capital called mid-year earns preferred return for remaining months of the year
        if not capital_calls_detailed.empty:
            # Calculate months from contribution date to end of year
            end_of_year_months = year * 12
            months_remaining = end_of_year_months - capital_calls_detailed['time_months']
            
            # Apply monthly preferred return for remaining time
            monthly_preferred_rate = params.waterfall.preferred_return_pct / 12.0
            preferred_return_multiplier = (1 + monthly_preferred_rate * months_remaining)
            
            # Update capital call amounts to include accrued preferred return
            capital_calls_detailed['amount'] = capital_calls_detailed['amount'] * preferred_return_multiplier
            
            # Calculate the incremental preferred return added
            current_year_preference_increase = (-sum(capital_calls_detailed['amount']) * lp_commit_pct - 
                                              capital_called_this_year * lp_commit_pct)
            lp_pref_balance += current_year_preference_increase
            
            if verbose:
                print(f'\nMID-YEAR CAPITAL CALL PREFERRED RETURN:')
                print(f'  Number of capital calls: {len(capital_calls_detailed)}')
                print(f'  Monthly preferred rate: {monthly_preferred_rate:.4%}')
                print(f'  Months remaining in year: {months_remaining.tolist()}')
                print(f'  Preferred return multipliers: {preferred_return_multiplier.tolist()}')
                print(f'  Additional preferred return accrued: ${current_year_preference_increase:,.0f}')
                print(f'  Total LP preference balance: ${lp_pref_balance:,.0f}')
        
        # Split capital contributions between LP and GP based on commitment percentages
        lp_contribution_this_year = capital_called_this_year * lp_commit_pct
        gp_contribution_this_year = capital_called_this_year * gp_commit_pct
        lp_contributions_total += lp_contribution_this_year
        gp_contributions_total += gp_contribution_this_year
        
        # Record LP capital contribution as negative cash flow
        if lp_contribution_this_year > 0:
            net_lp_flows_by_year[year] -= lp_contribution_this_year
        
        if verbose:
            print(f'\nCAPITAL CONTRIBUTION SUMMARY:')
            print(f'  Total capital called: ${capital_called_this_year:,.0f}')
            print(f'  LP contribution (@ {lp_commit_pct:.1%}): ${lp_contribution_this_year:,.0f}')
            print(f'  GP contribution (@ {gp_commit_pct:.1%}): ${gp_contribution_this_year:,.0f}')
            print(f'  Cumulative LP contributions: ${lp_contributions_total:,.0f}')
            print(f'  Cumulative GP contributions: ${gp_contributions_total:,.0f}')

        # DISTRIBUTION PROCESSING
        # Calculate total distributable cash from investment proceeds and cash reserves
        distributable_cash = annual_gross_proceeds.get(year, 0.0) + annual_cash_back.get(year, 0.0)
        
        if verbose:
            print(f'\nDISTRIBUTABLE CASH ANALYSIS:')
            print(f'  Investment proceeds: ${annual_gross_proceeds.get(year, 0.0):,.0f}')
            print(f'  Cash from reserves: ${annual_cash_back.get(year, 0.0):,.0f}')
            print(f'  Total distributable: ${distributable_cash:,.0f}')
        
        if distributable_cash <= 0:
            if verbose:
                print(f'  No distributions in Year {year} - proceeding to next year')
            # Continue to record keeping even with no distributions
        
        # --- TIER 1: RETURN OF CAPITAL (ROC) ---
        # Return invested capital to both LP and GP on a pro-rata basis
        total_unreturned_capital = ((lp_contributions_total + gp_contributions_total) - 
                                  (lp_distributions_total + gp_distributions_total))
        roc_payment = min(distributable_cash, total_unreturned_capital)
        
        # Calculate pro-rata shares based on total contributions
        total_contributions = lp_contributions_total + gp_contributions_total
        lp_roc_share = lp_contributions_total / total_contributions if total_contributions > 0 else 0
        
        lp_roc_payment = roc_payment * lp_roc_share
        gp_roc_payment = roc_payment - lp_roc_payment
        
        # Update distribution totals and reduce remaining distributable cash
        lp_distributions_total += lp_roc_payment
        gp_distributions_total += gp_roc_payment
        distributable_cash -= roc_payment
        
        if verbose:
            print(f'\nTIER 1 - RETURN OF CAPITAL:')
            print(f'  Total unreturned capital: ${total_unreturned_capital:,.0f}')
            print(f'  ROC payment available: ${roc_payment:,.0f}')
            print(f'  LP pro-rata share: {lp_roc_share:.1%}')
            print(f'  ROC to LP: ${lp_roc_payment:,.0f}')
            print(f'  ROC to GP: ${gp_roc_payment:,.0f}')
            print(f'  Remaining distributable cash: ${distributable_cash:,.0f}')

        # --- TIER 2: PREFERRED RETURN ---
        # Pay accumulated preferred return to LPs before any profit sharing
        pref_payment = min(distributable_cash, lp_pref_balance)
        lp_pref_balance -= pref_payment
        distributable_cash -= pref_payment
        cum_pref_payments += pref_payment
        
        if verbose:
            print(f'\nTIER 2 - PREFERRED RETURN:')
            print(f'  LP preference balance owed: ${lp_pref_balance + pref_payment:,.0f}')
            print(f'  Preferred return payment: ${pref_payment:,.0f}')
            print(f'  Remaining preference balance: ${lp_pref_balance:,.0f}')
            print(f'  Remaining distributable cash: ${distributable_cash:,.0f}')

        # --- TIER 3: GP CATCH-UP ---
        # Allow GP to receive higher percentage until reaching target carried interest proportion
        cumulative_proceeds = annual_gross_proceeds.loc[1:year].sum()
        total_profit_so_far = cumulative_proceeds - (lp_contributions_total + gp_contributions_total)
        total_payments_to_lp = cum_pref_payments + lp_carry_total
        
        gp_catch_up_payment, lp_catch_up_share = 0.0, 0.0
        
        # Determine if catch-up is needed (LP share of profits exceeds target)
        total_profit_payments = total_payments_to_lp + gp_carry_total
        if total_profit_payments > 0:
            lp_profit_share = total_payments_to_lp / total_profit_payments
            catch_up_needed = lp_profit_share > (1 - params.waterfall.carried_interest_pct)
        else:
            catch_up_needed = False
        
        if distributable_cash > 0 and params.waterfall.catch_up_pct > 0 and catch_up_needed:
            if verbose:
                print(f'\nTIER 3 - GP CATCH-UP (CATCH-UP REQUIRED):')
                print(f'  Cumulative investment proceeds: ${cumulative_proceeds:,.0f}')
                print(f'  Total profit generated: ${total_profit_so_far:,.0f}')
                print(f'  Total profit distributed: ${total_profit_payments:,.0f}')
                print(f'  LP share of distributed profits: {lp_profit_share:.1%}')
                print(f'  Target LP share: {1-params.waterfall.carried_interest_pct:.1%}')
            
            # Calculate total catch-up needed to reach target carried interest ratio
            numerator = ((params.waterfall.carried_interest_pct * total_payments_to_lp) - 
                        (1 - params.waterfall.carried_interest_pct) * gp_carry_total)
            denominator = (params.waterfall.catch_up_pct - params.waterfall.carried_interest_pct)
            catch_up_payments_needed_total = numerator / denominator
            
            catch_up_payments_available = min(catch_up_payments_needed_total, distributable_cash)
            gp_catch_up_payment = params.waterfall.catch_up_pct * catch_up_payments_available
            lp_catch_up_share = (1 - params.waterfall.catch_up_pct) * catch_up_payments_available
            
            # Update carry totals and reduce distributable cash
            gp_carry_total += gp_catch_up_payment
            lp_carry_total += lp_catch_up_share
            distributable_cash -= catch_up_payments_available
            
            if verbose:
                print(f'  Total catch-up needed: ${catch_up_payments_needed_total:,.0f}')
                print(f'  Catch-up payment available: ${catch_up_payments_available:,.0f}')
                print(f'  GP catch-up payment (@ {params.waterfall.catch_up_pct:.0%}): ${gp_catch_up_payment:,.0f}')
                print(f'  LP catch-up share (@ {1-params.waterfall.catch_up_pct:.0%}): ${lp_catch_up_share:,.0f}')
                
                # Show updated profit distribution ratios
                updated_total_lp = total_payments_to_lp + lp_catch_up_share
                updated_total_gp = gp_carry_total
                updated_total = updated_total_lp + updated_total_gp
                if updated_total > 0:
                    print(f'  Updated LP profit share: {updated_total_lp/updated_total:.1%}')
                    print(f'  Updated GP profit share: {updated_total_gp/updated_total:.1%}')
        elif verbose:
            print(f'\nTIER 3 - GP CATCH-UP (NO CATCH-UP NEEDED):')
            if total_profit_payments > 0:
                print(f'  LP profit share {lp_profit_share:.1%} ≤ target {1-params.waterfall.carried_interest_pct:.1%}')
            else:
                print(f'  No profits distributed yet')

        # --- TIER 4: FINAL SPLIT ---
        # Remaining proceeds split according to carried interest percentage
        gp_final_split, lp_final_split = 0.0, 0.0
        if distributable_cash > 0:
            gp_final_split = distributable_cash * params.waterfall.carried_interest_pct
            lp_final_split = distributable_cash * (1 - params.waterfall.carried_interest_pct)
            gp_carry_total += gp_final_split
            lp_carry_total += lp_final_split
            
            if verbose:
                print(f'\nTIER 4 - FINAL SPLIT:')
                print(f'  Remaining distributable cash: ${distributable_cash:,.0f}')
                print(f'  GP final split (@ {params.waterfall.carried_interest_pct:.0%}): ${gp_final_split:,.0f}')
                print(f'  LP final split (@ {1-params.waterfall.carried_interest_pct:.0%}): ${lp_final_split:,.0f}')

        # YEAR-END CALCULATIONS AND RECORD KEEPING
        total_to_lp_this_year = lp_roc_payment + pref_payment + lp_catch_up_share + lp_final_split
        total_to_gp_this_year = gp_roc_payment + gp_catch_up_payment + gp_final_split
        
        # Update preference basis for next year (unreturned capital + outstanding preferred return)
        lp_preference_basis = (lp_contributions_total - lp_distributions_total) + lp_pref_balance
        
        # Calculate fund's cash position
        cash_flow_this_year = (cash_flow.get(year, 0.0) - lp_roc_payment - gp_roc_payment - 
                              pref_payment - gp_catch_up_payment - lp_catch_up_share - 
                              gp_final_split - lp_final_split - annual_cash_back.get(year, 0.0))
        
        cumulative_cash_flow = (cash_flow.loc[1:year].sum() - lp_distributions_total - 
                               gp_distributions_total - cum_pref_payments - lp_carry_total - 
                               gp_carry_total - annual_cash_back[1:year].sum())
        
        if verbose:
            print(f'\nYEAR {year} SUMMARY:')
            print(f'  Total distributions to LP: ${total_to_lp_this_year:,.0f}')
            print(f'  Total distributions to GP: ${total_to_gp_this_year:,.0f}')
            print(f'  Fund cash flow this year: ${cash_flow_this_year:,.0f}')
            print(f'  Fund cumulative cash position: ${cumulative_cash_flow:,.0f}')

        # Store detailed breakdown for reporting
        waterfall_details_log.append({
            'Year': year,
            'Starting GP Unreturned Capital': starting_unreturned_gp_capital,
            'Starting LP Unreturned Capital': starting_unreturned_lp_capital,
            'Starting Total Unreturned Capital': starting_total_unreturned_capital,
            'LP Preference Basis Start': lp_pref_balance_start,
            'Pref Balance Start': lp_preference_basis_start,
            'GP Contributions in year': gp_contribution_this_year,
            'LP Contributions in year': lp_contribution_this_year,
            'LP Preference increase from balance start': carry_over_preference_increase,
            'LP Preference increase due to mid-year contributions': current_year_preference_increase,
            'LP Preference before distributions': lp_pref_balance_start + carry_over_preference_increase + current_year_preference_increase,
            'Distributable Proceeds this year': annual_gross_proceeds.get(year, 0.0),
            'Distributable Cash back this year': annual_cash_back.get(year, 0.0),
            'ROC to LP': lp_roc_payment,
            'ROC to GP': gp_roc_payment,
            'Pref to LP': pref_payment,
            'Catch-up to GP': gp_catch_up_payment,
            'Catch-up LP cut': lp_catch_up_share,
            'Final Split to LP': lp_final_split,
            'Final Split to GP': gp_final_split,
            'Total to LP': total_to_lp_this_year,
            'Total to GP': total_to_gp_this_year,
            'Cumulative Contributions so far': lp_contributions_total + gp_contributions_total,
            'Distributable Proceeds so far': cumulative_proceeds,
            'Cumulative profits before returns and distributions': total_profit_so_far,
            'ROC to LP Cumulative': lp_distributions_total,
            'ROC to GP Cumulative': gp_distributions_total,
            'Pref to LP Cumulative': cum_pref_payments,
            'LP Carry Cumulative': lp_carry_total,
            'GP Carry Cumulative': gp_carry_total,
            'Total to LP Cumulative': lp_carry_total + cum_pref_payments + lp_distributions_total,
            'Total to GP Cumulative': gp_carry_total + gp_distributions_total,
            'Year Investments': investments_this_year,
            'Year Fees': fees_this_year,
            'Cumulative Investments': cumulative_investments,
            'Cumulative Fees': cumulative_fees,
            'Cash Flow in year': cash_flow_this_year,
            'Cash Position EOY': cumulative_cash_flow
        })
        
        # Update LP net flows for IRR calculation
        net_lp_flows_by_year[year] += total_to_lp_this_year
        lp_net_flows_for_net_irr.loc[year - 1, 'amount'] = total_to_lp_this_year
        lp_net_flows_for_net_irr.loc[year - 1, 'time_months'] = year * 12
        lp_net_flows_for_net_irr.loc[year - 1, 'id'] = 10000
        lp_net_flows_for_net_irr.loc[year - 1, 'year'] = year

    # --- FINALIZE RESULTS ---
    # Prepare LP contribution data for IRR calculation
    lp_contributions_by_year = df_gross[df_gross['id'] == -2].copy()
    lp_contributions_by_year['amount'] = lp_contributions_by_year['amount'] * lp_commit_pct
    
    # Combine distributions and contributions for complete LP cash flow picture
    lp_net_flows_for_net_irr = pd.concat([lp_net_flows_for_net_irr, lp_contributions_by_year], ignore_index=True)
    lp_net_flows_for_net_irr = lp_net_flows_for_net_irr.sort_values('time_months')
    
    # Create comprehensive waterfall details DataFrame
    df_waterfall_details = pd.DataFrame(waterfall_details_log).set_index('Year')
    
    if verbose:
        print(f'\n{"="*50}')
        print('WATERFALL CALCULATION COMPLETE')
        print(f'{"="*50}')
        print(f'Total fund years processed: {total_fund_life_years}')
        print(f'Final LP cumulative distributions: ${lp_carry_total + cum_pref_payments + lp_distributions_total:,.0f}')
        print(f'Final GP cumulative distributions: ${gp_carry_total + gp_distributions_total:,.0f}')
    
    return lp_net_flows_for_net_irr, total_fund_life_years, df_waterfall_details
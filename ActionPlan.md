Strategic Action Plan: Using the VC Fund Model for Decision Making
This document outlines a structured, four-phase process for using the Monte Carlo simulation model to derive actionable strategic insights for fund management.

Phase 1: Establish a Base Case
Objective: Create a foundational, statistically significant understanding of the fund's expected performance under the most likely set of assumptions.

Action Items:

Finalize config.yaml: Ensure all parameters in the main config.yaml file reflect your core investment thesis and most probable market assumptions.

Run a Large Simulation: Execute the run_monte_carlo function for a high number of iterations (e.g., 10,000 to 20,000 runs). This large sample size is crucial for generating a stable distribution of outcomes.

Analyze Key Metrics: Save and analyze the full output from the "FINAL ANALYSIS & VISUALIZATION" cell. This includes:

Median Net IRR and Net Multiple.

The distribution of IRRs (the histogram plot).

Key risk metrics like Value at Risk (VaR) and the capital constraint percentage.

Document the Base Case: This set of results is your baseline against which all other scenarios and tests will be compared.

Phase 2: Identify Key Drivers (Sensitivity Analysis)
Objective: Understand which assumptions and strategic levers have the most significant impact on the fund's returns. A high sensitivity indicates a critical area of risk or opportunity.

Action Items:

Formulate Hypotheses: For each key parameter, form a strategic question (e.g., "How reliant are we on massive 'home run' exits?").

Configure sensitivity_suite: In your notebook, define a series of tests in the sensitivity_suite dictionary to test these hypotheses one by one.

Run the Sensitivity Suite: Execute the run_sensitivity_suite function.

Analyze the Output Graphs:

Steep Slope: Indicates high sensitivity. This parameter is a major driver of your fund's returns.

Flat Line: Indicates low sensitivity. The fund's performance is not heavily dependent on this specific assumption.

Rank Drivers: Based on the slopes, rank the parameters from most to least sensitive. This ranked list is your guide to the most critical strategic factors.

Phase 3: Stress-Test Scenarios
Objective: Evaluate how the fund strategy performs under different, plausible macroeconomic scenarios.

Action Items:

Create Scenario Configs: Make copies of your base config.yaml and name them descriptively (e.g., config_recession.yaml, config_hot_market.yaml).

Modify Scenario Parameters: Adjust the parameters in each new file to reflect the scenario. For a recession scenario, you might lower valuation step-ups, increase failure rates, and increase the time companies spend in each stage.

Run the Model for Each Scenario: Point your parameters_loader.py script to each new config file and re-run your base case (Phase 1) simulation.

Compare Scenario Outcomes: Compare the median IRR and risk metrics from each scenario to your base case. This will reveal the resilience and vulnerabilities of your fund strategy to external market forces.

Phase 4: Analyze Outlier Portfolios
Objective: Understand the specific sequence of events that leads to extreme success (top 1%) or catastrophic failure (bottom 1%).

Action Items:

Filter the Base Case Results: Use the analyze_outlier_portfolios script in your notebook on the results from your large Phase 1 simulation.

Analyze Failed Portfolios: Look at the "Breakdown of Company Outcomes" for the worst-performing funds. Identify if there is a common pattern (e.g., a high number of failures at a specific stage) that represents a key risk factor.

Analyze "Moonshot" Portfolios: Look at the breakdown for the best-performing funds. Identify the common drivers of success (e.g., "our best funds always had at least one Series B exit with a >20x multiple"). This helps confirm what needs to go right for the strategy to succeed.



Part 1: Action Plan for "Tiered / High Conviction" Strategy (V2)
Adding a tiered follow-on strategy is a significant upgrade. It moves the model's decision-making from the portfolio level to the company level, which is a much closer simulation of how a GP thinks.

Here is the breakdown of what would be required. You can use this for your V2 planning document.

V2 Feature: Tiered "High Conviction" Follow-On Strategy
Objective: To enable the fund to allocate follow-on capital based on the relative performance of its portfolio companies, applying different pro-rata rates to different performance tiers.

Implementation Requirements:

1. A Quantifiable Company Performance Metric:

Problem: The model currently knows a company's stage, but it does not have a metric to judge how well a company is performing relative to its peers.

Solution: We must introduce a key performance indicator (KPI) that is updated at each funding milestone. The most direct and realistic KPI is the Valuation Step-Up Multiple.

Technical Detail:

In the Company class in parameters.py, add a new attribute: self.last_valuation_step_up = 1.0.

In engine.py, inside the COMPANY_MILESTONE event (when a company successfully progresses to a new stage), we must calculate this metric:

new_post_money_valuation = The post-money valuation of the current follow-on round.

previous_post_money_valuation = The post-money valuation of the previous round (this would need to be stored in the Company object).

step_up = new_post_money_valuation / previous_post_money_valuation.

This step_up value would be stored in the company's state.

2. A Dynamic Ranking and Tiering Mechanism:

Problem: The engine needs a way to rank all active companies to determine the tier of the specific company seeking funding.

Solution: Create a helper function within engine.py, let's call it _get_company_tier(portfolio, company_id).

Technical Detail: This function would be called inside the COMPANY_MILESTONE event. It would:

Get a list of all Company objects currently in the portfolio that are is_active.

Sort this list in descending order based on the last_valuation_step_up KPI.

Define tier thresholds as parameters in config.yaml (e.g., tier1_cutoff_percentile: 0.8, tier2_cutoff_percentile: 0.3).

Find the rank of the company seeking funding in the sorted list.

Based on its rank and the percentile cutoffs, return its tier: "Tier1", "Tier2", or "Tier3".

3. Configuration for Tier-Based Pro-Rata Rates:

Problem: The config.yaml needs to hold the pro-rata rates for each tier.

Solution: The follow_on_strategy section in config.yaml would be expanded.

Technical Detail:

YAML

# In config.yaml, under follow_on_strategy:
type: "tiered_conviction"

tiered_conviction_settings:
  tier1_pro_rata_rate: 1.5   # Super pro-rata for top performers
  tier2_pro_rata_rate: 1.0   # Full pro-rata for the middle
  tier3_pro_rata_rate: 0.25  # Cede ownership in laggards
  tier1_cutoff_percentile: 0.8 # Top 20% of portfolio
  tier2_cutoff_percentile: 0.3 # Next 50% (from 30th to 80th percentile)
  # Bottom 30% are implicitly Tier 3
These parameters would, of course, need corresponding dataclasses in parameters.py.

4. Final Engine Logic Modification:

Problem: The COMPANY_MILESTONE event needs to use this new system.

Solution: The logic would be entirely replaced.

Technical Detail: Instead of using one current_pro_rata_rate, the code would look like this:

Python

# In engine.py, in the COMPANY_MILESTONE event for a follow-on:

company_tier = _get_company_tier(portfolio, company.company_id)

if company_tier == "Tier1":
    pro_rata_for_this_investment = params.follow_on_strategy.tiered_settings.tier1_pro_rata_rate
elif company_tier == "Tier2":
    pro_rata_for_this_investment = params.follow_on_strategy.tiered_settings.tier2_pro_rata_rate
else: # Tier 3
    pro_rata_for_this_investment = params.follow_on_strategy.tiered_settings.tier3_pro_rata_rate

follow_on_amount = round_size * pro_rata_for_this_investment
# ... rest of the investment logic
This is a non-trivial but powerful enhancement. It would be a defining feature of a V2 model.


# ==============================================================================
# --- VC Fund Model: Data Structures (v1.9) ---
# ==============================================================================
#
# This module defines the robust, institutional-grade data structures
# for the venture capital fund simulation. It is aligned with the
# refactored loader and configuration (v1.9+).
#
# ==============================================================================

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


# --------------------------------------------------------------------------
# --- Configuration & Parameter Dataclasses ---
# --------------------------------------------------------------------------

# For meta-data and record keeping of scenarios run through the different yaml files
# Each yaml should be a scenario with its own configuration
@dataclass
class Scenario:
    # it takes the name we gave to a case such as "aggressive follow on strategy", "large fund and defensive dilution", etc
    name: str
    # The date the simulation is run. Useful for version control to distingusih between results generated on different days with potentially different code
    date: str
    # Open text field for comments
    notes: str

# Defines the fules for the fund's treasurer (_trigger_capital_call function).
# Governs how and when the fund asks LPs for money
@dataclass
class CapitalCallSettings:
    # Standard size of a capital call expressed as a % of committed capital
    # LPs prefer predictable, sizable capital calls. This parameter prevents the fund from making many small, administratively burdensome micro-calls.
    tranche_size_pct: float
    # The funds safety buffer, expressed as a % of tranche size, not fund size
    # Triggers the top up call if the fund balance falls below a certain amount
    minimum_cash_balance_pct: float

# Defines how the fund's investment focus changes over the course of the investment period
@dataclass
class StageAllocEntry:
    # Specifies the year of the fund's life to which the allocation applies
    year: int
    # A dictionary that maps the stage name to its target allocation % for that year. Sum % = 1.0 
    allocation: Dict[str, float]

# Holds the defining parameters for a lognormal distribution
@dataclass
class DistParams:
    # The mean of the underlying normal distribution
    mu_log: float
    # Std of the underlying normal distribution. The higher the sigma, the wider and more skewed the valuation distribution
    sigma_log: float
    # Descriptive tag
    type: str = "lognormal"

# This holds the 4 current follow-on strategies that we have
@dataclass
class FollowOnStrategy:
    """Container for the overall follow-on strategy."""
    type: str  # Can be 'spray_and_pray', 'passive', 'pro_rata', or 'dynamic'
    
    # This value is only used when the type is 'passive'.
    # It is ignored for all other strategy types.
    passive_participation_rate: float

# Holds the key parameters that determine how profits are split between LPs and GP
@dataclass
class Waterfall:
    # Governs catch-up tier of waterfall. After LPs receive pref.ret. this determines how cash is split until GP has "caught up"
    catch_up_pct: float
    # GP's primary profit share, "carry". Standard 20%
    carried_interest_pct: float
    # Hurdle rate; the minimum annual return that must be paid back to the LPs before the GP can take their share of profits. Standard 8%
    preferred_return_pct: float
    # Percentage of the fund that the GP invests themselves alongside LPs. Standard between 1% - 2%
    gp_capital_contribution_pct: float

# Holds the key assumptions that govern what can happen to a company when it is in a specific stage
@dataclass
class StageParams:
    # Probability that a company will sucessfully graduate from this stage to the next
    prob_to_next_stage: Optional[float]
    # Pr(company will exit)
    prob_to_exit: float
    # Pr(company will fail)
    prob_to_fail: float
    # Average number of months a company spends in this stage before next milestone event (progress, exit, fail)
    time_in_stage_months: int
    # Distribution of Post Money Valuations for the stage 
    post_money_valuation_dist: DistParams
    # Multiple Distribution
    multiple_to_next_dist: Optional[DistParams]
    # NEW, SUPERIOR PARAMETER
    # The average dilution target for a financing round at this stage.
    # For example, 0.2 represents a 20% dilution.
    target_dilution_pct: Optional[float] 
    min_valuation: float
    max_valuation: float

# Brings all the other parameter classes together into a single, comprehensive object that the simulation engine uses
@dataclass
class FundParameters:
    
    # Metadata and Control
    scenario: Scenario
    schema_version: float
    num_investments: int
    investment_period_months: int
    max_deals_per_year: int
    max_company_lifespan_months: int
    # A list of probabilities for each potential extension year
    prob_of_extensions: List[float]

    # Core Fund Economics
    committed_capital: float
    fund_lifespan_months: int
    fund_lifespan_extensions_months: int
    ownership_cap: float
    target_investable_capital_pct: float
    allow_recycling: bool
    recycling_limit_pct_of_commitment: float
    mgmt_fee_commitment_period_rate: float
    mgmt_fee_post_commitment_period_rate: float
    mgmt_fee_extension_period_rate: float
    waterfall: Waterfall

    # Strategies and Mechanics
    capital_calls: CapitalCallSettings
    follow_on_strategy: FollowOnStrategy
    dynamic_stage_allocation: List[StageAllocEntry]
    #    initial_post_money_valuation_dist: Dict[str, DistParams]
    initial_ownership_targets: Dict[str, float]

    # Lifecycle Definition (The new, robust structure)
    stages_order: List[str]
    stages: Dict[str, StageParams]



# --------------------------------------------------------------------------
# --- Simulation State & Result Dataclasses ---
# --------------------------------------------------------------------------

# Represents the state of a single company in the portfolio
@dataclass
class Company:
    """Represents the state of a single company in the portfolio."""
    # Core Attributes
    company_id: int
    start_time: float
    initial_investment: float
    current_stage: str
    valuation: float

    # NEW: More descriptive status to track fund support
    status: str = "active_supported"  # Can be 'active_supported', 'active_passive', 'exited', 'failed'

    # State Tracking
    total_invested: float = field(init=False)
    # Added
    ownership: float = 0.0
    exit_proceeds: float = 0.0
    exit_valuation: float = 0.0
    exit_time: Optional[float] = None
    outcome: Optional[str] = None

    # Enhanced Analysis Attributes
    failure_reason: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Initializes state variables and logs the creation event."""
        self.total_invested = self.initial_investment
        self.ownership = self.ownership
        self.history.append({
            "time": self.start_time,
            "event": "Initial Investment",
            "stage": self.current_stage,
            "premoney_valuation": self.valuation-self.initial_investment,
            "round_investment": self.initial_investment,
            "round_dilution": self.initial_investment/self.valuation,
            "valuation": self.valuation,
            "ownership": self.ownership
        })

    def add_follow_on(self, amount: float, new_stage: str, time: float, premoney_valuation: float, round_dilution: float, new_valuation: float, new_ownership: float):
        """Adds a follow-on investment and updates the company's state."""
        self.total_invested += amount
        self.current_stage = new_stage
        self.valuation = new_valuation
        self.ownership = new_ownership
        self.history.append({
            "time": time,
            "event": "Follow-on",
            "stage": new_stage,
            "premoney_valuation": premoney_valuation,
            "round_investment": amount,
            "round_dilution": round_dilution,
            "valuation": new_valuation,
            "ownership": new_ownership
        })

    def pass_on_round(self, new_stage: str, time: float, premoney_valuation: float, round_dilution: float, new_valuation: float, new_ownership: float):
        """NEW METHOD: Transitions the company to a passive holding after a passed round."""
        self.status = "active_passive"
        self.current_stage = new_stage
        self.valuation = new_valuation  # Update valuation to reflect the new round we passed on
        self.ownership = new_ownership # Updates ownership based on round's dilution
        self.history.append({
            "time": time,
            "event": "Passed Follow-on",
            "stage": new_stage,
            "premoney_valuation": premoney_valuation,
            "round_investment": 0,
            "round_dilution": round_dilution,
            "valuation": new_valuation,
            "ownership": new_ownership
        })

    def finalize(self, outcome: str, time: float, proceeds: float, exit_valuation: float, reason: Optional[str] = None):
        """Finalizes the company's journey."""
        self.status = outcome
        self.outcome = outcome
        self.exit_time = time
        self.exit_proceeds = proceeds
        previous_round_valuation = self.valuation 
        self.exit_valuation = exit_valuation
        self.valuation = exit_valuation
        if outcome == "failed":
            self.failure_reason = reason if reason else "probabilistic_failure"
        if outcome != "failed":
            self.history.append({
                "time": time,
                "event": "Exit",
                "stage": "Exited",
                "premoney_valuation": previous_round_valuation,
                "round_investment": 0,
                "round_dilution": 0,
                "valuation": exit_valuation,
                "ownership": self.ownership
            })

    def timeout(self, time: float):
        """A specific finalization for companies that don't exit by the end of the fund's life."""
        self.finalize("failed", time, 0, 0, reason="fund_lifespan_ended")

    def generate_result(self) -> 'CompanyResult':
        """Creates a final, immutable result object for this company."""
        return CompanyResult(
            company_id=self.company_id,
            outcome=self.outcome,
            failure_reason=self.failure_reason,
            time_to_exit_months=self.exit_time - self.start_time if self.exit_time else None,
            total_invested=self.total_invested,
            exit_valuation=self.valuation,
            exit_ownership=self.ownership,
            exit_proceeds=self.exit_proceeds,
            multiple=self.exit_proceeds / self.total_invested if self.total_invested > 0 else 0,
            history=self.history
        )

# Acts as a permanent, unchangeable record of a company's final performance
@dataclass
class CompanyResult:
    company_id: int
    outcome: str
    failure_reason: Optional[str]
    time_to_exit_months: Optional[float]
    total_invested: float
    exit_valuation: float
    exit_ownership: float
    exit_proceeds: float
    multiple: float
    history: List[Dict[str, Any]]

# Stores the aggregated results of a single fund simulation, providing a complete picture of its performance
@dataclass
class PortfolioResult:
    # Core Economic Metrics
    gross_irr: float
    net_irr: float
    gross_multiple: float
    net_multiple: float

    # Key Operational Metrics
    capital_constrained: bool
    final_fund_life_years: float
    num_extensions: int                  # NEW: Tracks fund extensions
    average_check_size: float            # NEW: Tracks the average investment amount

    # Detailed Company-Level Results
    company_results: List[CompanyResult]
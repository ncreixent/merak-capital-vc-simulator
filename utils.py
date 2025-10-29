# utils.py
import numpy as np
import scipy.optimize
from typing import List, Tuple, Optional, Dict, Any
import functools; import operator

# Net present value formula (NPV) used as a mathematical helper function by the xirr solver
def _npv_x(rate: float, cash_flows_in_years: List[Tuple[float, float]]) -> float:
    if not cash_flows_in_years: return 0.0
    return sum(amount / ((1 + rate) ** time_years) for amount, time_years in cash_flows_in_years)

# Calculates IRR using the robust Brent's method with a wide, reliable search bracket.
def xirr(cash_flows: List[Tuple[float, float]], time_unit: str = 'years') -> Optional[float]:
    # A solution is only possible if there are both positive and negative cash flows
    if not cash_flows or not (any(cf[0] > 0 for cf in cash_flows) and any(cf[0] < 0 for cf in cash_flows)):
        return None

    # --- Standardize time units to years for consistent calculation ---
    time_divisor = {'months': 12.0, 'years': 1.0}.get(time_unit, 12.0)
    # Ensure the first cash flow happens at time 0, which is a best practice
    start_time = min(cf[1] for cf in cash_flows)
    cash_flows_in_years = [(amount, (time - start_time) / time_divisor) for amount, time in cash_flows]

    # --- Use a robust solver with a single, wide bracket to find the IRR ---
    try:
        # We replace the conditional bracketing with one wide, safe range.
        # This allows the solver to find the IRR regardless of whether it's
        # highly positive or highly negative.
        return scipy.optimize.brentq(lambda r: _npv_x(r, cash_flows_in_years), -0.99999, 50.0) # Search between -99.999% and 5,000%
    except (ValueError, RuntimeError):
        # This will now only fail in the rare case a solution truly doesn't exist.
        return None


def get_nested_value(data: Dict[str, Any], path: List[str]) -> Any:
    try:
        return functools.reduce(lambda acc, key: acc[key] if isinstance(acc, dict) else getattr(acc, key), path, data)
    except (KeyError, AttributeError):
        return None


def set_nested_value(data: Dict[str, Any], path: List[str], value: Any):
    for key in path[:-1]:
        data = data[key] if isinstance(data, dict) else getattr(data, key)
    
    final_key = path[-1]
    if isinstance(data, dict):
        data[final_key] = value
    else:
        setattr(data, final_key, value)
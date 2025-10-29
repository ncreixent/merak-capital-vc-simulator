# tests/test_utils.py (Corrected expected IRR value)
import pytest
from types import SimpleNamespace

# Import the functions to be tested
from utils import xirr, get_nested_value, set_nested_value

# --- Tests for the xirr function ---

def test_xirr_standard_case():
    """
    Tests a simple, standard IRR calculation.
    Invest $100, get back $121 two years later should be a 10% annual IRR.
    """
    cash_flows = [(-100, 0), (121, 24)]
    result = xirr(cash_flows, time_unit='months')
    assert result == pytest.approx(0.10, abs=1e-4)

def test_xirr_negative_irr():
    """
    Tests a scenario that should result in a negative IRR.
    """
    cash_flows = [(-100, 0), (90, 12)] # Lost 10% in one year
    result = xirr(cash_flows, time_unit='months')
    assert result == pytest.approx(-0.10, abs=1e-4)

def test_xirr_more_complex_flows():
    """
    Tests with multiple inflows and outflows.
    """
    cash_flows = [(-100, 0), (-50, 12), (80, 24), (150, 36)]
    result = xirr(cash_flows, time_unit='months')
    # --- FIX: Updated the expected value to the correct IRR ---
    assert result == pytest.approx(0.2025, abs=1e-4)

def test_xirr_invalid_inputs():
    """
    Tests that xirr returns None for invalid cash flow patterns.
    """
    assert xirr([(-100, 0), (-50, 12)]) is None
    assert xirr([(100, 0), (50, 12)]) is None
    assert xirr([]) is None


# --- Tests for nested value helper functions ---

@pytest.fixture
def nested_test_data():
    """Provides a sample nested structure for testing."""
    return {
        'a': {
            'b': SimpleNamespace(c=100, d=[10, 20])
        },
        'x': 50
    }

def test_get_nested_value(nested_test_data):
    """
    Tests the get_nested_value function.
    """
    path_to_c = ['a', 'b', 'c']
    path_to_x = ['x']
    
    assert get_nested_value(nested_test_data, path_to_c) == 100
    assert get_nested_value(nested_test_data, path_to_x) == 50
    assert get_nested_value(nested_test_data, ['a', 'z']) is None

def test_set_nested_value(nested_test_data):
    """
    Tests the set_nested_value function.
    """
    path_to_c = ['a', 'b', 'c']
    path_to_x = ['x']

    set_nested_value(nested_test_data, path_to_c, 999)
    assert nested_test_data['a']['b'].c == 999

    set_nested_value(nested_test_data, path_to_x, 777)
    assert nested_test_data['x'] == 777
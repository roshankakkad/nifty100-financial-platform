import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

from analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    opm_mismatch,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage,
    interest_coverage_label,
    interest_coverage_warning,
    net_debt,
    asset_turnover,
)


def test_net_profit_margin_normal():
    assert net_profit_margin(20, 100) == 20


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(20, 0) is None


def test_operating_profit_margin_normal():
    assert operating_profit_margin(25, 100) == 25


def test_opm_cross_check_mismatch():
    assert opm_mismatch(25, 20) is True


def test_roe_normal():
    assert return_on_equity(50, 100, 400) == 10


def test_roe_negative_equity():
    assert return_on_equity(50, -200, 100) is None


def test_roce_normal():
    result = return_on_capital_employed(120, 20, 100, 300, 100)
    assert round(result, 2) == 20


def test_roa_normal():
    assert return_on_assets(50, 1000) == 5


def test_debt_to_equity_debt_free():
    assert debt_to_equity(0, 100, 400) == 0


def test_high_leverage_non_financial():
    assert high_leverage_flag(6, "Information Technology") is True


def test_high_leverage_financial_suppressed():
    assert high_leverage_flag(6, "Financials") is False


def test_interest_coverage_normal():
    assert interest_coverage(100, 20, 10) == 12


def test_interest_coverage_zero_interest():
    assert interest_coverage(100, 20, 0) is None


def test_interest_coverage_label_debt_free():
    assert interest_coverage_label(None) == "Debt Free"


def test_interest_warning():
    assert interest_coverage_warning(1.2) is True


def test_net_debt():
    assert net_debt(500, 200) == 300


def test_asset_turnover():
    assert asset_turnover(1000, 500) == 2


def test_asset_turnover_zero_assets():
    assert asset_turnover(1000, 0) is None
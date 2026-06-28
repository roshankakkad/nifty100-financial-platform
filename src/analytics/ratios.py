def safe_div(numerator, denominator):
    if denominator is None or denominator == 0:
        return None
    return numerator / denominator


def net_profit_margin(net_profit, sales):
    if sales == 0:
        return None
    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales):
    if sales == 0:
        return None
    return (operating_profit / sales) * 100


def opm_mismatch(computed_opm, source_opm):
    if computed_opm is None or source_opm is None:
        return False
    return abs(computed_opm - source_opm) > 1


def return_on_equity(net_profit, equity_capital, reserves):
    equity = equity_capital + reserves
    if equity <= 0:
        return None
    return (net_profit / equity) * 100


def return_on_capital_employed(operating_profit, depreciation, equity_capital, reserves, borrowings):
    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        return None

    ebit = operating_profit - depreciation
    return (ebit / capital_employed) * 100


def return_on_assets(net_profit, total_assets):
    if total_assets == 0:
        return None
    return (net_profit / total_assets) * 100


def debt_to_equity(borrowings, equity_capital, reserves):
    if borrowings == 0:
        return 0

    equity = equity_capital + reserves
    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(de_ratio, broad_sector):
    if de_ratio is None:
        return False

    if broad_sector == "Financials":
        return False

    return de_ratio > 5


def interest_coverage(operating_profit, other_income, interest):
    if interest == 0:
        return None
    return (operating_profit + other_income) / interest


def interest_coverage_label(icr):
    if icr is None:
        return "Debt Free"
    return ""


def interest_coverage_warning(icr):
    if icr is None:
        return False
    return icr < 1.5


def net_debt(borrowings, investments):
    return borrowings - investments


def asset_turnover(sales, total_assets):
    if total_assets == 0:
        return None
    return sales / total_assets
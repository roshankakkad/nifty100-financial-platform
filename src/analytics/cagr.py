def calculate_cagr(start_value, end_value, years):
    if years <= 0:
        return None, "INVALID_YEARS"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value > 0:
        cagr = (((end_value / start_value) ** (1 / years)) - 1) * 100
        return cagr, "NORMAL"

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    return None, "UNKNOWN"


def compute_metric_cagr(values, years):
    if len(values) < years + 1:
        return None, "INSUFFICIENT"

    start_value = values.iloc[0]
    end_value = values.iloc[-1]

    return calculate_cagr(start_value, end_value, years)
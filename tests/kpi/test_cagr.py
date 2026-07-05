from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

from analytics.cagr import calculate_cagr


def test_normal_cagr():
    value, flag = calculate_cagr(100, 200, 5)
    assert flag == "NORMAL"


def test_decline_to_loss():
    value, flag = calculate_cagr(100, -50, 5)
    assert flag == "DECLINE_TO_LOSS"


def test_turnaround():
    value, flag = calculate_cagr(-100, 50, 5)
    assert flag == "TURNAROUND"


def test_both_negative():
    value, flag = calculate_cagr(-100, -50, 5)
    assert flag == "BOTH_NEGATIVE"


def test_zero_base():
    value, flag = calculate_cagr(0, 100, 5)
    assert flag == "ZERO_BASE"
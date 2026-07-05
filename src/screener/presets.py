from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "src"))

from screener.engine import load_config, run_custom_screen


def presets():
    return load_config().get("presets", {})


def run_preset(name):
    cfg = presets()
    if name not in cfg:
        raise ValueError(f"unknown preset: {name}")
    return run_custom_screen(cfg[name])


def run_all_presets():
    out = {}
    for name in presets():
        df = run_preset(name)
        out[name] = df
        print(f"{name}: {df['company_id'].nunique()} companies")
    return out


if __name__ == "__main__":
    run_all_presets()

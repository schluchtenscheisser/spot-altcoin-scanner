import os
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
DATA_PATH = "./reports"   # Ordner mit deinen JSON-Reports
MIN_DAYS = 5               # Mindestens 5 Reports empfohlen
HORIZON = 2                # T+2 als Basis für Performance-Test

# ------------------------------------------------------------
# LOAD ALL REPORTS
# ------------------------------------------------------------
def load_reports(path):
    all_rows = []
    for file in sorted(os.listdir(path)):
        if not file.endswith(".json"):
            continue
        with open(os.path.join(path, file), "r") as f:
            data = json.load(f)
            date = data["meta"]["date"]
            for cat in ["reversals", "breakouts", "pullbacks"]:
                for setup in data["setups"].get(cat, []):
                    row = {
                        "date": date,
                        "symbol": setup["symbol"],
                        "category": cat,
                        "score": setup["score"],
                        "price": setup["price_usdt"]
                    }
                    # Komponenten flatten
                    comps = setup.get("components", {})
                    for k, v in comps.items():
                        row[f"comp_{k}"] = v
                    all_rows.append(row)
    df = pd.DataFrame(all_rows)
    df.sort_values(by=["symbol", "date"], inplace=True)
    return df

# ------------------------------------------------------------
# COMPUTE RETURNS (T+1, T+2, T+3)
# ------------------------------------------------------------
def compute_future_returns(df):
    for lag in [1, 2, 3]:
        df[f"price_t{lag}"] = df.groupby("symbol")["price"].shift(-lag)
        df[f"ret_t{lag}_pct"] = (df[f"price_t{lag}"] - df["price"]) / df["price"] * 100
    return df

# ------------------------------------------------------------
# ANALYSIS: CORRELATIONS + REGRESSION
# ------------------------------------------------------------
def analyze_components(df, horizon=2):
    target_col = f"ret_t{horizon}_pct"
    valid = df[df[target_col].notnull()].copy()

    component_cols = [c for c in df.columns if c.startswith("comp_")]
    corr = valid[component_cols + [target_col]].corr()[target_col].drop(target_col)

    X = valid[component_cols].fillna(0)
    y = valid[target_col].fillna(0)
    model = LinearRegression().fit(X, y)
    importance = pd.Series(model.coef_, index=component_cols)

    print("\n=== COMPONENT CORRELATIONS (vs Return T+%d) ===" % horizon)
    print(corr.sort_values(ascending=False))

    print("\n=== LINEAR REGRESSION COEFFICIENTS ===")
    print(importance.sort_values(ascending=False))

    # Optional Plot
    importance.sort_values().plot(kind="barh", figsize=(8,5))
    plt.title(f"Feature Importance for T+{horizon} Returns")
    plt.xlabel("Impact (Linear Coefficient)")
    plt.tight_layout()
    plt.show()

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    df = load_reports(DATA_PATH)
    if len(df["date"].unique()) < MIN_DAYS:
        print(f"⚠️ Only {len(df['date'].unique())} days detected. At least {MIN_DAYS} recommended.")
    else:
        df = compute_future_returns(df)
        analyze_components(df, horizon=HORIZON)

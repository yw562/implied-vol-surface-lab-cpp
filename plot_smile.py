import csv
from pathlib import Path
import sys
import math

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
observed_path = ROOT / "out" / "iv_observed.csv"
polyfit_path  = ROOT / "out" / "iv_poly_fit.csv"
out_png       = ROOT / "results" / "iv_smile_demo.png"

def read_csv(path, col_x, col_y):
    xs, ys = [], []
    with open(path, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                x = float(row[col_x])
                y = float(row[col_y])
                if math.isfinite(x) and math.isfinite(y):
                    xs.append(x); ys.append(y)
            except Exception:
                continue
    return xs, ys

def main():
    if not observed_path.exists() or not polyfit_path.exists():
        print(f"[ERR] Missing CSVs. Make sure you've run the C++ binary to produce:\n  {observed_path}\n  {polyfit_path}")
        sys.exit(1)

    K_obs, IV_obs = read_csv(observed_path, "Strike", "IV")
    K_fit, IV_fit = read_csv(polyfit_path,  "Strike", "IV_poly")

    if not K_obs or not K_fit:
        print("[ERR] Empty data. Check your CSV contents.")
        sys.exit(1)

    plt.figure(figsize=(7.5, 5.0), dpi=160)
    # 观察值用散点，拟合值用线
    plt.scatter(K_obs, IV_obs, s=18, alpha=0.85, label="Observed IV")
    plt.plot(K_fit, IV_fit, linewidth=2.0, label="Cubic Fit")

    plt.title("Implied Volatility Smile (Observed vs Polynomial Fit)")
    plt.xlabel("Strike")
    plt.ylabel("Implied Volatility")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png)
    print(f"[OK] Saved figure to: {out_png}")

if __name__ == "__main__":
    main()

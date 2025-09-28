# implied-vol-surface-lab

A mini quant research lab for building and stress-testing **implied volatility (IV) surfaces**.  
We go from Black–Scholes pricing and IV inversion to smile fitting (Polynomial vs SVI),  
no-arbitrage health checks, and parameter time-series stability.

![Smile demo](results/iv_smile_demo.png)

---

## 🔧 Usage

Clone and build:

```bash
git clone https://github.com/yw562/implied-vol-surface-lab-cpp.git
cd implied-vol-surface-lab-cpp

# Build the C++ binary
mkdir -p build && cd build
cmake ..
cmake --build . -j
Run the demo (sample quotes):

bash
Copy code
./iv_lab ../data/sample_quotes.csv 100 0.5 0.02 put
This writes IV inversion + polynomial fit to out/ (CSV), and Greeks to stdout.
Python scripts then visualize / extend the results:

bash
Copy code
python3 plot_smile.py
python3 plot_term_structure.py
python3 svi_fit.py --S 100 --T 0.5
python3 rolling_stability.py --S 100 --T 0.5 --r 0.02 --n 30
python3 rolling_stability_smoothed.py --S 100 --T 0.5 --r 0.02 --n 30 --alpha 0.2 --rho_step 0.05
python3 rolling_stability_controls.py --S 100 --T 0.5 --r 0.02 --n 30 --alpha 0.35 ...
📈 Mini Term Structure
ATM total variance vs maturity T.
Demonstrates how volatility scales with time.



🎯 SVI (single-expiry) demo
Parametric fit of the implied volatility smile using Stochastic Volatility Inspired (SVI).



⏱ Rolling stability (2-min cadence, simulated)
We simulate 30 time steps with mild perturbations and re-fit SVI each step.

Outputs:

results/svi_params_timeseries.png

data/svi_params_timeseries_example.csv

Key takeaways:

ATM IV is highly stable (CV < 1%).

b, σ are reasonably stable.

ρ (skew) is the jumpiest (wing asymmetry + parameter coupling).

Discrete butterfly QC passes (no arbitrage violations).

🪄 Rolling stability — smoothed controls
We add:

EMA smoothing (α=0.2).

ρ rate limit (±0.05 per step).

Result: CV reduction across parameters, ATM stays stable.

Artifacts:

results/svi_params_timeseries_smoothed.png

data/svi_params_timeseries_smoothed_example.csv

🕹 Controls tuning (single-expiry)
Multi-parameter rate limits + fallback-to-last-good dropped fallbacks to 5/30.

CVs stay low; ρ still most volatile (expected from skew sensitivity).

Artifact: results/svi_params_timeseries_controls.png

Example CSV: data/svi_params_timeseries_controls_example.csv

🔒 Stability Tuning
Raw SVI updates can be noisy, esp. for ρ (skew) and m (shift).
We introduced two stabilizers:

Regularization: stronger prior on ρ, light anchor on m.

Fallback logic: revert to last good state only when both loss and violation conditions trigger.

Results:

Raw → EMA CV dropped sharply (e.g. ρ: 2.15 → 0.0148).

Fallbacks moderate (~5/30).

Skew volatility reduced; other params (a, b, σ) remain stable.

Mimics production-style calibration: stability as important as fit quality.



CV Comparison
Parameter	Raw CV	EMA CV
a	0.64	0.246
b	0.212	0.0421
ρ (rho)	2.15	0.0148
m	0.608	0.114
σ (sigma)	0.226	0.0716

ρ jitter: 2.15 → 0.0148 (huge improvement).

Other params also smoother while preserving fit.

Fallbacks ~5/30 → balanced (not too strict, not too loose).

🧠 What we learned
How to invert prices to IV and fit both polynomial and SVI smiles.

How to run basic no-arbitrage checks (butterfly convexity).

How parameters behave over time and why stability tuning matters in production.

How to balance fit accuracy vs robustness with priors, smoothing, and fallback logic.

🚀 Next extensions
Fit full term structure with SVI or SABR.

Add real market data ingestion.

Integrate C++ ↔ Python pipeline for performance + visualization.

Stress-test under extreme skew / jump conditions.

yaml
Copy code

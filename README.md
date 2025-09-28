# implied-vol-surface-lab
A mini quant research lab for building and stress-testing implied volatility surfaces: from Black–Scholes pricing and IV inversion to smile fitting (Polynomial vs SVI), no-arbitrage health checks, and parameter time-series stability.
![Smile demo](results/iv_smile_demo.png)

## Mini Term Structure

![ATM total variance vs T](results/atm_variance_vs_maturity.png)

## SVI (single-expiry) demo

![SVI fit](results/iv_svi_fit.png)

## Rolling stability (2-min cadence, simulated)

We simulate 30 time steps with mild wing/ATM perturbations and re-fit SVI each step.
Outputs:
- `results/svi_params_timeseries.png`
- `data/svi_params_timeseries_example.csv` (example)

Key takeaways in our demo:
- **ATM IV is highly stable** (CV < 1%).
- **b, σ** are reasonably stable; **ρ** is the jumpiest (wing asymmetry + parameter coupling).
- **Discrete butterfly QC** on reconstructed call prices passes (no violations).


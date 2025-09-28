# implied-vol-surface-lab
A mini quant research lab for building and stress-testing implied volatility surfaces: from Black–Scholes pricing and IV inversion to smile fitting (Polynomial vs SVI), no-arbitrage health checks, and parameter time-series stability.
![Smile demo](results/iv_smile_demo.png)

# Run a demo with sample quotes
./iv_lab ../data/sample_quotes.csv 100 0.5 0.02 put

# Plot results with Python
python3 plot_smile.py
python3 plot_term_structure.py
python3 svi_fit.py --S 100 --T 0.5
python3 rolling_stability.py --S 100 --T 0.5 --r 0.02 --n 30
python3 rolling_stability_smoothed.py --S 100 --T 0.5 --r 0.02 --n 30 --alpha 0.2 --rho_step 0.05
python3 rolling_stability_controls.py --S 100 --T 0.5 --r 0.02 --n 30 --alpha 0.35 ...


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


## Rolling stability — smoothed controls
We add EMA smoothing (α=0.2) and a per-step rate limit on ρ (±0.05).
Result: substantial CV reduction across parameters while ATM stays stable.
Artifacts:
- `results/svi_params_timeseries_smoothed.png`
- `data/svi_params_timeseries_smoothed_example.csv`

### Controls tuning (single-expiry)
- Multi-parameter rate-limits + fallback-to-last-good dropped fallbacks to **5/30**.
- CVs stay low; **ρ remains the most volatile** parameter → expected due to skew sensitivity.
- Artifact: `results/svi_params_timeseries_controls.png`, CSV: `data/svi_params_timeseries_controls_example.csv`.

## Stability Tuning

In practice, raw SVI parameter updates can be noisy, especially for skew (ρ) and shift (m).  
We introduced two stabilization techniques:

1. **Regularization:** a stronger prior on ρ (and a light anchor on m) to prevent erratic jumps.  
2. **Fallback logic:** only revert to the last good state when both loss and violation conditions are triggered.

**Results:**  
- Raw → EMA coefficient of variation (CV) dropped significantly (e.g. ρ: 2.15 → 0.0148 in the controlled run).  
- Fallbacks remained moderate (~5 out of 30 steps).  
- Skew volatility was markedly reduced, while other parameters (a, b, σ) stayed stable.

This tuning mimics production-style calibration, where stability is as important as fit quality.

![Stability controls](results/svi_params_timeseries_controls.png)


### Stability Tuning: CV Comparison

| Parameter | Raw CV | EMA CV |
|-----------|--------|--------|
| a         | 0.64   | 0.246  |
| b         | 0.212  | 0.0421 |
| ρ (rho)   | 2.15   | 0.0148 |
| m         | 0.608  | 0.114  |
| σ (sigma) | 0.226  | 0.0716 |

- **ρ jitter** 2.15 → 0.0148 (biggest improvement).
- Other parameters smoother while preserving fit accuracy. 
- Fallbacks limited to ~5/30 → calibration robust without over-correction. 
> > **Note:**
> The fallback count (≈5/30) indicates that only a handful of calibration steps required rolling back to the last good parameter set.
> > This mimics production-style workflows where stability is as critical as fit accuracy:
> > too few fallbacks → risk of unstable fits slipping through;
> > too many fallbacks → model becomes over-constrained.
> > Around 5/30 is a healthy balance.

## What we learned
- How to invert market option prices into implied volatilities.
- How to fit Polynomial vs SVI smiles and check arbitrage constraints.
- How to evaluate parameter stability across a rolling time series.
- Why stability tuning (priors, EMA smoothing, fallbacks) is critical in practice.
- Practical skills in C++ model prototyping and Python visualization for quant research.

## What we learned
- Extend from single-expiry to a full term structure (SVI / SABR).
- Add real market option data ingestion.
- Explore production-style calibration pipelines with robust monitoring.
- Stress-test under extreme skew / jump scenarios.


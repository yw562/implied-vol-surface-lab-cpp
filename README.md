
# implied-vol-surface-lab-cpp

A minimal C++ lab for option smile modeling.  
Currently implemented:

- **Black–Scholes pricing** (calls & puts)
- **Price → Implied Volatility inversion** (Brent root-finding)
- **Single-maturity cubic polynomial smile fit**
- **Greeks calculation** (for validation / sanity checks)
- **CSV I/O** for quotes and outputs

This is the foundation for building a research toolkit around implied volatility surfaces, with a focus on *practical reproducibility* and *step-by-step extensions*.

---

## 🔧 Build & Run

### Requirements
- CMake ≥ 3.12  
- C++17 compiler (tested with AppleClang 17 on macOS)

### Build
```bash
git clone https://github.com/yw562/implied-vol-surface-lab-cpp.git
cd implied-vol-surface-lab-cpp
mkdir -p build && cd build
cmake ..
cmake --build . -j
Run
Example (using sample quotes provided):

bash
Copy code
./iv_lab ../data/sample_quotes.csv 100 0.5 0.02 put
Arguments:

<csv_path> – path to input quotes

<S> – current underlying spot price

<T_years> – time to maturity in years (e.g. 0.5 for 6 months)

<r_rate> – risk-free rate (as decimal, e.g. 0.02 for 2%)

<type> – "call" or "put"

📂 Input Format
CSV with columns:

arduino
Copy code
Strike,LastPrice,Type
80,22.10,put
90,14.80,put
95,11.20,put
...
Strike: option strike

LastPrice: observed market option price

Type: "call" or "put"

📂 Outputs
When you run the program, it generates CSV files under out/:

iv_observed.csv

Columns: Strike,IV

Implied volatilities obtained by inverting BS prices.

iv_poly_fit.csv

Columns: Strike,IV_poly

Cubic polynomial fit of the smile.

Console also prints:

Confirmation messages ([OK] wrote out/...)

A sample calculation of ATM Greeks for validation.

📊 Example Usage
bash
Copy code
./iv_lab ../data/sample_quotes.csv 100 0.5 0.02 put
Produces:

out/iv_observed.csv (raw IVs)

out/iv_poly_fit.csv (smile fit)

These can be plotted in Excel/Numbers/Python.
Example visualization:

Blue dots: observed IV (from prices)

Orange line: cubic polynomial fit

🚀 Next Steps (Planned Extensions)
Add basic health checks (butterfly convexity proxies, outlier filters)

Extend to multi-expiry term structure (ATM total variance vs maturity)

Implement SVI parameterization with simple optimizers

Small event studies (e.g. pre/post earnings skew changes)

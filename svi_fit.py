import csv, math, random
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent

def load_observed(path):
    Ks, IVs = [], []
    with open(path, newline='') as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            f.seek(0)
            for row in csv.reader(f):
                if len(row) >= 2:
                    Ks.append(float(row[0])); IVs.append(float(row[1]))
        else:
            for row in r:
                Ks.append(float(row["Strike"]))
                IVs.append(float(row["IV"]))
    z = sorted(zip(Ks, IVs))
    return [k for k,_ in z], [v for _,v in z]

def svi_w(k,a,b,rho,m,sig):
    return a + b*( rho*(k-m) + math.sqrt( (k-m)**2 + sig**2 ) )

def loss(params, ks, w_obs):
    a,b,rho,m,sig = params
    if b<=1e-8 or abs(rho)>=0.999 or sig<=1e-6 or a<=1e-10:
        return 1e100
    se = 0.0
    for k, w in zip(ks, w_obs):
        wp = svi_w(k,a,b,rho,m,sig)
        se += (wp - w)**2
    se += 1e-4*(a*a + b*b + m*m + sig*sig) + 1e-4*(rho*rho)
    return se

def fit_svi(ks, w_obs, n_restart=30, iters=400):
    kmin, kmax = min(ks), max(ks)
    wbar = sum(w_obs)/len(w_obs)
    best = None
    for _ in range(n_restart):
        a  = max(1e-6, 0.5*wbar)
        b  = random.uniform(0.01, 2.0)
        rho= random.uniform(-0.8, 0.8)
        m  = random.uniform(kmin*0.5, kmax*0.5)
        sig= random.uniform(0.05, 0.8)
        p = [a,b,rho,m,sig]
        cur = loss(p, ks, w_obs)
        step = [x*0.2 for x in [a or 1e-2, b, 0.2, (kmax-kmin+1e-3), sig]]
        for it in range(iters):
            i = random.randrange(5)
            trial = p[:]
            trial[i] += random.uniform(-1,1)*step[i]
            val = loss(trial, ks, w_obs)
            if val < cur or random.random() < 0.05:
                p, cur = trial, val
            if (it+1)%80==0: step = [s*0.5 for s in step]
        if best is None or cur < best[0]:
            best = (cur, p)
    return best[1]

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--S", type=float, required=True)
    ap.add_argument("--T", type=float, required=True)
    ap.add_argument("--in_csv", default=str(ROOT/"out"/"iv_observed.csv"))
    args = ap.parse_args()

    Ks, IVs = load_observed(args.in_csv)
    ks = [math.log(K/args.S) for K in Ks]
    w_obs = [(iv**2)*args.T for iv in IVs]

    params = fit_svi(ks, w_obs)
    a,b,rho,m,sig = params
    print("[SVI] a=%.6f b=%.6f rho=%.4f m=%.6f sigma=%.6f"%(a,b,rho,m,sig))

    w_fit = [svi_w(k,a,b,rho,m,sig) for k in ks]
    iv_fit = [math.sqrt(max(1e-12,w)/args.T) for w in w_fit]
    out_csv = ROOT/"out"/"iv_svi_fit.csv"
    with open(out_csv, "w", newline='') as f:
        w = csv.writer(f); w.writerow(["Strike","IV_svi"])
        for K, iv in zip(Ks, iv_fit): w.writerow([K, iv])
    print(f"[OK] wrote {out_csv}")

    plt.figure(figsize=(7.2,4.6), dpi=160)
    plt.scatter(Ks, IVs, s=18, alpha=0.85, label="Observed IV")
    plt.plot(Ks, iv_fit, linewidth=2.0, label="SVI fit")
    plt.title("SVI fit vs Observed IV")
    plt.xlabel("Strike"); plt.ylabel("Implied Volatility")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    plt.legend(); plt.tight_layout()
    out_png = ROOT/"results"/"iv_svi_fit.png"
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png)
    print(f"[OK] saved {out_png}")

if __name__ == "__main__":
    random.seed(42)
    main()

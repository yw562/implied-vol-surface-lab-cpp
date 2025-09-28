import csv, math, random
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
random.seed(123)

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

def bs_call(S,K,T,r,sigma):
    if sigma<=0 or T<=0: return max(0.0, S - K*math.exp(-r*T))
    d1=(math.log(S/K)+(r+0.5*sigma*sigma)*T)/(sigma*math.sqrt(T))
    d2=d1 - sigma*math.sqrt(T)
    Nx = 0.5*(1+math.erf(d1/math.sqrt(2))); Ny = 0.5*(1+math.erf(d2/math.sqrt(2)))
    return S*Nx - K*math.exp(-r*T)*Ny

# --- SVI ---
def svi_w(k,a,b,rho,m,sig): return a + b*( rho*(k-m) + math.sqrt((k-m)**2 + sig**2) )

def svi_loss(p, ks, w_obs):
    a,b,rho,m,sig = p
    if b<=1e-8 or abs(rho)>=0.999 or sig<=1e-6 or a<=1e-10: return 1e100
    se=0.0
    for k,w in zip(ks,w_obs):
        wp = svi_w(k,a,b,rho,m,sig); se += (wp-w)**2
    se += 1e-4*(a*a + b*b + m*m + sig*sig) + 1e-4*(rho*rho)
    return se

def fit_svi(ks, w_obs, n_restart=20, iters=300):
    kmin, kmax = min(ks), max(ks); wbar = sum(w_obs)/len(w_obs)
    best=None
    for _ in range(n_restart):
        a  = max(1e-6, 0.5*wbar); b  = random.uniform(0.02, 1.5)
        rho= random.uniform(-0.8, 0.8); m  = random.uniform(kmin*0.5, kmax*0.5)
        sig= random.uniform(0.05, 0.6)
        p=[a,b,rho,m,sig]; cur=svi_loss(p,ks,w_obs)
        step=[x*0.2 for x in [a or 1e-2, b, 0.2, (kmax-kmin+1e-3), sig]]
        for it in range(iters):
            i = random.randrange(5); trial=p[:]; trial[i]+=random.uniform(-1,1)*step[i]
            val=svi_loss(trial,ks,w_obs)
            if val<cur or random.random()<0.05: p,cur=trial,val
            if (it+1)%80==0: step=[s*0.5 for s in step]
        if best is None or cur<best[0]: best=(cur,p)
    return best[1]

def make_rolls(Ks, IVs, n=30):
    S=100.0; xs=[k/S-1.0 for k in Ks]; out=[]
    for _ in range(n):
        drift=0.001*random.uniform(-1,1)
        left =0.015*random.uniform(-1,1)
        right=0.008*random.uniform(-1,1)
        curve=[]
        for x,iv in zip(xs,IVs):
            wing = left*max(0,-x) + right*max(0,x)
            noise= random.gauss(0, 0.002)
            iv_t = max(0.05, iv*(1.0+drift) + wing + noise)
            curve.append(iv_t)
        out.append(curve)
    return out

def butterfly_violations_call_prices(Ks, IVs, S, T, r):
    C=[bs_call(S,K,T,r,iv) for K,iv in zip(Ks,IVs)]
    bad=0
    for i in range(1,len(C)-1):
        if C[i-1] - 2*C[i] + C[i+1] < -1e-8: bad+=1
    return bad

def ema(prev, x, alpha): return (1-alpha)*prev + alpha*x

def main():
    import argparse, statistics as st
    ap=argparse.ArgumentParser()
    ap.add_argument("--S", type=float, default=100.0)
    ap.add_argument("--T", type=float, default=0.5)
    ap.add_argument("--r", type=float, default=0.02)
    ap.add_argument("--in_csv", default=str(ROOT/"out"/"iv_observed.csv"))
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--alpha", type=float, default=0.2, help="EMA smoothing weight")
    ap.add_argument("--rho_step", type=float, default=0.05, help="max per-step |Δrho|")
    args=ap.parse_args()

    Ks, IV0 = load_observed(args.in_csv); ks=[math.log(K/args.S) for K in Ks]
    w0=[(iv**2)*args.T for iv in IV0]
    p0=fit_svi(ks,w0); print("[t=0] SVI:", p0)

    curves=make_rolls(Ks,IV0,n=args.n)

    rows=[["t","a","b","rho","m","sigma","ATM_IV","viol",
           "a_ema","b_ema","rho_ema","m_ema","sigma_ema","rho_clipped"]]
    series={k:[] for k in ["a","b","rho","m","sigma","ATM_IV","viol",
                            "a_ema","b_ema","rho_ema","m_ema","sigma_ema","rho_clip_cnt"]}

    a_e,b_e,rho_e,m_e,sig_e = p0; rho_clip_cnt=0

    for t,IVt in enumerate(curves,1):
        w_obs=[(iv**2)*args.T for iv in IVt]
        a,b,rho,m,sig = fit_svi(ks, w_obs)

        # 线性插值 ATM
        def iv_atm():
            for i in range(len(Ks)-1):
                if (Ks[i]<=args.S<=Ks[i+1]) or (Ks[i+1]<=args.S<=Ks[i]):
                    k1,k2=Ks[i],Ks[i+1]; iv1,iv2=IVt[i],IVt[i+1]
                    t_=(args.S-k1)/(k2-k1); return iv1 + t_*(iv2-iv1)
            return IVt[min(range(len(Ks)), key=lambda i: abs(Ks[i]-args.S))]
        atm = iv_atm()
        viol= butterfly_violations_call_prices(Ks,IVt,args.S,args.T,args.r)

        # --- ρ 限幅 + EMA 平滑 ---
        rho_raw = rho
        # 限幅：每步最多变 args.rho_step
        rho_low, rho_high = rho_e - args.rho_step, rho_e + args.rho_step
        if rho < rho_low: rho = rho_low; rho_clip_cnt += 1
        elif rho > rho_high: rho = rho_high; rho_clip_cnt += 1
        # EMA
        a_e   = ema(a_e,   a,   args.alpha)
        b_e   = ema(b_e,   b,   args.alpha)
        rho_e = ema(rho_e, rho, args.alpha)
        m_e   = ema(m_e,   m,   args.alpha)
        sig_e = ema(sig_e, sig, args.alpha)

        rows.append([t,a,b,rho_raw,m,sig,atm,viol, a_e,b_e,rho_e,m_e,sig_e,rho_clip_cnt])

        series["a"].append(a); series["b"].append(b); series["rho"].append(rho_raw)
        series["m"].append(m); series["sigma"].append(sig); series["ATM_IV"].append(atm); series["viol"].append(viol)
        series["a_ema"].append(a_e); series["b_ema"].append(b_e); series["rho_ema"].append(rho_e)
        series["m_ema"].append(m_e); series["sigma_ema"].append(sig_e); series["rho_clip_cnt"].append(rho_clip_cnt)

    # 写 CSV
    out_csv = ROOT/"out"/"svi_params_timeseries_smoothed.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv,"w",newline="") as f: csv.writer(f).writerows(rows)
    print(f"[OK] wrote {out_csv}")

    # 画对比图
    t = list(range(1,len(series["a"])+1))
    plt.figure(figsize=(9,5.2), dpi=160)
    for key, key_e in [("a","a_ema"),("b","b_ema"),("rho","rho_ema"),("m","m_ema"),("sigma","sigma_ema")]:
        plt.plot(t, series[key], label=f"{key} raw", linewidth=1.0)
        plt.plot(t, series[key_e], label=f"{key} EMA", linewidth=2.0)
    plt.xlabel("time steps (~2-min cadence simulated)")
    plt.title("SVI params — raw vs EMA (+ rho rate limit)")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    plt.legend(ncol=3, fontsize=9)
    out_png = ROOT/"results"/"svi_params_timeseries_smoothed.png"
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(out_png)
    print(f"[OK] saved {out_png}")

    # 摘要
    def summary(arr):
        import statistics as st
        mu = st.fmean(arr); sd = st.pstdev(arr) if len(arr)>1 else 0.0
        cv = sd/abs(mu) if abs(mu)>1e-12 else float('inf')
        return mu,sd,cv
    for name in ["a","b","rho","m","sigma"]:
        mu_raw,sd_raw,cv_raw = summary(series[name])
        mu_e, sd_e, cv_e     = summary(series[name+"_ema"])
        print(f"[STAB] {name:5s}  raw CV={cv_raw:.3g}  ->  EMA CV={cv_e:.3g}")
    print(f"[QC] rho clipped times = {series['rho_clip_cnt'][-1]}")

if __name__ == "__main__":
    main()

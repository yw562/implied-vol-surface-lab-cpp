import csv, math, random, statistics as st
from pathlib import Path

# === simplified svi_loss with regularization ===
def svi_loss(params, k_arr, iv_arr):
    a, b, rho, m, sig = params
    se = 0.0
    for k, iv in zip(k_arr, iv_arr):
        x = k - m
        w = a + b * (rho * x + (x*x + sig*sig)**0.5)
        if w <= 1e-12:
            w = 1e-12
        model_iv = w**0.5
        se += (model_iv - iv)**2

    # 强化正则：rho 更重，m 轻锚定
    lambda_core = 1e-4
    lambda_rho  = 6e-4
    lambda_m    = 2e-4
    se += lambda_core*(a*a + b*b + sig*sig) + lambda_rho*(rho*rho) + lambda_m*(m*m)
    return se
# (注意：你原来的脚本 rolling_stability_controls.py 里除了这个函数，
# 还有 main loop, 参数更新, 输出 CSV 和画图的逻辑 —— 记得保留！
# 我这里只给出 svi_loss 的新版本，直接替换原函数。)

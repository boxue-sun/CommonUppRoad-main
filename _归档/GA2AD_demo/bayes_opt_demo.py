# -*- coding: utf-8 -*-
"""
贝叶斯优化 demo（纯 numpy + sklearn，秒跑）

演示核心思路：把「找最危险场景」当成「在未知风险函数上找最大值」，
用高斯过程(GP)代理模型 + 期望提升(EI) acquisition function，
用尽量少的查询次数逼近最大值 —— 对比 随机搜索 / 网格穷举。

风险函数模拟你 close_range 实验的规律：车距越小 + ego 越快 → 越危险。
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from scipy.stats import norm

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

GAP_MIN, GAP_MAX = 2.0, 50.0
V_MIN, V_MAX = 10.0, 30.0


def true_risk(gap, v_ego):
    """真实(未知)风险函数：低车距 + 高速度 → 高风险。最大约 0.85 在 (2,30) 角。"""
    f_gap = 1.0 / (1.0 + np.exp((gap - 15.0) / 4.0))
    f_v = 1.0 / (1.0 + np.exp(-(v_ego - 18.0) / 6.0))
    return f_gap * f_v


def make_pool(n=60):
    g = np.linspace(GAP_MIN, GAP_MAX, n)
    v = np.linspace(V_MIN, V_MAX, n)
    GG, VV = np.meshgrid(g, v)
    return np.c_[GG.ravel(), VV.ravel()], GG, VV


def gp_model():
    kernel = ConstantKernel(1.0, (1e-3, 1e3)) * RBF([8.0, 4.0], (1e-2, 1e2)) \
        + WhiteKernel(1e-3, (1e-6, 1e-1))
    return GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                    n_restarts_optimizer=2, random_state=0)


def ei(mu, std, y_best):
    with np.errstate(divide='ignore'):
        z = (mu - y_best) / (std + 1e-9)
        val = (mu - y_best) * norm.cdf(z) + std * norm.pdf(z)
        val[std < 1e-9] = 0.0
    return val


def run_bo(pool, budget=30, init=3, seed=0):
    np.random.seed(seed)
    idx_sampled = list(np.random.choice(len(pool), init, replace=False))
    X = pool[idx_sampled]
    y = true_risk(X[:, 0], X[:, 1])
    best_hist = [y.max()]
    for _ in range(budget - init):
        gp = gp_model().fit(X, y)
        mu, std = gp.predict(pool, return_std=True)
        acq = ei(mu, std, y.max())
        # 选没采样过的点里 EI 最大的
        acq[idx_sampled] = -np.inf
        nxt = int(np.argmax(acq))
        idx_sampled.append(nxt)
        X = np.vstack([X, pool[nxt]])
        y = np.append(y, true_risk(pool[nxt, 0], pool[nxt, 1]))
        best_hist.append(y.max())
    return np.array(best_hist), X, y


def run_random(budget=30, seed=0):
    np.random.seed(seed)
    pts = np.random.uniform([GAP_MIN, V_MIN], [GAP_MAX, V_MAX], size=(budget, 2))
    y = true_risk(pts[:, 0], pts[:, 1])
    return np.maximum.accumulate(y), pts


def run_grid(n_gap=6, n_v=5):
    g = np.linspace(GAP_MIN, GAP_MAX, n_gap)
    v = np.linspace(V_MIN, V_MAX, n_v)
    GG, VV = np.meshgrid(g, v)
    pts = np.c_[GG.ravel(), VV.ravel()]
    y = true_risk(pts[:, 0], pts[:, 1])
    return np.maximum.accumulate(y), pts


# ---- 主流程 ----
pool, GG, VV = make_pool()
budget = 30

# 多次平均，去掉随机性
N_RUN = 10
bo_all = [run_bo(pool, budget, seed=s)[0] for s in range(N_RUN)]
bo_mean = np.mean(bo_all, axis=0)
rand_all = [run_random(budget, seed=s)[0] for s in range(N_RUN)]
rand_mean = np.mean(rand_all, axis=0)

grid_hist, grid_pts = run_grid()
# 网格只有 30 个点，累积曲线长度=30
grid_x = np.arange(1, len(grid_hist) + 1)

# 单条 BO 轨迹（画采样点用）
bo_hist, bo_X, bo_y = run_bo(pool, budget, seed=1)

print("=== 30 次查询后找到的最高风险（越大越好，最大约 0.85）===")
print(f"  网格穷举:        {grid_hist[-1]:.3f}")
print(f"  随机搜索(均值):   {rand_mean[-1]:.3f}")
print(f"  贝叶斯优化(均值): {bo_mean[-1]:.3f}  <- GA2AD/彭老师方向")
print(f"  贝叶斯优化(最优): {max(run_bo(pool, budget, seed=s)[0][-1] for s in range(20)):.3f}")
print(f"\n  达到风险 0.70 所需查询次数:  随机~{np.argmax(rand_mean >= 0.70)+1 if (rand_mean>=0.70).any() else '>30'}  贝叶斯~{np.argmax(bo_mean >= 0.70)+1 if (bo_mean>=0.70).any() else '>30'}")

# ---- 画图 ----
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))

ax = axes[0]
risk = true_risk(GG, VV)
cf = ax.contourf(GG, VV, risk, levels=20, cmap='RdYlGn_r')
ax.scatter(bo_X[:, 0], bo_X[:, 1], c='black', s=22, marker='o',
           edgecolors='white', linewidths=0.4, zorder=5, label='贝叶斯优化采样点')
ax.set_xlabel('车距 (m)'); ax.set_ylabel('ego 速度 (m/s)')
ax.set_title('真实风险地形 + 贝叶斯优化采样点（黑点）')
fig.colorbar(cf, ax=ax, label='风险')
ax.legend(loc='upper right', fontsize=8)

ax = axes[1]
ax.plot(np.arange(1, budget+1), bo_mean, 'o-', color='#E74C3C', lw=2, label='贝叶斯优化')
ax.plot(np.arange(1, budget+1), rand_mean, 's--', color='#2E86C1', lw=1.8, label='随机搜索')
ax.plot(grid_x, grid_hist, '^-', color='#95A5A6', lw=1.5, label='网格穷举')
ax.axhline(0.85, color='gray', ls=':', lw=1)
ax.text(budget-2, 0.855, '理论最大值 0.85', fontsize=8, ha='right')
ax.set_xlabel('查询次数（每次=一次 UPPAAL 验证）')
ax.set_ylabel('已找到的最高风险')
ax.set_title(f'{N_RUN} 次平均：贝叶斯优化更少查询找到危险区')
ax.legend(); ax.grid(alpha=0.3)

plt.tight_layout()
out = r"d:\3study\zh\_归档\GA2AD_demo\bayes_opt_demo.png"
plt.savefig(out, dpi=120)
print("\n图已保存:", out)

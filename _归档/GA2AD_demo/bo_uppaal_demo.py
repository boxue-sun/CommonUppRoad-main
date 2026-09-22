# -*- coding: utf-8 -*-
"""
贝叶斯优化 + UPPAAL 对抗场景搜索（mock 版，3 维参数空间）

参数空间（3 维）：初始距离 gap、自车初速度 v_ego、障碍物初速度 v_obs
优化目标：最大化碰撞风险（找到最危险的场景）

闭环（每轮迭代）：
  ① 代理模型 GP：用已有样本预测全空间风险 + 不确定性
  ② 采集函数 EI：平衡开发/探索，选出「最有潜力出碰撞」的候选参数
  ③ UPPAAL 真值校验：候选参数送 UPPAAL，拿到确定性「是否碰撞可达 + 风险值」
  ④ 加入数据集，循环，直到 UPPAAL 调用预算用完

和现有贝叶斯优化自动驾驶论文的区别：
  别人评估器 = CARLA 仿真（随机、不可证明）；这里评估器 = UPPAAL（确定性，可数学证明碰撞路径可达）。
  贝叶斯优化只负责提升搜索效率，完备性完全来自 UPPAAL。
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

# ---- 三维参数空间 ----
GAP = (3.0, 50.0)     # 初始距离 gap (m)
VEGO = (10.0, 30.0)   # 自车初速度 v_ego (m/s)
VOBS = (0.0, 25.0)    # 障碍物初速度 v_obs (m/s)
BOUNDS = np.array([GAP, VEGO, VOBS])
COLLISION_THRESHOLD = 0.5


def mock_uppaal(x):
    """mock 版 UPPAAL oracle：确定性返回碰撞风险 0~1。

    规则对齐真实 ISO 15622 实验规律：车距小 × ego 快 × 障碍物慢 → 危险。
    （真实 UPPAAL 返回「碰撞路径是否可达」这个确定真值；这里用连续风险值
      便于 GP 拟合，>0.5 判为碰撞。）"""
    gap, v_ego, v_obs = x
    closing = v_ego - v_obs
    if closing <= 0:
        return 0.0
    f_gap = 1.0 / (1.0 + np.exp((gap - 13.0) / 2.5))   # 车距小 → 危险
    f_ego = 1.0 / (1.0 + np.exp(-(v_ego - 20.0) / 6.0))  # ego 快 → 危险
    f_obs = 1.0 / (1.0 + np.exp((v_obs - 10.0) / 6.0))   # 障碍物慢 → 危险
    return float(f_gap * f_ego * f_obs)


def make_pool(n=40):
    g = np.linspace(GAP[0], GAP[1], n)
    v = np.linspace(VEGO[0], VEGO[1], n)
    o = np.linspace(VOBS[0], VOBS[1], n)
    GG, VV, OO = np.meshgrid(g, v, o, indexing='ij')
    return np.c_[GG.ravel(), VV.ravel(), OO.ravel()]


def gp_model():
    kernel = ConstantKernel(1.0, (1e-3, 1e3)) \
        * RBF([6.0, 5.0, 5.0], (1e-2, 1e2)) + WhiteKernel(1e-3, (1e-6, 1e-1))
    return GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                    n_restarts_optimizer=2, random_state=0)


def ei(mu, std, y_best):
    with np.errstate(divide='ignore'):
        z = (mu - y_best) / (std + 1e-9)
        val = (mu - y_best) * norm.cdf(z) + std * norm.pdf(z)
        val[std < 1e-9] = 0.0
    return val


def run_bo(pool, budget=40, init=5, seed=0):
    np.random.seed(seed)
    idx = list(np.random.choice(len(pool), init, replace=False))
    X = pool[idx]
    y = np.array([mock_uppaal(x) for x in X])           # ① 初始样本 → UPPAAL 拿真值
    coll_hist = list(np.cumsum(y > COLLISION_THRESHOLD))   # 每个初始样本后累计碰撞数
    best_hist = list(np.maximum.accumulate(y))
    for _ in range(budget - init):
        gp = gp_model().fit(X, y)                        # ② 代理模型 GP 预测
        mu, std = gp.predict(pool, return_std=True)
        acq = ei(mu, std, y.max())                       # ③ EI 采集函数选点
        acq[idx] = -np.inf
        nxt = int(np.argmax(acq))
        y_nxt = mock_uppaal(pool[nxt])                   # ④ UPPAAL 形式化真值校验
        idx.append(nxt)
        X = np.vstack([X, pool[nxt]])
        y = np.append(y, y_nxt)
        coll_hist.append(coll_hist[-1] + (y_nxt > COLLISION_THRESHOLD))
        best_hist.append(max(best_hist[-1], y_nxt))
    return np.array(coll_hist), np.array(best_hist), X, y


def run_random(budget=40, seed=0):
    np.random.seed(seed)
    pts = np.random.uniform(BOUNDS[:, 0], BOUNDS[:, 1], size=(budget, 3))
    y = np.array([mock_uppaal(x) for x in pts])
    coll = np.cumsum(y > COLLISION_THRESHOLD)
    best = np.maximum.accumulate(y)
    return coll, best, pts


def run_grid(n=5):
    g = np.linspace(GAP[0], GAP[1], n)
    v = np.linspace(VEGO[0], VEGO[1], n)
    o = np.linspace(VOBS[0], VOBS[1], n)
    GG, VV, OO = np.meshgrid(g, v, o, indexing='ij')
    pts = np.c_[GG.ravel(), VV.ravel(), OO.ravel()]
    y = np.array([mock_uppaal(x) for x in pts])
    coll = np.cumsum(y > COLLISION_THRESHOLD)
    best = np.maximum.accumulate(y)
    return coll, best, pts


# ---- 主流程 ----
pool = make_pool()
budget = 40
N_RUN = 10

bo_coll = np.mean([run_bo(pool, budget, seed=s)[0] for s in range(N_RUN)], axis=0)
rand_coll = np.mean([run_random(budget, seed=s)[0] for s in range(N_RUN)], axis=0)
grid_coll, grid_best, grid_pts = run_grid(5)   # 5x5x5=125 个网格点

# 一条 BO 轨迹，画采样点
bo_coll1, bo_best1, bo_X, bo_y = run_bo(pool, budget, seed=1)
is_coll = bo_y > COLLISION_THRESHOLD

print("=== 预算 %d 次 UPPAAL 调用，找到的碰撞场景数 ===" % budget)
print(f"  随机搜索(均值):   {rand_coll[-1]:.1f} 个碰撞")
print(f"  网格穷举(125点):  {grid_coll[-1]:.1f} 个碰撞（需测满全空间）")
print(f"  贝叶斯优化(均值): {bo_coll[-1]:.1f} 个碰撞  <- 本方法")

def first_reach(hist, k):
    hit = np.where(hist >= k)[0]
    return int(hit[0] + 1) if hit.size else None

for k in (1, 3, 6):
    b = first_reach(bo_coll, k); r = first_reach(rand_coll, k)
    bs = f"{b}" if b else ">40"; rs = f"{r}" if r else ">40"
    print(f"  找到第 {k} 个碰撞所需调用次数:  随机~{rs}  贝叶斯~{bs}")

# ---- 画图 ----
fig = plt.figure(figsize=(13, 5))

# 左：3D 散点（BO 采样点 vs 真实危险区）
ax = fig.add_subplot(1, 2, 1, projection='3d')
# 真实危险区（mock UPPAAL 判定碰撞的点，浅色底）
danger_mask = grid_pts
y_danger = np.array([mock_uppaal(x) for x in grid_pts])
dg = grid_pts[y_danger > COLLISION_THRESHOLD]
ax.scatter(dg[:, 0], dg[:, 1], dg[:, 2], c='#FADBD8', s=6, alpha=0.35, depthshade=False, label='真实危险区(碰撞)')
ax.scatter(bo_X[is_coll, 0], bo_X[is_coll, 1], bo_X[is_coll, 2], c='#E74C3C', s=45, marker='o', edgecolors='k', linewidths=0.4, label='BO 找到的碰撞')
ax.scatter(bo_X[~is_coll, 0], bo_X[~is_coll, 1], bo_X[~is_coll, 2], c='#27AE60', s=25, marker='o', alpha=0.7, label='BO 采样(安全)')
ax.set_xlabel('gap (m)'); ax.set_ylabel('v_ego (m/s)'); ax.set_zlabel('v_obs (m/s)')
ax.set_title('BO 采样点逐渐聚集到危险角（低 gap × 快 ego × 慢 obs）')
ax.legend(fontsize=8, loc='upper left')
ax.view_init(elev=22, azim=-60)

# 右：收敛曲线
ax2 = fig.add_subplot(1, 2, 2)
ax2.plot(np.arange(1, budget+1), bo_coll, 'o-', color='#E74C3C', lw=2, label='贝叶斯优化')
ax2.plot(np.arange(1, budget+1), rand_coll, 's--', color='#2E86C1', lw=1.8, label='随机搜索')
ax2.plot(np.arange(1, len(grid_coll)+1), grid_coll, '^-', color='#95A5A6', lw=1.2, label='网格穷举')
ax2.set_xlabel('UPPAAL 调用次数')
ax2.set_ylabel('累计找到的碰撞场景数')
ax2.set_title(f'{N_RUN} 次平均：BO 用更少 UPPAAL 调用找到更多碰撞')
ax2.legend(); ax2.grid(alpha=0.3)

plt.tight_layout()
out = r"d:\3study\zh\_归档\GA2AD_demo\bo_uppaal_demo.png"
plt.savefig(out, dpi=120)
print("\n图已保存:", out)

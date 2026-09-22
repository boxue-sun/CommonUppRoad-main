# -*- coding: utf-8 -*-
"""
GA2AD 思想小 demo（纯 Python，秒跑，不依赖 UPPAAL/CommonRoad）

演示两件事：
  1. 用「风险场(TTC)」当连续奖励，替代「撞/没撞」的二元奖励 → 坏车学得更快
  2. 让前车(坏车/背景车)「学一个策略」——在什么车距/相对速度下该刹车/加速
     → 学出来的策略 = 「近距离急刹」，正好复现你 sudden_brake 实验的 81.8% 碰撞

场景：一维跟车。ego 是简化版 ISO 15622 ACC（自由流/接近/制动，带反应延迟）。
      前车是「对抗者」，每一步选 刹车/匀速/加速，目标是把 ego 撞了。
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ---- 物理/模型参数（对齐你的 ISO 15622 设定）----
DT = 0.1
CAR_LEN = 4.5
EGO_DESIRED = 25.0      # ego 期望速度
EGO_VMAX = 33.0
REACTION_TIME = 1.0     # 反应延迟(s) —— 碰撞的主因
T_DANGER = 1.0          # 危险 TTC 阈值
A_EMERG = -7.0          # 紧急制动（比前车-6略强）
A_ACCEL = 1.5           # 加速
HEADWAY = 1.2           # 跟车时距(s)
MIN_GAP = 3.0           # 最小跟车距离(m)
LEAD_A = np.array([-6.0, 0.0, 2.0])   # 前车动作: [刹车, 匀速, 加速]

# ---- 状态离散化 ----
GAP_EDGES = [5, 10, 20, 40]          # 车距分 5 档
REL_EDGES = [-1, 1, 5]               # 接近速度分 4 档
N_GAP, N_REL, N_ACT = 5, 4, 3


def ego_accel(gap, v_ego, v_lead):
    """简化 ISO 15622 ACC：跟车模式(目标车距) + 紧急制动(TTC)"""
    rel = v_ego - v_lead
    ttc = gap / rel if rel > 0.01 else 1e9
    if ttc < T_DANGER:
        return A_EMERG                       # 紧急制动
    g_star = MIN_GAP + HEADWAY * v_ego       # 目标跟车距离
    a = 0.4 * (gap - g_star) + 0.7 * (v_lead - v_ego)   # 车距误差 + 速度误差
    return float(np.clip(a, A_EMERG, A_ACCEL))


def state_index(gap, rel):
    g = int(np.digitize(gap, GAP_EDGES))       # 0..4
    r = int(np.digitize(rel, REL_EDGES))       # 0..3
    return g, r


def run_episode(Q, eps, use_risk):
    """跑一局，返回 (是否碰撞, 总奖励)。Q=None 表示纯随机基线。"""
    v_ego = np.random.uniform(18, 26)
    v_lead = np.random.uniform(16, 24)
    gap = np.random.uniform(30, 60)
    x_ego, x_lead = 0.0, gap

    # 反应延迟：ego 的制动命令延迟 REACTION_TIME 生效（环形缓冲）
    delay_steps = int(REACTION_TIME / DT) + 1
    hist = [0.0] * delay_steps

    total = 0.0
    for step in range(300):
        rel = v_ego - v_lead
        g, r = state_index(gap, rel)

        # 前车（对抗者）选动作
        if Q is None:
            act = np.random.randint(N_ACT)
        elif np.random.rand() < eps:
            act = np.random.randint(N_ACT)
        else:
            act = int(np.argmax(Q[g, r]))

        a_lead = LEAD_A[act]
        # ego 选动作（带延迟）
        desired = ego_accel(gap, v_ego, v_lead)
        hist.append(desired)
        a_ego = hist.pop(0)

        # 推进动力学
        v_lead = max(0.0, v_lead + a_lead * DT)
        x_lead += v_lead * DT
        v_ego = max(0.0, min(EGO_VMAX, v_ego + a_ego * DT))
        x_ego += v_ego * DT
        gap = x_lead - x_ego - CAR_LEN

        # 风险场奖励（GA2AD 核心：risk ∝ 1/TTC）
        risk = 0.0
        if rel > 0.01 and gap > 0:
            ttc = gap / rel
            risk = 1.0 / (ttc + 0.3)

        rew = (risk if use_risk else 0.0) - 0.01   # 微小时间惩罚
        done = False
        if gap <= 0:
            rew += 10.0; done = True               # 撞了，大奖励
        elif gap > 100:
            rew -= 5.0; done = True                # 前车跑远，惩罚

        if Q is not None:
            g2, r2 = state_index(max(gap, 0), rel) if not done else (g, r)
            target = rew + (0.0 if done else 0.95 * np.max(Q[g2, r2]))
            Q[g, r, act] += 0.2 * (target - Q[g, r, act])

        total += rew
        if done:
            return gap <= 0, total
    return False, total


def train(use_risk, episodes=800, seed=0):
    np.random.seed(seed)
    Q = np.zeros((N_GAP, N_REL, N_ACT))
    coll = []
    for ep in range(episodes):
        eps = max(0.05, 1.0 - ep / episodes)
        hit, _ = run_episode(Q, eps, use_risk)
        coll.append(1 if hit else 0)
    return Q, np.array(coll)


def rolling(x, w=50):
    return np.convolve(x, np.ones(w) / w, mode='valid')


# ---- 训练两种奖励 ----
Q_risk, coll_risk = train(use_risk=True, episodes=1200)
Q_bin, coll_bin = train(use_risk=False, episodes=1200)

# ---- 随机基线 ----
np.random.seed(123)
coll_rand = []
for _ in range(1200):
    hit, _ = run_episode(None, 0, True)
    coll_rand.append(1 if hit else 0)

print("=== 碰撞率对比（分阶段，看谁学得快）===")
print(f"{'方法':<22}{'前150局':>10}{'中150-300局':>12}{'最后200局':>12}")
print(f"{'纯随机前车':<20}{np.mean(coll_rand[:150]):>11.1%}{np.mean(coll_rand[150:300]):>13.1%}{np.mean(coll_rand[-200:]):>13.1%}")
print(f"{'二元奖励(撞+10/否-1)':<20}{np.mean(coll_bin[:150]):>11.1%}{np.mean(coll_bin[150:300]):>13.1%}{np.mean(coll_bin[-200:]):>13.1%}")
print(f"{'风险场奖励(∝1/TTC)':<20}{np.mean(coll_risk[:150]):>11.1%}{np.mean(coll_risk[150:300]):>13.1%}{np.mean(coll_risk[-200:]):>13.1%}  <- GA2AD")

# ---- 学到的策略解读 ----
GAP_LABELS = ['0-5m', '5-10m', '10-20m', '20-40m', '40m+']
REL_LABELS = ['慢于ego', '接近', '略快', '远快于ego']
ACT_LABELS = ['刹车', '匀速', '加速']
policy = Q_risk.argmax(axis=2)
print("\n=== 坏车学到的策略（每格最优动作）===")
print("         " + "  ".join(f"{l:>7}" for l in REL_LABELS))
for gi in range(N_GAP):
    row = "  ".join(f"{ACT_LABELS[policy[gi, ri]]:>7}" for ri in range(N_REL))
    print(f"{GAP_LABELS[gi]:>6}  {row}")

# ---- 画图 ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))

ax = axes[0]
ax.plot(rolling(coll_rand), label='纯随机前车', color='gray', lw=1.5)
ax.plot(rolling(coll_bin), label='二元奖励(撞+10/否-1)', color='#2E86C1', lw=1.8)
ax.plot(rolling(coll_risk), label='风险场奖励(∝1/TTC)', color='#E74C3C', lw=2.2)
ax.set_xlabel('训练局数'); ax.set_ylabel('碰撞率(滚动50局)')
ax.set_title('坏车学习曲线：风险场奖励收敛更快')
ax.legend(); ax.grid(alpha=0.3)

ax = axes[1]
cmap = plt.get_cmap('RdYlGn_r', 3)
im = ax.imshow(policy, cmap=cmap, vmin=0, vmax=2, aspect='auto')
ax.set_xticks(range(N_REL)); ax.set_xticklabels(REL_LABELS)
ax.set_yticks(range(N_GAP)); ax.set_yticklabels(GAP_LABELS)
ax.set_xlabel('相对速度(接近速度)'); ax.set_ylabel('车距')
ax.set_title('学到的策略：近距离→刹车')
cbar = fig.colorbar(im, ax=ax, ticks=[0, 1, 2])
cbar.ax.set_yticklabels(ACT_LABELS)

ax = axes[2]
# 用学到的最优策略跑一条轨迹，看碰撞过程
np.random.seed(7)
v_ego, v_lead, gap = 25.0, 22.0, 40.0
x_ego, x_lead = 0.0, gap
delay_steps = int(REACTION_TIME / DT) + 1
hist = [0.0] * delay_steps
gaps, ts = [], []
for step in range(300):
    rel = v_ego - v_lead
    g, r = state_index(gap, rel)
    act = int(np.argmax(Q_risk[g, r]))
    a_lead = LEAD_A[act]
    desired = ego_accel(gap, v_ego, v_lead)
    hist.append(desired); a_ego = hist.pop(0)
    v_lead = max(0.0, v_lead + a_lead * DT); x_lead += v_lead * DT
    v_ego = max(0.0, min(EGO_VMAX, v_ego + a_ego * DT)); x_ego += v_ego * DT
    gap = x_lead - x_ego - CAR_LEN
    gaps.append(gap); ts.append(step * DT)
    if gap <= 0:
        break
ax.plot(ts, gaps, color='#E74C3C', lw=2)
ax.axhline(0, color='black', ls='--', lw=1)
ax.set_xlabel('时间(s)'); ax.set_ylabel('车距(m)')
ax.set_title('对抗轨迹：前车急刹 → 追尾碰撞')
ax.grid(alpha=0.3)

plt.tight_layout()
out = r"d:\3study\zh\_归档\GA2AD_demo\ga2ad_demo.png"
plt.savefig(out, dpi=120)
print("\n图已保存:", out)

"""
rl_scenario_search.py
强化学习搜索危险场景：Agent 在参数空间中学习找到碰撞场景
基于 close_range 实验数据 (200 变体)

环境: (distance, ego_speed, obs_speed) → collision?
Agent: Q-learning 学习哪个参数区域最危险
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os, sys, csv, random
from collections import defaultdict

ROOT = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(ROOT, "experiments", "rl_search")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====== 参数空间 (与 close_range 一致) ======
DISTANCES = [3, 5, 8, 10, 15, 20, 30, 50]
OBS_SPEEDS = [0, 1, 3, 5, 10]
EGO_SPEEDS = [10, 15, 20, 25, 30]

N_DIST = len(DISTANCES)
N_OBS = len(OBS_SPEEDS)
N_EGO = len(EGO_SPEEDS)
TOTAL = N_DIST * N_OBS * N_EGO  # 200


def load_ground_truth():
    """加载 close_range 实验结果"""
    csv_path = os.path.join(ROOT, "experiments", "exp_close_range", "results.csv")
    grid = np.zeros((N_DIST, N_OBS, N_EGO), dtype=np.float32)
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            di = DISTANCES.index(int(row['distance']))
            oi = OBS_SPEEDS.index(int(row['obs_speed']))
            ei = EGO_SPEEDS.index(int(row['ego_speed']))
            grid[di, oi, ei] = 1.0 if row['collision_found'] == 'TRUE' else 0.0
    return grid

# ====== RL 环境 ======
class ScenarioSearchEnv:
    """
    参数空间搜索环境。
    状态 = (di, oi, ei) 离散索引
    动作 = 0-5: ±distance, ±obs_speed, ±ego_speed
    """
    def __init__(self, ground_truth):
        self.gt = ground_truth
        self.n_actions = 6
        self.state = (0, 0, 0)
        self.visited = set()

    def reset(self, start=None):
        if start is not None:
            self.state = start
        else:
            self.state = (
                random.randint(0, N_DIST - 1),
                random.randint(0, N_OBS - 1),
                random.randint(0, N_EGO - 1)
            )
        self.visited = {self.state}
        return self.state

    def step(self, action):
        di, oi, ei = self.state
        # 动作: 0=dist-, 1=dist+, 2=obs-, 3=obs+, 4=ego-, 5=ego+
        if action == 0 and di > 0:
            di -= 1
        elif action == 1 and di < N_DIST - 1:
            di += 1
        elif action == 2 and oi > 0:
            oi -= 1
        elif action == 3 and oi < N_OBS - 1:
            oi += 1
        elif action == 4 and ei > 0:
            ei -= 1
        elif action == 5 and ei < N_EGO - 1:
            ei += 1

        self.state = (di, oi, ei)
        collision = self.gt[di, oi, ei] > 0.5

        # 奖励设计
        if self.state in self.visited:
            reward = -0.5  # 重复访问小惩罚
        elif collision:
            reward = 10.0   # 找到碰撞
        else:
            reward = -1.0   # 没找到

        self.visited.add(self.state)
        done = len(self.visited) >= 60  # 每 episode 最多 60 步
        return self.state, reward, done, {'collision': collision}

    @staticmethod
    def action_names():
        return ['dist-', 'dist+', 'obs-', 'obs+', 'ego-', 'ego+']

    @staticmethod
    def state_to_params(state):
        di, oi, ei = state
        return DISTANCES[di], OBS_SPEEDS[oi], EGO_SPEEDS[ei]


# ====== Q-Learning Agent ======
class QLearningAgent:
    def __init__(self, n_actions, alpha=0.1, gamma=0.95, epsilon=1.0,
                 epsilon_min=0.05, epsilon_decay=0.995):
        self.Q = defaultdict(lambda: np.zeros(n_actions))
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.n_actions = n_actions

    def act(self, state, training=True):
        if training and random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        return int(np.argmax(self.Q[state]))

    def learn(self, state, action, reward, next_state):
        best_next = np.max(self.Q[next_state])
        td_target = reward + self.gamma * best_next
        self.Q[state][action] += self.alpha * (td_target - self.Q[state][action])

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


# ====== 训练 ======
def train_agent(env, agent, episodes=500):
    """训练 Q-learning agent"""
    episode_rewards = []
    episode_collisions = []
    total_collisions_found = set()

    for ep in range(episodes):
        state = env.reset()
        done = False
        ep_reward = 0
        ep_col = 0

        while not done:
            action = agent.act(state, training=True)
            next_state, reward, done, info = env.step(action)
            agent.learn(state, action, reward, next_state)
            state = next_state
            ep_reward += reward
            if info['collision']:
                ep_col += 1
                total_collisions_found.add(state)

        agent.decay_epsilon()
        episode_rewards.append(ep_reward)
        episode_collisions.append(ep_col)

        if (ep + 1) % 50 == 0:
            print(f"  Episode {ep+1:4d}: reward={ep_reward:6.1f}, "
                  f"collisions_found={len(total_collisions_found)}, "
                  f"epsilon={agent.epsilon:.3f}")

    return episode_rewards, episode_collisions, total_collisions_found


# ====== 基准对比 ======
def random_search(env, n_steps=3000):
    """随机搜索 baseline"""
    env.reset()
    collisions_found = set()
    for _ in range(n_steps):
        action = random.randint(0, 5)
        state, _, _, info = env.step(action)
        if info['collision']:
            collisions_found.add(state)
    return collisions_found


def grid_search(ground_truth):
    """网格穷举 baseline"""
    collisions = set()
    for di in range(N_DIST):
        for oi in range(N_OBS):
            for ei in range(N_EGO):
                if ground_truth[di, oi, ei] > 0.5:
                    collisions.add((di, oi, ei))
    return collisions


# ====== 可视化 ======
def plot_training_curve(rewards, collisions_per_ep, output_path):
    """训练曲线"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    ax1.plot(rewards, alpha=0.3, color='blue', linewidth=0.5)
    ax1.plot(np.convolve(rewards, np.ones(20)/20, mode='valid'),
             color='blue', linewidth=2, label='20-episode avg')
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Total Reward')
    ax1.set_title('Q-Learning Training: Reward per Episode')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(collisions_per_ep, alpha=0.3, color='red', linewidth=0.5)
    ax2.plot(np.convolve(collisions_per_ep, np.ones(20)/20, mode='valid'),
             color='red', linewidth=2, label='20-episode avg')
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Collisions Found')
    ax2.set_title('Collisions Discovered per Episode')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()
    print(f"  -> {output_path}")


def plot_q_value_heatmap(agent, ground_truth, output_path):
    """Q-value 热力图 vs 真实碰撞分布"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))

    # 按距离聚合 Q 值
    dist_names = [str(d) + 'm' for d in DISTANCES]

    for ei, (ego_spd, ax) in enumerate(zip(EGO_SPEEDS[:3], axes[0])):
        q_map = np.zeros((N_DIST, N_OBS))
        gt_map = np.zeros((N_DIST, N_OBS))
        for di in range(N_DIST):
            for oi in range(N_OBS):
                gt_map[di, oi] = ground_truth[di, oi, ei]
                q_vals = agent.Q[(di, oi, ei)]
                q_map[di, oi] = np.max(q_vals)

        im = ax.imshow(q_map.T, origin='lower', aspect='auto', cmap='YlOrRd',
                       extent=[0, N_DIST, 0, N_OBS])
        ax.set_xticks(range(N_DIST))
        ax.set_xticklabels(dist_names, rotation=45, fontsize=7)
        ax.set_yticks(range(N_OBS))
        ax.set_yticklabels([str(s) for s in OBS_SPEEDS], fontsize=7)
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('Obs Speed (m/s)')
        ax.set_title(f'Q-values: ego={ego_spd} m/s')

    for ei, (ego_spd, ax) in enumerate(zip(EGO_SPEEDS[3:], axes[1])):
        gt_map = np.zeros((N_DIST, N_OBS))
        for di in range(N_DIST):
            for oi in range(N_OBS):
                gt_map[di, oi] = ground_truth[di, oi, ei]
        im = ax.imshow(gt_map.T, origin='lower', aspect='auto', cmap='RdYlGn_r',
                       extent=[0, N_DIST, 0, N_OBS], vmin=0, vmax=1)
        ax.set_xticks(range(N_DIST))
        ax.set_xticklabels(dist_names, rotation=45, fontsize=7)
        ax.set_yticks(range(N_OBS))
        ax.set_yticklabels([str(s) for s in OBS_SPEEDS], fontsize=7)
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('Obs Speed (m/s)')
        ax.set_title(f'Ground Truth: ego={ego_spd} m/s (red=collision)')

    fig.suptitle('Q-Learning: Learned Danger Zones vs Actual Collision Data',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()
    print(f"  -> {output_path}")


def plot_search_efficiency(agent, total_collisions, output_path):
    """搜索效率对比：RL vs Random"""
    fig, ax = plt.subplots(figsize=(10, 6))
    max_steps = 3000
    n_trials = 50

    # RL greedy
    rl_curve = np.zeros(max_steps)
    for trial in range(n_trials):
        env_rl = ScenarioSearchEnv(load_ground_truth())
        env_rl.reset()
        found = set()
        for step in range(max_steps):
            state = env_rl.state
            action = np.argmax(agent.Q[state])
            next_state, _, _, info = env_rl.step(action)
            if info['collision']:
                found.add(next_state)
            rl_curve[step] += len(found)
    rl_curve /= n_trials

    # Random
    rnd_curve = np.zeros(max_steps)
    for trial in range(n_trials):
        env_rnd = ScenarioSearchEnv(load_ground_truth())
        env_rnd.reset()
        found = set()
        for step in range(max_steps):
            action = random.randint(0, 5)
            state, _, _, info = env_rnd.step(action)
            if info['collision']:
                found.add(state)
            rnd_curve[step] += len(found)
    rnd_curve /= n_trials

    ax.plot(rl_curve, 'b-', linewidth=2, label='RL (Q-Learning greedy)')
    ax.plot(rnd_curve, 'r--', linewidth=2, label='Random search')
    ax.axhline(y=total_collisions, color='green', linestyle=':',
               linewidth=2, label=f'Total collisions ({total_collisions})')
    ax.set_xlabel('Search Steps')
    ax.set_ylabel('Cumulative Collisions Found')
    ax.set_title('Search Efficiency: RL vs Random')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()
    print(f"  -> {output_path}")
    return rl_curve, rnd_curve


def plot_agent_trajectory(agent, ground_truth, output_path):
    """可视化 agent 在参数空间中的搜索路径"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    for idx, ego_spd in enumerate([15, 20, 25, 30]):
        ax = axes[idx // 2, idx % 2]
        ei = EGO_SPEEDS.index(ego_spd)

        # 画真实碰撞
        gt_map = ground_truth[:, :, ei]
        ax.imshow(gt_map.T, origin='lower', aspect='auto', cmap='RdYlGn_r',
                  extent=[0, N_DIST, 0, N_OBS], alpha=0.3, vmin=0, vmax=1)

        # 画 Q 值箭头
        for di in range(N_DIST):
            for oi in range(N_OBS):
                q = agent.Q[(di, oi, ei)]
                if np.max(q) > 0:
                    best_a = np.argmax(q)
                    dx, dy = 0, 0
                    if best_a == 0: dx = -0.3
                    elif best_a == 1: dx = 0.3
                    elif best_a == 2: dy = -0.3
                    elif best_a == 3: dy = 0.3
                    elif best_a == 4: dx, dy = 0, 0  # ego change not shown
                    elif best_a == 5: dx, dy = 0, 0
                    if dx != 0 or dy != 0:
                        ax.arrow(di + 0.5, oi + 0.5, dx, dy,
                                 head_width=0.15, head_length=0.1,
                                 fc='blue', ec='blue', alpha=0.6, width=0.02)

        ax.set_xticks(range(N_DIST))
        ax.set_xticklabels([str(d) for d in DISTANCES])
        ax.set_yticks(range(N_OBS))
        ax.set_yticklabels([str(s) for s in OBS_SPEEDS])
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('Obs Speed (m/s)')
        ax.set_title(f'RL Policy: ego={ego_spd} m/s\n(arrows point toward danger)')

    fig.suptitle('Learned Policy: Agent Learns to Move Toward Collision Zones',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()
    print(f"  -> {output_path}")


# ====== 主程序 ======
def main():
    print("=" * 60)
    print("RL Scenario Search: Q-Learning on Collision Data")
    print(f"Parameter Space: {N_DIST}D × {N_OBS}O × {N_EGO}E = {TOTAL} states")
    print(f"Total Collisions: {int(np.sum(load_ground_truth()))}")
    print("=" * 60)

    # 1. 加载数据
    ground_truth = load_ground_truth()
    total_collisions = int(np.sum(ground_truth))
    print(f"\nGround truth: {total_collisions}/{TOTAL} collisions ({total_collisions/TOTAL*100:.1f}%)")

    # 2. 训练 Q-learning
    print("\n[1/4] Training Q-Learning Agent...")
    env = ScenarioSearchEnv(ground_truth)
    agent = QLearningAgent(n_actions=6, alpha=0.1, gamma=0.95,
                           epsilon=1.0, epsilon_min=0.05, epsilon_decay=0.995)
    rewards, collisions_per_ep, rl_found = train_agent(env, agent, episodes=500)

    print(f"\n  RL found {len(rl_found)}/{total_collisions} unique collisions "
          f"({len(rl_found)/max(1,total_collisions)*100:.1f}%)")

    # 3. 对比 baseline
    print("\n[2/4] Running baselines...")
    env_rnd = ScenarioSearchEnv(ground_truth)
    random_found = random_search(env_rnd, n_steps=3000)
    grid_found = grid_search(ground_truth)
    print(f"  Random search (3000 steps): {len(random_found)}/{total_collisions}")
    print(f"  Grid search (exhaustive):   {len(grid_found)}/{total_collisions} (100%)")

    # 4. 可视化
    print("\n[3/4] Generating visualizations...")
    plot_training_curve(rewards, collisions_per_ep,
                        os.path.join(OUTPUT_DIR, 'training_curve.png'))
    plot_q_value_heatmap(agent, ground_truth,
                         os.path.join(OUTPUT_DIR, 'q_value_heatmap.png'))
    plot_agent_trajectory(agent, ground_truth,
                          os.path.join(OUTPUT_DIR, 'agent_policy.png'))

    # 5. 效率对比
    print("\n[4/4] Comparing search efficiency...")
    rl_curve, rnd_curve = plot_search_efficiency(
        agent, total_collisions,
        os.path.join(OUTPUT_DIR, 'search_efficiency.png'))

    # 效率统计
    rl_steps_to_80pct = np.argmax(rl_curve >= total_collisions * 0.8)
    rnd_steps_to_80pct = np.argmax(rnd_curve >= total_collisions * 0.8)
    print(f"\n  Steps to find 80% of collisions:")
    print(f"    RL:     {rl_steps_to_80pct} steps")
    print(f"    Random: {rnd_steps_to_80pct} steps")
    if rnd_steps_to_80pct > 0:
        print(f"    Speedup: {rnd_steps_to_80pct / max(1, rl_steps_to_80pct):.1f}x")

    # 最终总结
    print("\n" + "=" * 60)
    print("Done! Output files:")
    print(f"  {os.path.join(OUTPUT_DIR, 'training_curve.png')}")
    print(f"  {os.path.join(OUTPUT_DIR, 'q_value_heatmap.png')}")
    print(f"  {os.path.join(OUTPUT_DIR, 'agent_policy.png')}")
    print(f"  {os.path.join(OUTPUT_DIR, 'search_efficiency.png')}")
    print("=" * 60)


if __name__ == '__main__':
    main()

"""
rl_online_search.py
在线强化学习搜索：Agent 直接调 UPPAAL，在未知的大参数空间中找碰撞

核心区别：不是从CSV学，而是每次query真正跑UPPAAL验证
目标：用最少UPPAAL查询找到最多碰撞场景
"""
import subprocess, os, sys, csv, random, json, tempfile, shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(__file__)
TEMPLATE = os.path.join(ROOT, "uppaal", "template.xml")
VERIFYTA = r"C:\Program Files\UPPAAL-5.1.0-beta5\app\bin\verifyta.exe"
QUERY = "A[] !cps_i_state.detection.collide\n"

# ====== 连续参数空间（中等规模，可跑完基准）======
DISTANCES = [3, 5, 8, 10, 15, 20, 30, 50]                    # 8 values
EGO_SPEEDS = [10, 15, 20, 25, 30, 35]                        # 6 values
OBS_SPEEDS = [0, 3, 5, 10, 15, 20]                           # 6 values

N_D, N_E, N_O = len(DISTANCES), len(EGO_SPEEDS), len(OBS_SPEEDS)
TOTAL_STATES = N_D * N_E * N_O  # 18×15×15 = 4050
print(f"Parameter space: {N_D}D × {N_E}E × {N_O}O = {TOTAL_STATES} states")
print(f"Grid search would need {TOTAL_STATES} UPPAAL queries (~{TOTAL_STATES*3//60} minutes)")

# ====== UPPAAL Oracle ======
class UppaalOracle:
    """把 UPPAAL 包装成一个函数：输入参数 → 输出碰撞/安全"""
    def __init__(self):
        self.cache = {}         # 缓存已查过的结果
        self.query_count = 0
        self.tmpdir = tempfile.mkdtemp(prefix="rl_uppaal_")
        self.query_file = os.path.join(self.tmpdir, "query.q")
        with open(self.query_file, 'w') as f:
            f.write(QUERY)

    def query(self, distance, ego_speed, obs_speed):
        """查询 UPPAAL：这组参数会不会碰撞？返回 True=碰撞"""
        key = (distance, ego_speed, obs_speed)
        if key in self.cache:
            return self.cache[key]

        self.query_count += 1
        model_path = os.path.join(self.tmpdir, "model.xml")
        self._generate_model(distance, obs_speed, ego_speed, model_path)

        try:
            result = subprocess.run(
                [VERIFYTA, "-s", model_path, self.query_file],
                capture_output=True, text=True, timeout=60,
                encoding='utf-8', errors='replace'
            )
            output = result.stdout + result.stderr
            collision = "NOT satisfied" in output  # NOT satisfied = found counterexample = collision
        except Exception:
            collision = False

        self.cache[key] = collision
        return collision

    def _generate_model(self, distance, obs_speed, ego_speed, output_path):
        """用模板生成单个 UPPAAL 模型（复用 close_range 的逻辑）"""
        with open(TEMPLATE, 'r', encoding='utf-8') as f:
            tpl = f.read()

        scenario_lines = [
            "const int P = 1;", "const uint16_t MAXTIME = 50;",
            "const int MAXP = 2;", "const int NONE = -1;", "const int MAXL = 3;",
            "const int MAXSO = 1;", "const int MAXDO = 1;",
            "const int MAXTP = 1;", "const int MAXPRE = 1;", "const int MAXSUC = 1;",
            "const double THRESHOLD = 4.0;", "const double TIMESTEPSIZE = 0.1;",
            "const double RADAR = 100;", "const uint8_t N1 = 1;",
            "const uint8_t N2 = 4;", "const uint8_t MAXACT = 2;",
            "typedef int[0,MAXACT-1] act_id_t;",
            "const uint8_t BASE = 10;", "const uint8_t EXPONENT = 1;",
            "const uint8_t MAXOBS = 1;", "typedef int[0,MAXOBS-1] obs_id_t;",
            "", "typedef int[-1,65535] id_t;",
            "typedef struct { int32_t x; int32_t y; }ST_IPOINT;",
            "typedef struct { double x; double y; }ST_DPOINT;",
            "typedef struct { ST_IPOINT ends[2]; }ST_DLINE;",
            "typedef struct { ST_IPOINT points[MAXP]; bool dashLine; }ST_BOUND;",
            "typedef struct { id_t ID; ST_BOUND left; ST_BOUND right; id_t predecessor[MAXPRE]; id_t successor[MAXSUC]; id_t adjLeft; bool dirLeft; id_t adjRight; bool dirRight; }ST_LANE;",
            "typedef struct { bool collide; bool outside; bool reach; }ST_DETECTION;",
            "typedef struct { ST_DPOINT position; double velocity; double orientation; double acceleration; double accRate; double yawRate; }ST_DSTATE;",
            "typedef struct { ST_IPOINT position; int32_t velocity; int32_t orientation; int32_t acceleration; int32_t accRate; int32_t yawRate; ST_DETECTION detection; }ST_ISTATE;",
            "typedef struct { hybrid clock x; hybrid clock y; hybrid clock velocity; hybrid clock orientation; hybrid clock acceleration; }ST_DYNAMICS;",
            "typedef struct { ST_IPOINT center; int32_t width; int32_t length; int32_t orientation; }ST_RECTANGLE;",
            "typedef struct { int32_t maxVelocity; int32_t minVelocity; int32_t maxOrientation; int32_t minOrientation; }ST_RULES;",
            "typedef struct { ST_IPOINT goal; }ST_PLANNING;",
            "typedef struct { int32_t time; ST_DSTATE dState; }ST_PAIR;",
            "typedef struct { int32_t vMin; int32_t vMax; int32_t accMax; int32_t decMax; int32_t laneChangeProb; int32_t cutInRange; int32_t initialLane; }ST_OBEHAVIOR;",
            "",
            "const ST_BOUND leftLane1 = {{{0, 17}, {1990, 17}}, false};",
            "const ST_BOUND rightLane1 = {{{0, -17}, {1990, -17}}, false};",
            "const ST_LANE lane1 = {1, leftLane1, rightLane1, {NONE}, {NONE}, 2, false, NONE, false};",
            "const ST_BOUND leftLane2 = {{{0, 52}, {1990, 52}}, false};",
            "const ST_BOUND rightLane2 = {{{0, 17}, {1990, 17}}, false};",
            "const ST_LANE lane2 = {2, leftLane2, rightLane2, {NONE}, {NONE}, 3, true, 1, false};",
            "const ST_BOUND leftLane3 = {{{0, 87}, {1990, 87}}, false};",
            "const ST_BOUND rightLane3 = {{{0, 52}, {1990, 52}}, false};",
            "const ST_LANE lane3 = {3, leftLane3, rightLane3, {NONE}, {NONE}, NONE, false, 2, true};",
            "const ST_LANE laneNet[MAXL] = {lane1, lane2, lane3};",
            "const bool staticObsExists = false;",
            "const ST_RECTANGLE staticObs[MAXSO] = {{{NONE, NONE}, NONE, NONE, NONE}};",
            "const ST_PLANNING planning = {{995, 0}};",
        ]
        scenario_data = "\n".join(scenario_lines)

        sm = "<declaration>// Generated scenario starts"
        em = "// Generated scenario ends"
        si = tpl.index(sm)
        ei = tpl.index(em) + len(em)
        tpl = tpl[:si] + sm + "\n" + scenario_data + "\n" + tpl[ei:]

        # Obstacle
        obs_start = "<system>// Generated moving obstacles starts"
        obs_end = "// Generated moving obstacles ends"
        osi = tpl.index(obs_start)
        oei = tpl.index(obs_end) + len(obs_end)
        v_min, v_max = max(0.5, obs_speed*0.5), obs_speed*1.5+5
        obs_data = (
            "<system>// Generated moving obstacles starts\n"
            f"const ST_DSTATE initCS0 = {{{{{distance}.0, 0.0}}, {float(obs_speed)}, 0.0, 0.0, 0.0, 0.0}};\n"
            f"const ST_RECTANGLE shapeObs0 = {{{{{distance*10}, 0}}, 20, 45, 0}};\n"
            f"const ST_OBEHAVIOR obsBehavior0 = {{d2i({v_min}), d2i({v_max}), d2i(3.0), d2i(6.0), d2i(0.3), d2i(50.0), d2i(0.0)}};\n"
            "obs0 = Obstacle(0, initCS0, shapeObs0, obsBehavior0);\n"
            "// Generated moving obstacles ends"
        )
        tpl = tpl[:osi] + obs_data + tpl[oei:]

        # Ego
        es = "// Generated ego vehicle starts"
        ee = "// Generated ego vehicle ends"
        esi = tpl.index(es)
        eei = tpl.index(ee) + len(ee)
        ego_data = (
            "// Generated ego vehicle starts\n"
            f"const ST_DSTATE initEgo = {{{{{0.0}, 0.0}}, {float(ego_speed)}, 0.0, 0.0, 0.0, 0.0}};\n"
            "const ST_RECTANGLE initShapeEgo = {{0, 0}, 10, 45, 0};\n"
            "const ST_RULES rules = {d2i(4.0), 0, d2i(0.2), d2i(-0.2)};\n"
            "const int[0,MAXL] initLane = 0;\n"
            "move = Act_Move(0); turn = Act_Turn(1);\n"
            "controller = Controller(initLane,initEgo,initShapeEgo,rules);\n"
            "timer = Timer(); dynamics = Dynamics(); rewardMachine = Rewards();\n"
            "// Generated ego vehicle ends"
        )
        tpl = tpl[:esi] + ego_data + tpl[eei:]

        # System
        ss = "// Generated model instances starts"
        se = "// Generated model instances ends"
        ssi = tpl.index(ss)
        ssei = tpl.index(se) + len(se)
        tpl = tpl[:ssi] + f"// Generated model instances starts\nsystem timer, obs0, move, turn, controller, dynamics, rewardMachine;\n// Generated model instances ends" + tpl[ssei:]

        # Query
        qs, qe = "<queries>", "</queries>"
        qsi = tpl.index(qs)
        qei = tpl.index(qe) + len(qe)
        tpl = tpl[:qsi] + f"<queries><query><formula>A[] !cps_i_state.detection.collide</formula><comment/></query></queries>" + tpl[qei:]

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(tpl)

    def cleanup(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def stats(self):
        return f"{self.query_count} queries, {sum(self.cache.values())} collisions found"


# ====== Q-Learning Agent（在线版）======
class QLearningAgent:
    def __init__(self, n_actions=6, alpha=0.1, gamma=0.95,
                 epsilon=1.0, eps_min=0.05, eps_decay=0.995):
        self.Q = {}  # dict: state_tuple -> np.array(6)
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.eps_min = eps_min
        self.eps_decay = eps_decay
        self.n_actions = n_actions

    def _ensure(self, state):
        if state not in self.Q:
            self.Q[state] = np.zeros(self.n_actions)

    def act(self, state, training=True):
        self._ensure(state)
        if training and random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        return int(np.argmax(self.Q[state]))

    def learn(self, s, a, r, ns):
        self._ensure(s)
        self._ensure(ns)
        self.Q[s][a] += self.alpha * (r + self.gamma * np.max(self.Q[ns]) - self.Q[s][a])

    def decay(self):
        self.epsilon = max(self.eps_min, self.epsilon * self.eps_decay)


# ====== 环境（在线版）======
class OnlineEnv:
    """每次 step 调 UPPAAL"""
    def __init__(self, oracle):
        self.oracle = oracle
        self.state = (0, 0, 0)
        self.visited = set()
        self.all_collisions = set()

    def reset(self):
        self.state = (random.randint(0, N_D-1), random.randint(0, N_E-1),
                      random.randint(0, N_O-1))
        self.visited = {self.state}
        return self.state

    def step(self, action):
        di, ei, oi = self.state
        if action == 0 and di > 0: di -= 1
        elif action == 1 and di < N_D-1: di += 1
        elif action == 2 and ei > 0: ei -= 1
        elif action == 3 and ei < N_E-1: ei += 1
        elif action == 4 and oi > 0: oi -= 1
        elif action == 5 and oi < N_O-1: oi += 1

        self.state = (di, ei, oi)
        d, e, o = DISTANCES[di], EGO_SPEEDS[ei], OBS_SPEEDS[oi]

        # 真正调 UPPAAL！
        collision = self.oracle.query(d, e, o)

        if collision:
            self.all_collisions.add(self.state)
            reward = 10.0
        elif self.state in self.visited:
            reward = -0.5
        else:
            reward = -1.0

        self.visited.add(self.state)
        return self.state, reward, collision


# ====== 训练 + 对比 ======
def train_online(env, agent, episodes=100, steps_per_ep=20):
    """在线训练：每次 step 都调 UPPAAL"""
    total_collisions = set()
    history = []
    for ep in range(episodes):
        state = env.reset()
        ep_collisions = 0
        for _ in range(steps_per_ep):
            action = agent.act(state, training=True)
            next_state, reward, collision = env.step(action)
            agent.learn(state, action, reward, next_state)
            state = next_state
            if collision:
                ep_collisions += 1
                total_collisions.add(state)
        agent.decay()
        history.append(len(total_collisions))
        if (ep+1) % 20 == 0:
            print(f"  Ep {ep+1:3d}: found {len(total_collisions)} collisions, "
                  f"queries={env.oracle.query_count}, eps={agent.epsilon:.3f}")
    return history, total_collisions


def random_search_baseline(oracle, n_queries):
    """随机搜索 baseline：用相同的查询预算"""
    env = OnlineEnv(oracle)
    env.reset()
    found = set()
    curve = []
    for _ in range(n_queries):
        di = random.randint(0, N_D-1)
        ei = random.randint(0, N_E-1)
        oi = random.randint(0, N_O-1)
        d, e, o = DISTANCES[di], EGO_SPEEDS[ei], OBS_SPEEDS[oi]
        if oracle.query(d, e, o):
            found.add((di, ei, oi))
        curve.append(len(found))
    return curve, found


# ====== 可视化 ======
def plot_results(rl_curve, rnd_curve, oracle, output_dir):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 图1: 发现曲线
    ax = axes[0]
    rl_q = oracle.query_count - len(rl_curve) * 20  # approximate
    # Use simple step indices
    ax.plot(range(1, len(rl_curve)+1), rl_curve, 'b-', linewidth=2, label='RL (Q-learning)')
    ax.plot(range(1, len(rnd_curve)+1), rnd_curve, 'r--', linewidth=2, label='Random')
    ax.set_xlabel('Training Episodes / Search Batches', fontsize=11)
    ax.set_ylabel('Unique Collisions Found', fontsize=11)
    ax.set_title('Collision Discovery: RL vs Random', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 图2: 查询效率（以查询次数为X轴）
    ax = axes[1]
    steps_per_ep = 10
    rl_x = [(i+1)*steps_per_ep for i in range(len(rl_curve))]
    ax.plot(rl_x, rl_curve, 'b-', linewidth=2, label=f'RL ({rl_curve[-1]} found)')
    ax.plot(range(1, len(rnd_curve)+1), rnd_curve, 'r--', linewidth=2, label=f'Random ({rnd_curve[-1]} found)')
    ax.set_xlabel('UPPAAL Queries', fontsize=11)
    ax.set_ylabel('Collisions Found', fontsize=11)
    ax.set_title(f'Search Efficiency ({oracle.query_count} total queries)', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 图3: Q值热力图（ego=25m/s 切片）
    ax = axes[2]
    try:
        ei = EGO_SPEEDS.index(25)
    except ValueError:
        ei = len(EGO_SPEEDS)//2
    q_map = np.zeros((N_D, N_O))
    for di in range(N_D):
        for oi in range(N_O):
            s = (di, ei, oi)
            if s in agent.Q:
                q_map[di, oi] = np.max(agent.Q[s])
    im = ax.imshow(q_map.T, origin='lower', aspect='auto', cmap='YlOrRd',
                   extent=[0, N_D, 0, N_O])
    ax.set_xticks(range(0, N_D, 2))
    ax.set_xticklabels([str(DISTANCES[i]) for i in range(0, N_D, 2)], rotation=45, fontsize=7)
    ax.set_yticks(range(0, N_O, 2))
    ax.set_yticklabels([str(OBS_SPEEDS[i]) for i in range(0, N_O, 2)], fontsize=7)
    ax.set_xlabel('Distance (m)')
    ax.set_ylabel('Obs Speed (m/s)')
    ax.set_title(f'Learned Q-values (ego={EGO_SPEEDS[ei]} m/s)', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax, label='Max Q-value')

    fig.suptitle('Online RL Scenario Search: Learning to Find Dangerous Scenarios via UPPAAL',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    out = os.path.join(output_dir, 'online_rl_results.png')
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"  -> {out}")


# ====== 主程序 ======
def main():
    print("=" * 60)
    print("Online RL: Agent queries UPPAAL in real-time")
    print(f"Parameter space: {TOTAL_STATES} states (grid search = {TOTAL_STATES} queries)")
    print("=" * 60)

    # 1. 创建 Oracle 和 Environment
    oracle = UppaalOracle()
    env = OnlineEnv(oracle)
    agent = QLearningAgent(n_actions=6, alpha=0.1, gamma=0.95,
                           epsilon=1.0, eps_min=0.05, eps_decay=0.99)

    # 2. 训练 RL
    n_episodes = 40        # 40 轮
    steps_per_ep = 10      # 每轮 10 步
    total_rl_queries = n_episodes * steps_per_ep  # ~400 queries
    print(f"\n[1/3] Training RL agent ({n_episodes} ep × {steps_per_ep} steps = ~{total_rl_queries} UPPAAL queries)")
    print(f"      Estimated time: ~{total_rl_queries*3//60} min")
    rl_history, rl_found = train_online(env, agent, episodes=n_episodes,
                                         steps_per_ep=steps_per_ep)
    print(f"\n  RL found {len(rl_found)} unique collisions in {oracle.query_count} queries")

    # 3. Random baseline（用相同查询数）
    oracle2 = UppaalOracle()
    print(f"\n[2/3] Random baseline ({total_rl_queries} queries)...")
    rnd_curve, rnd_found = random_search_baseline(oracle2, total_rl_queries)

    # 4. Ground truth（网格穷举）
    print(f"\n[3/3] Computing ground truth (full grid, {TOTAL_STATES} queries)...")
    print(f"      This will take ~{TOTAL_STATES*2//60} minutes...")
    oracle3 = UppaalOracle()
    gt_collisions = set()
    gt_count = 0
    for di in range(N_D):
        for ei in range(N_E):
            for oi in range(N_O):
                d, e, o = DISTANCES[di], EGO_SPEEDS[ei], OBS_SPEEDS[oi]
                if oracle3.query(d, e, o):
                    gt_collisions.add((di, ei, oi))
                gt_count += 1
        print(f"    Grid progress: {gt_count}/{TOTAL_STATES} ({gt_count*100//TOTAL_STATES}%), "
              f"collisions so far: {len(gt_collisions)}")

    total_gt = len(gt_collisions)
    print(f"\n  Ground truth: {total_gt}/{TOTAL_STATES} collisions ({total_gt/TOTAL_STATES*100:.1f}%)")

    # 5. 统计
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Total parameter space:     {TOTAL_STATES} states")
    print(f"  Total collisions (GT):     {total_gt}")
    print(f"  RL found:                  {len(rl_found)}/{total_gt} ({len(rl_found)/max(1,total_gt)*100:.1f}%)")
    print(f"  Random found:              {len(rnd_found)}/{total_gt} ({len(rnd_found)/max(1,total_gt)*100:.1f}%)")
    print(f"  RL queries:                {oracle.query_count}")
    print(f"  Grid queries (exhaustive): {TOTAL_STATES}")
    if total_gt > 0:
        rl_efficiency = len(rl_found) / max(1, oracle.query_count) * 100
        rnd_efficiency = len(rnd_found) / max(1, total_rl_queries) * 100
        grid_efficiency = total_gt / TOTAL_STATES * 100
        print(f"  RL efficiency:     {rl_efficiency:.1f} collisions per 100 queries")
        print(f"  Random efficiency: {rnd_efficiency:.1f} collisions per 100 queries")
        print(f"  Grid efficiency:   {grid_efficiency:.1f} collisions per 100 queries (exhaustive)")
    print("=" * 60)

    # 6. 可视化
    output_dir = os.path.join(ROOT, "experiments", "rl_search")
    os.makedirs(output_dir, exist_ok=True)
    plot_results(rl_history, rnd_curve, oracle, output_dir)

    # 7. 保存结果
    results = {
        'parameter_space': {'distances': DISTANCES, 'ego_speeds': EGO_SPEEDS, 'obs_speeds': OBS_SPEEDS},
        'total_states': TOTAL_STATES,
        'total_collisions_gt': total_gt,
        'rl_found': len(rl_found),
        'random_found': len(rnd_found),
        'rl_queries': oracle.query_count,
        'grid_queries': TOTAL_STATES,
    }
    with open(os.path.join(output_dir, 'online_rl_results.json'), 'w') as f:
        json.dump(results, f, indent=2)

    oracle.cleanup()
    oracle2.cleanup()
    oracle3.cleanup()
    print(f"\nDone. Output: {output_dir}")


if __name__ == '__main__':
    main()

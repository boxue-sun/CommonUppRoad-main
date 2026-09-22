"""
generate_cut_in_gifs.py
切入场景 GIF — CommonRoad 原生渲染
Ego 在 lane1 直行，动态障碍物从 lane2 切入 lane1
测试 ISO 15622 ACC 是否能避开
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

import os, sys, numpy as np, imageio

sys.path.insert(0, os.path.dirname(__file__))
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.state import CustomState, InitialState
from commonroad.scenario.trajectory import Trajectory
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.geometry.obstacle_shapes.rect_obstacle_shape import RectObstacleShape

ROOT = os.path.dirname(__file__)
ANIM_DIR = os.path.join(ROOT, "experiments", "animation", "cut_in")
os.makedirs(ANIM_DIR, exist_ok=True)

# ZAM_Tutorial: lane1 center Y=0, lane2 center Y=3.5, lane3 center Y=7.0
ROAD_SCENARIO = os.path.join(ROOT, "scenarios", "ZAM_Tutorial-1_2_T-1.xml")
LANE1_Y = 0.0     # ego 车道
LANE2_Y = 3.5     # 障碍物起始车道

# ====== ISO 15622 ACC 参数 ======
V_SET, T_HW, S0 = 30.0, 1.8, 2.0
A_MAX, COMFORT_BRAKE, EMERGENCY_BRAKE = 1.5, -2.0, -6.0
BRAKE_RATE, REACTION_TIME = 3.0, 1.5
DANGER_TTC, WARNING_TTC = 1.5, 3.0
APPROACH_DIST, P_GAIN = 80.0, 0.4

DT = 0.1
MAX_STEPS = 80
CAR_W, CAR_L = 1.8, 4.5


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def simulate_cut_in(ego_v0, obs_v0, distance):
    """
    模拟切入场景：
    - Ego 在 lane1 (Y=0) 直行，ISO 15622 控制
    - 障碍物从 lane2 (Y=3.5) 起步，延迟后向 lane1 切入
    """
    ego_x, ego_y = 0.0, LANE1_Y
    ego_v, ego_a, ego_heading = ego_v0, 0.0, 0.0

    # 障碍物从 lane2 起步
    obs_x = distance
    obs_y = LANE2_Y
    obs_v = obs_v0
    obs_a = 0.0
    obs_heading = -0.25   # 初始斜向ego车道(≈14°)，模拟激进切入

    # 切入行为控制
    yaw_rate = 1.5        # 横摆角速度 rad/s (快速变道)
    cut_in_duration = 2.5  # 切入持续2.5秒

    danger_detected = False
    reaction_step = 0
    log_lines = []
    collision_step = -1

    for step in range(MAX_STEPS):
        t = step * DT

        # === 障碍物：从 lane2 切向 lane1 ===
        if t < cut_in_duration:
            # 持续右转切向 ego 车道
            obs_yaw_rate = -yaw_rate
            obs_a = -1.0  # 切入时轻微减速
        elif abs(obs_heading) > 0.03:
            # 回正方向
            obs_yaw_rate = yaw_rate * 1.5
            obs_a = -3.0
        else:
            # 已在 ego 车道，直行减速
            obs_yaw_rate = 0.0
            obs_heading = 0.0
            obs_a = -3.0

        # 更新障碍物
        obs_heading += obs_yaw_rate * DT
        obs_v = max(0.0, obs_v + obs_a * DT)
        obs_x += obs_v * np.cos(obs_heading) * DT
        obs_y += obs_v * np.sin(obs_heading) * DT

        # === 间距和 TTC ===
        dx = obs_x - ego_x
        dy = obs_y - ego_y
        gap_2d = np.sqrt(dx**2 + dy**2)
        rel_v_long = ego_v - obs_v * np.cos(obs_heading)

        long_gap = dx
        if rel_v_long > 0.1 and long_gap > 0:
            ttc = long_gap / rel_v_long
        else:
            ttc = 999.0

        # === 碰撞检测 ===
        lat_gap = abs(obs_y - ego_y)
        if lat_gap < CAR_W and abs(long_gap) < CAR_L and collision_step < 0:
            collision_step = step

        # === Ego ISO 15622 决策 ===
        if ttc < WARNING_TTC:
            if not danger_detected:
                danger_detected = True
                reaction_step = 0
            reaction_step += 1
        else:
            danger_detected = False
            reaction_step = 0

        if danger_detected and reaction_step * DT < REACTION_TIME:
            pass  # 反应延迟，不干预
        else:
            desired_gap = S0 + ego_v * T_HW
            target_acc = 0.0

            if long_gap > APPROACH_DIST:
                target_acc = A_MAX if ego_v < V_SET else 0.0
            elif long_gap > desired_gap + 5.0:
                denom = max(1.0, APPROACH_DIST - desired_gap - 5.0)
                gap_ratio = clamp((APPROACH_DIST - long_gap) / denom, 0.0, 1.0)
                target_acc = -gap_ratio * 2.0
                if ego_v < obs_v:
                    target_acc = 0.0
            elif long_gap > S0:
                gap_error = long_gap - desired_gap
                target_acc = P_GAIN * gap_error - 0.5 * rel_v_long
                target_acc = clamp(target_acc, COMFORT_BRAKE, A_MAX)
            else:
                target_acc = EMERGENCY_BRAKE

            if ttc < DANGER_TTC:
                target_acc = EMERGENCY_BRAKE
            elif ttc < WARNING_TTC:
                if target_acc > COMFORT_BRAKE:
                    target_acc = COMFORT_BRAKE

            acc_step = BRAKE_RATE * DT
            if target_acc < ego_a - acc_step:
                ego_a -= acc_step
            elif target_acc > ego_a + acc_step:
                ego_a += acc_step
            else:
                ego_a = target_acc

        ego_v = max(0.0, ego_v + ego_a * DT)
        ego_x += ego_v * DT
        # ego 始终在 lane1 直行

        line = (f"{t:.1f} {obs_x:.2f} {obs_y:.2f} {obs_heading:.3f} "
                f"{obs_v:.2f} {obs_a:.2f} "
                f"{ego_x:.2f} {ego_y:.2f} {ego_heading:.3f} "
                f"{ego_v:.2f} {ego_a:.2f}")
        log_lines.append(line)

    return log_lines, collision_step


def parse_log(log_lines):
    obs_s, ego_s = [], []
    for line in log_lines:
        p = list(map(float, line.split()))
        obs_s.append((p[0], p[1], p[2], p[3], p[4], p[5]))
        ego_s.append((p[0], p[6], p[7], p[8], p[9], p[10]))
    return obs_s, ego_s


def make_dyn_obs(obs_id, states):
    t0, x0, y0, h0, v0, a0 = states[0]
    init = CustomState(position=np.array([x0, y0]), velocity=v0,
                       orientation=h0, time_step=0).convert_state_to_state(InitialState())
    state_list = []
    for row in states[1:]:
        t, x, y, h, v, a = row
        state_list.append(CustomState(
            position=np.array([x, y]), velocity=v, orientation=h,
            acceleration=a, time_step=int(round(t / DT))))
    if not state_list:
        return None
    traj = Trajectory(1, state_list)
    shape = RectObstacleShape(width=CAR_W, length=CAR_L)
    pred = TrajectoryPrediction(traj, shape)
    return DynamicObstacle(obs_id, ObstacleType.CAR, shape, init, pred)


def render_gif(obs_states, ego_states, collision_step, output_path, title):
    """CommonRoad 原生渲染 GIF"""
    scenario, pps = CommonRoadFileReader(ROAD_SCENARIO).open()
    for o in list(scenario.dynamic_obstacles):
        scenario.remove_obstacle(o)

    # 障碍物 = 红色卡车 (TRUCK 类型视觉上区别于 CAR)
    obs = make_dyn_obs(100, obs_states)
    if obs:
        obs.obstacle_type = ObstacleType.TRUCK  # 视觉区分
    # Ego = 普通轿车
    ego = make_dyn_obs(200, ego_states)

    if obs:
        scenario.add_objects(obs)
    if ego:
        scenario.add_objects(ego)

    figs_dir = os.path.join(ANIM_DIR, "temp_figs")
    os.makedirs(figs_dir, exist_ok=True)
    filenames = []

    n_frames = min(len(ego_states), 60)
    if collision_step >= 0:
        n_frames = min(n_frames, collision_step + 8)

    for t in range(n_frames):
        fig = plt.figure(figsize=(20, 6))
        rnd = MPRenderer()
        rnd.draw_params.time_begin = t
        rnd.draw_params.time_end = t + 1
        rnd.draw_params.dynamic_obstacle.draw_icon = True
        rnd.draw_params.dynamic_obstacle.draw_shape = True

        scenario.draw(rnd)
        pps.draw(rnd)
        rnd.render()

        # 标注
        ax = plt.gca()
        ax.set_title(title, fontsize=13, fontweight='bold', pad=10)

        # 标注 ego（在下车道）
        ex, ey = ego_states[t][1], ego_states[t][2]
        ax.annotate('EGO (ACC)', (ex, ey - 2.5), fontsize=9, ha='center',
                     color='blue', fontweight='bold',
                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

        # 标注障碍物
        ox, oy = obs_states[t][1], obs_states[t][2]
        ax.annotate('CUT-IN', (ox, oy + 2.5), fontsize=9, ha='center',
                     color='red', fontweight='bold',
                     bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))

        if collision_step >= 0 and t >= collision_step:
            cx, cy = (ex + ox) / 2, (ey + oy) / 2
            ax.annotate('COLLISION!', (cx, cy + 5), fontsize=18, ha='center',
                         color='red', fontweight='bold',
                         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9,
                                   edgecolor='red', linewidth=2), zorder=50)

        fp = os.path.join(figs_dir, f"f_{t:03d}.png")
        plt.savefig(fp, dpi=80, bbox_inches='tight')
        plt.close()
        filenames.append(fp)

    dur = 0.15 if collision_step >= 0 else 0.12
    with imageio.get_writer(output_path, mode='I', duration=dur, loop=0) as w:
        for fn in filenames:
            w.append_data(imageio.imread(fn))
    for fn in filenames:
        os.remove(fn)


def main():
    # 场景参数: (distance, ego_speed, obs_speed)
    # Ego在lane1 (Y=0), 障碍物从lane2 (Y=3.5) 切向 lane1
    selected = [
        # 碰撞场景：距离近+速度差大，障碍物切入后 ego 来不及反应
        (5, 25, 12, "cut-in COLLISION: 5m, ego=25, obs=12"),
        (8, 28, 15, "cut-in COLLISION: 8m, ego=28, obs=15"),
        (6, 22, 10, "cut-in COLLISION: 6m, ego=22, obs=10"),
        # 安全场景1：距离远，切入完成后 ego 有足够时间减速
        (15, 25, 18, "cut-in SAFE: 15m, ego=25, obs=18"),
        # 安全场景2：距离近但 obs 速度快，切入后拉开距离
        (8, 20, 22, "cut-in SAFE: 8m, ego=20, obs=22 (faster)"),
        # 安全场景3：远距离，完全安全
        (25, 25, 15, "cut-in SAFE: 25m, ego=25, obs=15"),
    ]

    print("Cut-in GIFs — CommonRoad native rendering")
    print(f"  Ego: lane1 (Y=0), Obstacle: lane2 (Y=3.5) → cuts into lane1")
    print("=" * 60)

    for dist, ego_spd, obs_spd, desc in selected:
        log_lines, col_step = simulate_cut_in(ego_spd, obs_spd, dist)
        obs_s, ego_s = parse_log(log_lines)

        prefix = "collision" if col_step >= 0 else "safe"
        fname = f"{prefix}_ego{ego_spd}_obs{obs_spd}_dist{dist}m.gif"
        out = os.path.join(ANIM_DIR, fname)

        tag = "COLLISION!" if col_step >= 0 else "safe"
        print(f"  dist={dist}m ego={ego_spd} obs={obs_spd} → {tag} → {fname}")
        render_gif(obs_s, ego_s, col_step, out, desc)

    print(f"\nDone. Output: {ANIM_DIR}")


if __name__ == '__main__':
    main()

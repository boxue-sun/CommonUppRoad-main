"""
generate_following_brake_gifs.py
跟车急刹场景：ego 跟着障碍物行驶，障碍物突然急刹，ego 撞上 / 刚好刹住
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

import os
import sys
import numpy as np
import imageio

sys.path.insert(0, os.path.dirname(__file__))

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.state import CustomState, InitialState
from commonroad.scenario.trajectory import Trajectory
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.geometry.obstacle_shapes.rect_obstacle_shape import RectObstacleShape

ROOT = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(ROOT, "experiments", "animation", "following_brake")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ROAD_SCENARIO = os.path.join(ROOT, "scenarios", "ZAM_Tutorial-1_2_T-1.xml")

# === ISO 15622 ACC 参数 ===
V_SET = 30.0
T_HW = 1.8
S0 = 2.0
A_MAX = 1.5
COMFORT_BRAKE = -2.0
EMERGENCY_BRAKE = -6.0
BRAKE_RATE = 3.0
REACTION_TIME = 0.3  # ACC 系统真实延迟
DANGER_TTC = 1.5
WARNING_TTC = 3.0
APPROACH_DIST = 80.0
P_GAIN = 0.4


def simulate_following_brake(ego_v0, obs_v0, dist, brake_time, obs_decel, dt=0.1, max_steps=120, ego_const_speed=True):
    """
    跟车急刹场景模拟
    ego_v0: ego 初始速度
    obs_v0: 障碍物初始速度（同向）
    dist: 初始间距
    brake_time: 障碍物开始刹车的时间（秒）
    obs_decel: 障碍物减速度（负值，如 -8.0）
    """
    ego_x, ego_v, ego_a = 0.0, ego_v0, 0.0
    obs_x, obs_v = float(dist), obs_v0
    danger_detected = False
    reaction_step = 0
    log_lines = []
    collision_step = -1

    for step in range(max_steps):
        t = step * dt
        gap = obs_x - ego_x

        # 记录状态
        line = f"{t:.1f} {obs_x:.2f} 0.0 0.0 {obs_v:.2f} 0.0 {ego_x:.2f} 0.0 0.0 {ego_v:.2f} {ego_a:.2f}"
        log_lines.append(line)

        # 碰撞检测 (两车半长之和: (4.5+4.3)/2 = 4.4m)
        if gap < 4.4 and collision_step < 0:
            collision_step = step

        # === 障碍物行为：brake_time 前匀速，之后急刹 ===
        if t >= brake_time:
            obs_v = max(0.0, obs_v + obs_decel * dt)

        # TTC
        rel_vel = ego_v - obs_v
        if rel_vel > 0.1:
            ttc = gap / rel_vel
        else:
            ttc = 999.0

        # 层1: 危险检测（距离触发，更敏感）
        danger_threshold = max(50.0, ego_v * 2.0)  # 至少 50m 或 2 秒距离
        if gap < danger_threshold or ttc < WARNING_TTC:
            if not danger_detected:
                danger_detected = True
                reaction_step = 0
            reaction_step += 1
        else:
            danger_detected = False
            reaction_step = 0

        if danger_detected and reaction_step * dt < REACTION_TIME:
            pass  # 反应延迟不干预
        else:
            # 层2: 四模式决策
            desired_gap = S0 + ego_v * T_HW
            target_acc = 0.0

            if ego_const_speed and not danger_detected:
                target_acc = 0.0  # 跟车场景：无危险时保持匀速
            elif gap > APPROACH_DIST:
                target_acc = A_MAX if ego_v < V_SET else 0.0
            elif gap > desired_gap + 5.0:
                denom = max(1.0, APPROACH_DIST - desired_gap - 5.0)
                gap_ratio = max(0.0, min(1.0, (APPROACH_DIST - gap) / denom))
                target_acc = -gap_ratio * 2.0
                if ego_v < obs_v:
                    target_acc = 0.0
            elif gap > S0:
                gap_error = gap - desired_gap
                target_acc = P_GAIN * gap_error - 0.5 * rel_vel
                target_acc = max(COMFORT_BRAKE, min(A_MAX, target_acc))
            else:
                target_acc = EMERGENCY_BRAKE

            # 层3: 紧急制动覆盖
            if ttc < DANGER_TTC:
                target_acc = EMERGENCY_BRAKE
            elif ttc < WARNING_TTC:
                if target_acc > COMFORT_BRAKE:
                    target_acc = COMFORT_BRAKE

            # 渐进刹车
            acc_step = BRAKE_RATE * dt
            if target_acc < ego_a - acc_step:
                ego_a = ego_a - acc_step
            elif target_acc > ego_a + acc_step:
                ego_a = ego_a + acc_step
            else:
                ego_a = target_acc

        ego_v = max(0.0, ego_v + ego_a * dt)
        ego_x = ego_x + ego_v * dt
        obs_x = obs_x + obs_v * dt

    return log_lines, collision_step


def make_dynamic_obstacle(obstacle_id, states, w=1.8, l=4.3):
    """从状态序列创建 CommonRoad DynamicObstacle"""
    t0, x0, y0, h0, v0, a0 = states[0]
    initial_state = CustomState(
        position=np.array([x0, y0]),
        velocity=v0,
        orientation=h0,
        time_step=0
    ).convert_state_to_state(InitialState())

    state_list = []
    for row in states[1:]:
        t, x, y, h, v, a = row
        state = CustomState(
            position=np.array([x, y]),
            velocity=v,
            orientation=h,
            acceleration=a,
            time_step=int(round(t / 0.1))
        )
        state_list.append(state)

    if len(state_list) == 0:
        return None

    trajectory = Trajectory(1, state_list)
    shape = RectObstacleShape(width=w, length=l)
    prediction = TrajectoryPrediction(trajectory, shape)
    return DynamicObstacle(obstacle_id, ObstacleType.CAR, shape, initial_state, prediction)


def parse_log_lines(log_lines):
    """解析 log 行为 obs 和 ego 状态"""
    obs_states, ego_states = [], []
    for line in log_lines:
        parts = list(map(float, line.split()))
        t, ox, oy, oh, ov, oa, ex, ey, eh, ev, ea = parts
        obs_states.append((t, ox, oy, oh, ov, oa))
        ego_states.append((t, ex, ey, eh, ev, ea))
    return obs_states, ego_states


def render_commonroad_gif(scenario_path, obs_states, ego_states, collision_step, output_path, brake_time=None):
    """用 CommonRoad 原生渲染器生成 GIF"""
    scenario, pps = CommonRoadFileReader(scenario_path).open()

    for orig_obs in list(scenario.dynamic_obstacles):
        scenario.remove_obstacle(orig_obs)

    obs = make_dynamic_obstacle(100, obs_states, w=1.8, l=4.3)
    ego = make_dynamic_obstacle(200, ego_states, w=1.0, l=4.5)

    if obs:
        scenario.add_objects(obs)
    if ego:
        scenario.add_objects(ego)

    figs_dir = os.path.join(OUTPUT_DIR, "temp_figs")
    os.makedirs(figs_dir, exist_ok=True)
    filenames = []

    n_frames = min(len(ego_states), 150)
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

        # 碰撞标注
        if collision_step >= 0 and t >= collision_step:
            ax = plt.gca()
            ex, ey = ego_states[t][1], ego_states[t][2]
            ax.annotate('COLLISION!', (ex, ey + 8), fontsize=20, ha='center',
                        color='red', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='red'),
                        zorder=20)

        # 急刹标注（障碍物开始刹车时显示）
        if brake_time is not BRAKE_NONE and t == int(brake_time / 0.1):
            ax = plt.gca()
            ox, oy = obs_states[t][1], obs_states[t][2]
            ax.annotate('BRAKE!', (ox, oy + 8), fontsize=16, ha='center',
                        color='red', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='orange', alpha=0.9, edgecolor='red'),
                        zorder=20)

        filepath = os.path.join(figs_dir, f"frame_{t:03d}.png")
        plt.savefig(filepath, dpi=80, bbox_inches='tight')
        plt.close()
        filenames.append(filepath)

    duration = 0.15
    with imageio.get_writer(output_path, mode='I', duration=duration) as writer:
        for fn in filenames:
            writer.append_data(imageio.imread(fn))

    for fn in filenames:
        os.remove(fn)

    tag = f"COLLISION at step {collision_step}" if collision_step >= 0 else "SAFE"
    print(f"  {tag} -> {os.path.basename(output_path)}")


BRAKE_NONE = 999  # sentinel

def main():
    print("=" * 70)
    print("跟车急刹场景 GIF 生成")
    print("=" * 70)

    scenarios = [
        # (ego_v, obs_v, dist, brake_time, obs_decel, name, description)
        # 场景1: 碰撞 - ego 25 跟着 obs 25, 距离 35m, obs 在 3s 急刹 -8m/s²
        (25, 25, 35, 3.0, -8.0, "collision_follow_brake", "ego25 obs25 dist35 brake@3s decel8"),
        # 场景2: 安全 - ego 25 跟着 obs 25, 距离 400m, obs 在 3s 急刹 -8m/s²（ego 能刹住）
        (25, 25, 400, 10.0, -8.0, "safe_follow_brake", "ego25 obs25 dist400 brake@10s decel8"),
        # 场景3: 碰撞 - ego 30 跟着 obs 30, 距离 40m, obs 在 2.5s 急刹 -8m/s²
        (30, 30, 40, 2.5, -8.0, "collision_highspeed", "ego30 obs30 dist40 brake@2.5s decel8"),
        # 场景4: 安全 - ego 30 跟着 obs 30, 距离 500m, obs 在 10s 急刹 -8m/s²
        (30, 30, 500, 10.0, -8.0, "safe_highspeed", "ego30 obs30 dist500 brake@10s decel8"),
    ]

    for ego_v, obs_v, dist, brake_t, decel, name, desc in scenarios:
        print(f"\n[{name}] {desc}")
        log, coll = simulate_following_brake(ego_v, obs_v, dist, brake_t, decel, max_steps=200)
        obs_s, ego_s = parse_log_lines(log)
        out = os.path.join(OUTPUT_DIR, f"{name}.gif")
        render_commonroad_gif(ROAD_SCENARIO, obs_s, ego_s, coll, out, brake_time=brake_t)

    print("\n" + "=" * 70)
    print(f"Done! GIFs saved to: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()

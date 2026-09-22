"""
generate_iso15622_cr_gifs.py
ISO 15622 模型 + CommonRoad 原生渲染器 GIF 生成器
流程：ISO 15622 Python 模拟 → CommonRoad DynamicObstacle → MPRenderer 渲染 GIF
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

import os
import sys
import json
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
ANIM_DIR = os.path.join(ROOT, "experiments", "animation", "iso15622")
os.makedirs(ANIM_DIR, exist_ok=True)

ROAD_SCENARIO = os.path.join(ROOT, "scenarios", "ZAM_Tutorial-1_2_T-1.xml")

# === ISO 15622 参数 ===
V_SET = 30.0
T_HW = 1.8
S0 = 2.0
A_MAX = 1.5
COMFORT_BRAKE = -2.0
EMERGENCY_BRAKE = -6.0
BRAKE_RATE = 3.0
REACTION_TIME = 1.5
DANGER_TTC = 1.5
WARNING_TTC = 3.0
APPROACH_DIST = 80.0
P_GAIN = 0.4


def simulate_sudden_brake(ego_x0, ego_v0, obs_x0, obs_v0, brake_step=20, obs_decel=-6.0, dt=0.1, max_steps=80):
    """前车急刹场景：障碍物先匀速，到 brake_step 时突然急刹"""
    ego_x, ego_v, ego_a = ego_x0, ego_v0, 0.0
    obs_x, obs_v = obs_x0, obs_v0
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

        # 碰撞检测
        if gap < 4.0 and collision_step < 0:
            collision_step = step

        # === 障碍物行为：brake_step 之前匀速，之后急刹 ===
        if step >= brake_step:
            obs_v = max(0.0, obs_v + obs_decel * dt)

        # TTC
        rel_vel = ego_v - obs_v
        if rel_vel > 0.1:
            ttc = gap / rel_vel
        else:
            ttc = 999.0

        # 层1: 反应延迟
        if ttc < WARNING_TTC:
            if not danger_detected:
                danger_detected = True
                reaction_step = 0
            reaction_step += 1
        else:
            danger_detected = False
            reaction_step = 0

        if danger_detected and reaction_step * dt < REACTION_TIME:
            pass
        else:
            # 层2: 四模式决策
            desired_gap = S0 + ego_v * T_HW
            target_acc = 0.0

            if gap > APPROACH_DIST:
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

            if ttc < DANGER_TTC:
                target_acc = EMERGENCY_BRAKE
            elif ttc < WARNING_TTC:
                if target_acc > COMFORT_BRAKE:
                    target_acc = COMFORT_BRAKE

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


def simulate_iso15622(ego_x0, ego_v0, obs_x0, obs_v0, dt=0.1, max_steps=60):
    """ISO 15622 模拟（障碍物匀速），返回 log 行和碰撞步"""
    ego_x, ego_v, ego_a = ego_x0, ego_v0, 0.0
    obs_x, obs_v = obs_x0, obs_v0
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

        # 碰撞检测
        if gap < 4.0 and collision_step < 0:
            collision_step = step

        # TTC
        rel_vel = ego_v - obs_v
        if rel_vel > 0.1:
            ttc = gap / rel_vel
        else:
            ttc = 999.0

        # 层1: 反应延迟
        if ttc < WARNING_TTC:
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

            if gap > APPROACH_DIST:
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


def render_commonroad_gif(scenario_path, obs_states, ego_states, collision_step, output_path):
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

    figs_dir = os.path.join(ANIM_DIR, "temp_figs")
    os.makedirs(figs_dir, exist_ok=True)
    filenames = []

    n_frames = min(len(ego_states), 50)
    if collision_step >= 0:
        n_frames = min(n_frames, collision_step + 6)

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

        if collision_step >= 0 and t >= collision_step:
            ax = plt.gca()
            ex, ey = ego_states[t][1], ego_states[t][2]
            ax.annotate('COLLISION!', (ex, ey + 8), fontsize=18, ha='center',
                        color='red', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='red'),
                        zorder=20)

        filepath = os.path.join(figs_dir, f"frame_{t:03d}.png")
        plt.savefig(filepath, dpi=80, bbox_inches='tight')
        plt.close()
        filenames.append(filepath)

    duration = 0.2 if collision_step >= 0 else 0.15
    with imageio.get_writer(output_path, mode='I', duration=duration) as writer:
        for fn in filenames:
            writer.append_data(imageio.imread(fn))

    for fn in filenames:
        os.remove(fn)


def main():
    distances = [3, 5, 8, 10, 15, 20, 30, 50]
    obs_speeds = [0, 1, 3, 5, 10]
    ego_speeds = [10, 15, 20, 25, 30]

    for d in distances:
        os.makedirs(os.path.join(ANIM_DIR, f'dist_{d}m'), exist_ok=True)

    total = len(distances) * len(obs_speeds) * len(ego_speeds)
    print(f"ISO 15622 + CommonRoad GIF Generator")
    print(f"Total: {total} variants")
    print(f"Output: {ANIM_DIR}")
    print("=" * 70)

    collision_count = 0
    safe_count = 0
    vid = 0

    for dist in distances:
        for obs_spd in obs_speeds:
            for ego_spd in ego_speeds:
                ego_x0 = 0.0
                obs_x0 = float(dist)

                log_lines, collision_step = simulate_iso15622(ego_x0, ego_spd, obs_x0, obs_spd)
                obs_states, ego_states = parse_log_lines(log_lines)

                prefix = "collision" if collision_step >= 0 else "safe"
                fname = f"{prefix}_ego{ego_spd}_obs{obs_spd}_dist{dist}.gif"

                # 保存到根目录和距离子文件夹
                output_path = os.path.join(ANIM_DIR, fname)
                subfolder_path = os.path.join(ANIM_DIR, f"dist_{dist}m", fname)

                print(f"[{vid:3d}/{total}] dist={dist:2d}m obs={obs_spd:2d} ego={ego_spd:2d} -> ", end="", flush=True)
                render_commonroad_gif(ROAD_SCENARIO, obs_states, ego_states, collision_step, output_path)

                import shutil
                shutil.copy2(output_path, subfolder_path)

                if collision_step >= 0:
                    collision_count += 1
                else:
                    safe_count += 1
                vid += 1

    print("=" * 70)
    print(f"Done! {collision_count} COLLISION, {safe_count} SAFE")
    print(f"Output: {ANIM_DIR}")


if __name__ == '__main__':
    main()

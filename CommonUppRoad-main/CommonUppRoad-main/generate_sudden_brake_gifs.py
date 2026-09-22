"""
generate_sudden_brake_gifs.py
生成前车急刹场景的 CommonRoad 风格 GIF
ego 使用法规驾驶员模型（反应延迟 + 渐进刹车）
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
from commonroad.geometry.obstacle_shapes.rect_obstacle_shape import RectObstacleShape as Rectangle

ROOT = os.path.dirname(__file__)
ANIM_DIR = os.path.join(ROOT, "experiments", "animation")
os.makedirs(ANIM_DIR, exist_ok=True)
ROAD_SCENARIO = os.path.join(ROOT, "scenarios", "ZAM_Tutorial-1_2_T-1.xml")


def regulatory_driver_step(v_ego, v_lead, gap, current_acc, dt=0.1,
                           reaction_time=1.5, brake_rate=3.0,
                           max_brake=-8.0, comfort_brake=-4.0,
                           ttc_emergency=1.5, ttc_warning=3.0,
                           danger_detected=False, reaction_count=0):
    """
    法规驾驶员模型：一步仿真
    返回：new_acc, new_danger_detected, new_reaction_count
    """
    # 计算 TTC
    if v_ego > v_lead + 0.1:
        ttc = gap / (v_ego - v_lead)
    else:
        ttc = 999.0

    # 反应延迟检测
    if ttc < ttc_warning:
        if not danger_detected:
            danger_detected = True
            reaction_count = 0
        reaction_count += 1
    else:
        danger_detected = False
        reaction_count = 0

    # 决策
    if not danger_detected:
        target_acc = 0.5
    elif reaction_count * dt < reaction_time:
        target_acc = 0.0  # 反应时间内不刹车
    elif ttc < ttc_emergency:
        target_acc = max_brake
    else:
        target_acc = comfort_brake

    # 渐进刹车
    acc_step = brake_rate * dt
    if target_acc < current_acc - acc_step:
        new_acc = current_acc - acc_step
    elif target_acc > current_acc + acc_step:
        new_acc = current_acc + acc_step
    else:
        new_acc = target_acc

    return new_acc, danger_detected, reaction_count


def simulate(ego_x0, ego_v0, obs_x0, obs_v0, obs_brake, dt=0.1, max_steps=80):
    """模拟前车急刹场景"""
    ego_x, ego_v, ego_acc = ego_x0, ego_v0, 0.0
    obs_x, obs_v = obs_x0, obs_v0
    danger_detected = False
    reaction_count = 0

    ego轨迹 = [(ego_x, ego_v, ego_acc)]
    obs轨迹 = [(obs_x, obs_v)]
    collision_step = -1

    for step in range(max_steps):
        # 障碍物急刹
        obs_v = max(0.0, obs_v + obs_brake * dt)
        obs_x = obs_x + obs_v * dt

        # 法规模型控制 ego
        gap = max(0.01, obs_x - ego_x)
        ego_acc, danger_detected, reaction_count = regulatory_driver_step(
            ego_v, obs_v, gap, ego_acc, dt,
            danger_detected=danger_detected, reaction_count=reaction_count
        )
        ego_v = max(0.0, ego_v + ego_acc * dt)
        ego_x = ego_x + ego_v * dt

        ego轨迹.append((ego_x, ego_v, ego_acc))
        obs轨迹.append((obs_x, obs_v))

        if abs(ego_x - obs_x) < 4.0 and collision_step < 0:
            collision_step = step + 1

    return ego轨迹, obs轨迹, collision_step


def make_dynamic_obstacle(obstacle_id, states, w=1.8, l=4.3, dt=0.1):
    t0, x0, y0, h0, v0, a0 = states[0]
    initial_state = CustomState(
        position=np.array([x0, y0]), velocity=v0, orientation=h0, time_step=0
    ).convert_state_to_state(InitialState())

    state_list = []
    for row in states[1:]:
        t, x, y, h, v, a = row
        state = CustomState(
            position=np.array([x, y]), velocity=v, orientation=h,
            acceleration=a, time_step=int(round(t / dt))
        )
        state_list.append(state)

    if not state_list:
        return None
    trajectory = Trajectory(1, state_list)
    shape = Rectangle(width=w, length=l)
    prediction = TrajectoryPrediction(trajectory, shape)
    return DynamicObstacle(obstacle_id, ObstacleType.CAR, shape, initial_state, prediction)


def render_gif(scenario_path, ego轨迹, obs轨迹, collision_step, title, output_path, dt=0.1):
    scenario, pps = CommonRoadFileReader(scenario_path).open()
    for orig in list(scenario.dynamic_obstacles):
        scenario.remove_obstacle(orig)

    # 转换为状态格式：(t, x, y, heading, v, a)
    obs_states = [(i * dt, ox, 0.0, 0.0, ov, 0.0) for i, (ox, ov) in enumerate(obs轨迹)]
    ego_states = [(i * dt, ex, 0.0, 0.0, ev, ea) for i, (ex, ev, ea) in enumerate(ego轨迹)]

    obs = make_dynamic_obstacle(100, obs_states, dt=dt)
    ego = make_dynamic_obstacle(200, ego_states, dt=dt)
    if obs: scenario.add_objects(obs)
    if ego: scenario.add_objects(ego)

    figs_dir = os.path.join(ANIM_DIR, "temp_figs")
    os.makedirs(figs_dir, exist_ok=True)
    filenames = []

    n_frames = min(len(ego_states), 50)
    if collision_step >= 0:
        n_frames = min(n_frames, collision_step + 5)

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
            ex = ego_states[t][1]
            ax.annotate('COLLISION!', (ex, 8), fontsize=18, ha='center',
                        color='red', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='red'),
                        zorder=20)

        filepath = os.path.join(figs_dir, f"frame_{t:03d}.png")
        plt.savefig(filepath, dpi=80, bbox_inches='tight')
        plt.close()
        filenames.append(filepath)

    dur = 0.25 if collision_step >= 0 else 0.15
    with imageio.get_writer(output_path, mode='I', duration=dur) as writer:
        for fn in filenames:
            writer.append_data(imageio.imread(fn))
    for fn in filenames:
        os.remove(fn)

    tag = f"COLLISION at step {collision_step}" if collision_step >= 0 else "SAFE"
    print(f"  {tag} -> {os.path.basename(output_path)}")


def main():
    dt = 0.1
    scenarios = [
        # (描述, ego速度, obs速度, 距离, obs刹车减速度)
        ("ego25_obs20_dist15_brake4", 25, 20, 15, -4.0),
        ("ego25_obs20_dist25_brake4", 25, 20, 25, -4.0),
        ("ego30_obs25_dist20_brake4", 30, 25, 20, -4.0),
        ("ego30_obs25_dist30_brake3", 30, 25, 30, -3.0),
        ("ego15_obs10_dist20_brake4", 15, 10, 20, -4.0),
        ("ego20_obs15_dist25_brake4", 20, 15, 25, -4.0),
        ("ego25_obs20_dist40_brake4", 25, 20, 40, -4.0),
    ]

    print("Generating sudden brake GIFs...")
    print("=" * 60)

    for name, ego_v, obs_v, dist, brake in scenarios:
        ego轨迹, obs轨迹, collision_step = simulate(0, ego_v, dist, obs_v, brake, dt)
        prefix = "collision" if collision_step >= 0 else "safe"
        output_path = os.path.join(ANIM_DIR, f"brake_{prefix}_{name}.gif")
        print(f"[{name}] ego={ego_v}m/s obs={obs_v}m/s dist={dist}m brake={brake}m/s2")
        render_gif(ROAD_SCENARIO, ego轨迹, obs轨迹, collision_step, name, output_path, dt)

    print("=" * 60)
    print(f"Done! GIFs saved to: {ANIM_DIR}")


if __name__ == '__main__':
    main()

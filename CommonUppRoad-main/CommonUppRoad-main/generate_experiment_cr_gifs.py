"""
generate_experiment_cr_gifs.py
用 CommonRoad 原生渲染器生成碰撞/安全场景的 GIF
流程：Python 模拟 → sampling.log → CommonRoad DynamicObstacle → 渲染 GIF
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
ANIM_DIR = os.path.join(ROOT, "experiments", "animation")
os.makedirs(ANIM_DIR, exist_ok=True)

# 用 ZAM_Tutorial 作为道路背景（直路）
ROAD_SCENARIO = os.path.join(ROOT, "scenarios", "ZAM_Tutorial-1_2_T-1.xml")


def idm_acceleration(v_ego, v_lead, gap):
    """IDM 加速度，限幅 [-10, 2]"""
    v0, T, s0, a_max, b_comf, delta = 30.0, 1.5, 2.0, 2.0, 1.5, 4
    s_star = s0 + v_ego * T + v_ego * (v_ego - v_lead) / (2.0 * np.sqrt(a_max * b_comf))
    if gap < 0.001:
        gap = 0.001
    acc = a_max * (1.0 - (v_ego / v0) ** delta - (s_star / gap) ** 2)
    return max(-10.0, min(2.0, acc))


def simulate(ego_x0, ego_v0, obs_x0, obs_v0, dt=0.1, max_steps=60):
    """模拟并生成 sampling.log 格式的数据"""
    ego_x, ego_v, ego_h = ego_x0, ego_v0, 0.0
    obs_x, obs_v, obs_h = obs_x0, obs_v0, 0.0

    log_lines = []  # 每行: time obs_x obs_y obs_h obs_v obs_a ego_x ego_y ego_h ego_v ego_a
    collision_step = -1

    for step in range(max_steps):
        t = step * dt

        # 记录状态 (sampling.log 格式)
        line = f"{t:.1f} {obs_x:.2f} {obs_h:.2f} {obs_h:.2f} {obs_v:.2f} 0.0 {ego_x:.2f} {0.0:.2f} {ego_h:.2f} {ego_v:.2f} 0.0"
        log_lines.append(line)

        # 碰撞检测
        if abs(ego_x - obs_x) < 4.0 and collision_step < 0:
            collision_step = step

        # IDM 控制 ego
        gap = max(0.01, obs_x - ego_x)
        acc = idm_acceleration(ego_v, obs_v, gap)
        ego_v = max(0.0, ego_v + acc * dt)
        ego_x = ego_x + ego_v * dt

        # 障碍物匀速
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
    obs_states = []
    ego_states = []
    for line in log_lines:
        parts = list(map(float, line.split()))
        t, ox, oy, oh, ov, oa, ex, ey, eh, ev, ea = parts
        obs_states.append((t, ox, oy, oh, ov, oa))
        ego_states.append((t, ex, ey, eh, ev, ea))
    return obs_states, ego_states


def render_commonroad_gif(scenario_path, obs_states, ego_states, collision_step, title, output_path):
    """用 CommonRoad 原生渲染器生成 GIF"""
    scenario, pps = CommonRoadFileReader(scenario_path).open()

    # 先删除原场景的所有动态障碍物
    for orig_obs in list(scenario.dynamic_obstacles):
        scenario.remove_obstacle(orig_obs)

    # 只添加我们的障碍物和 ego
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

        # 碰撞标注
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

    tag = f"COLLISION at step {collision_step}" if collision_step >= 0 else "SAFE"
    print(f"  {tag} -> {os.path.basename(output_path)}")


def main():
    scenarios = [
        # (描述, ego位置, ego速度, obs位置, obs速度)
        ("collision_5m_30mps",  0, 30,  5, 0),
        ("collision_10m_30mps", 0, 30, 10, 1),
        ("collision_15m_25mps", 0, 25, 15, 0),
        ("collision_20m_30mps", 0, 30, 20, 3),
        ("safe_20m_10mps",      0, 10, 20, 5),
        ("safe_30m_15mps",      0, 15, 30, 10),
        ("safe_50m_20mps",      0, 20, 50, 10),
    ]

    print("Generating CommonRoad-style GIFs...")
    print("=" * 60)

    for name, ego_x0, ego_v0, obs_x0, obs_v0 in scenarios:
        log_lines, collision_step = simulate(ego_x0, ego_v0, obs_x0, obs_v0)
        obs_states, ego_states = parse_log_lines(log_lines)

        prefix = "collision" if collision_step >= 0 else "safe"
        output_path = os.path.join(ANIM_DIR, f"cr_{prefix}_{name}.gif")

        print(f"[{name}] ego={ego_v0}m/s obs={obs_v0}m/s dist={obs_x0 - ego_x0}m")
        render_commonroad_gif(ROAD_SCENARIO, obs_states, ego_states, collision_step, name, output_path)

    print("=" * 60)
    print(f"Done! GIFs saved to: {ANIM_DIR}")


if __name__ == '__main__':
    main()
